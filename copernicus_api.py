"""
Niger Delta Sentinel - Phase 3: Copernicus Data Space Ecosystem (CDSE) Integration
Uses OData API with smart cloud filtering for reliable, clear Sentinel-2 imagery.
"""

import os
import requests
import certifi
import zipfile
import logging
import numpy as np
import rasterio
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Force SSL certificate verification for cloud environments
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

# Load environment variables securely
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# CDSE Endpoints
TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
ODATA_URL = "https://catalogue.dataspace.copernicus.eu/odata/v1"

# Niger Delta Bounding Box (minx, miny, maxx, maxy)
NIGER_DELTA_BBOX = "POLYGON((5.0 4.0, 7.5 4.0, 7.5 6.0, 5.0 6.0, 5.0 4.0))"


def get_access_token() -> str:
    """Authenticates with CDSE using OAuth2 Password flow."""
    client_id = os.getenv("CDSE_CLIENT_ID")
    username = os.getenv("CDSE_USERNAME")
    password = os.getenv("CDSE_PASSWORD")
    
    if not client_id or not username or not password:
        raise ValueError("CDSE credentials not found in .env file.")
        
    logger.info("Requesting OAuth2 access token from CDSE...")
    
    payload = {
        "grant_type": "password",
        "client_id": client_id,
        "username": username,
        "password": password
    }
    
    response = requests.post(TOKEN_URL, data=payload, timeout=30, verify=certifi.where())
    response.raise_for_status()
    
    token = response.json().get("access_token")
    if not token:
        raise ValueError("Access token not found in CDSE response.")
        
    logger.info("Successfully acquired CDSE access token.")
    return token


def search_latest_scene(token: str) -> dict:
    """
    Queries OData API for the latest Sentinel-2 L2A scene over Niger Delta.
    SMART FILTER: Fetches top 5 recent scenes and picks the first with < 30% cloud cover.
    """
    logger.info("Querying OData API for latest clear Sentinel-2 scene...")
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    date_filter = f"ContentDate/Start gt {start_date.strftime('%Y-%m-%dT00:00:00.000Z')}"
    
    # Fetch top 5 to give us options for cloud filtering
    params = {
        "$filter": (
            f"Collection/Name eq 'SENTINEL-2' "
            f"and contains(Name, 'MSIL2A') "
            f"and OData.CSC.Intersects(area=geography'SRID=4326;{NIGER_DELTA_BBOX}') "
            f"and {date_filter}"
        ),
        "$orderby": "ContentDate/Start desc",
        "$top": 5,
        "$expand": "Attributes"
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{ODATA_URL}/Products", params=params, headers=headers, timeout=60, verify=certifi.where())
    response.raise_for_status()
    
    products = response.json().get("value", [])
    
    if not products:
        logger.warning("No scenes found with geographic filter. Trying without location filter...")
        params_simple = {
            "$filter": (
                f"Collection/Name eq 'SENTINEL-2' "
                f"and contains(Name, 'MSIL2A') "
                f"and {date_filter}"
            ),
            "$orderby": "ContentDate/Start desc",
            "$top": 5,
            "$expand": "Attributes"
        }
        response = requests.get(f"{ODATA_URL}/Products", params=params_simple, headers=headers, timeout=60, verify=certifi.where())
        response.raise_for_status()
        products = response.json().get("value", [])
        
        if not products:
            raise ValueError("No Sentinel-2 L2A scenes found in last 90 days.")
    
    # 🌤️ SMART CLOUD FILTERING: Find the first scene with < 30% cloud cover
    best_scene = None
    for product in products:
        cloud_cover = None
        for attr in product.get("Attributes", []):
            if attr["Name"] == "cloudCover":
                try:
                    cloud_cover = float(attr["Value"])
                except (ValueError, TypeError):
                    continue
                break
        
        if cloud_cover is not None and cloud_cover < 30.0:
            best_scene = product
            logger.info(f"Found clear scene: {product['Name']} with {cloud_cover:.1f}% cloud cover.")
            break
    
    # Fallback: If all recent scenes are cloudy, use the absolute latest one
    if best_scene is None:
        best_scene = products[0]
        fallback_cloud = None
        for attr in best_scene.get("Attributes", []):
            if attr["Name"] == "cloudCover":
                try:
                    fallback_cloud = float(attr["Value"])
                except (ValueError, TypeError):
                    pass
                break
        logger.warning(f"No clear scenes (<30%) found recently. Using latest scene with {fallback_cloud}% cloud cover.")
    
    scene = best_scene
    scene_id = scene["Id"]
    scene_name = scene["Name"]
    scene_date = scene["ContentDate"]["Start"]
    
    final_cloud_cover = None
    for attr in scene.get("Attributes", []):
        if attr["Name"] == "cloudCover":
            try:
                final_cloud_cover = float(attr["Value"])
            except (ValueError, TypeError):
                pass
            break
    
    logger.info(f"Selected scene: {scene_name} | UUID: {scene_id} | Date: {scene_date} | Cloud Cover: {final_cloud_cover}%")
    
    return {
        "id": scene_id,
        "name": scene_name,
        "date": scene_date,
        "cloud_cover": final_cloud_cover
    }


def download_and_prepare_scene(scene: dict, token: str, output_path: str = "data/live_sentinel2.tif") -> str:
    """Downloads the Sentinel-2 ZIP, extracts B04 and B08, creates multi-band GeoTIFF."""
    product_uuid = scene["id"]
    scene_name = scene["name"]
    
    download_url = f"https://zipper.dataspace.copernicus.eu/odata/v1/Products({product_uuid})/$value"
    logger.info(f"Initiating download for {scene_name}...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 🛡️ RESILIENCE FIX: Create a session with automatic retries for dropped connections
    session = requests.Session()
    retry_strategy = Retry(
        total=3, 
        backoff_factor=2, 
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    
    try:
        with session.get(download_url, headers=headers, stream=True, timeout=300, verify=certifi.where()) as r:
            r.raise_for_status()
            zip_path = "data/temp_sentinel2.zip"
            os.makedirs("data", exist_ok=True)
            
            with open(zip_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk: # filter out keep-alive new chunks
                        f.write(chunk)
    except requests.exceptions.RequestException as e:
        logger.error(f"Download failed or interrupted: {e}")
        raise
        
    logger.info("Download complete. Extracting required bands...")
    
    extract_dir = "data/temp_extract"
    os.makedirs(extract_dir, exist_ok=True)
    
    b04_path = None
    b08_path = None
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for member in zip_ref.namelist():
                if member.endswith('_B04_10m.jp2'):
                    zip_ref.extract(member, extract_dir)
                    b04_path = os.path.join(extract_dir, member)
                elif member.endswith('_B08_10m.jp2'):
                    zip_ref.extract(member, extract_dir)
                    b08_path = os.path.join(extract_dir, member)
                    
        if not b04_path or not b08_path:
            raise FileNotFoundError("Could not locate B04 or B08 10m bands in the downloaded archive.")
            
        logger.info("Bands extracted. Converting JPEG2000 to multi-band GeoTIFF...")
        
        # 🛡️ MEMORY FIX: Downsample to web-friendly resolution (2048x2048)
        TARGET_SIZE = (2048, 2048)
        
        with rasterio.open(b04_path) as src_red:
            red_data = src_red.read(1, out_shape=TARGET_SIZE, resampling=rasterio.enums.Resampling.average)
            profile = src_red.profile.copy()
            original_bounds = src_red.bounds
            
        with rasterio.open(b08_path) as src_nir:
            nir_data = src_nir.read(1, out_shape=TARGET_SIZE, resampling=rasterio.enums.Resampling.average)
            
        height, width = TARGET_SIZE
        bands_data = np.zeros((8, height, width), dtype=np.uint16)
        bands_data[3] = red_data
        bands_data[7] = nir_data
        
        profile.update(
            count=8,
            dtype='uint16',
            compress='lzw',
            nodata=0,
            width=width,
            height=height,
            transform=rasterio.transform.from_bounds(
                original_bounds.left, original_bounds.bottom, 
                original_bounds.right, original_bounds.top,
                width, height
            )
        )
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with rasterio.open(output_path, 'w', **profile) as dst:
            dst.write(bands_data)
            
        logger.info(f"Successfully prepared live GeoTIFF at: {output_path}")
        return output_path
        
    finally:
        if os.path.exists(zip_path):
            os.remove(zip_path)
        if os.path.exists(extract_dir):
            import shutil
            shutil.rmtree(extract_dir)


def fetch_and_prepare_live_data() -> tuple:
    """Master orchestration function."""
    try:
        token = get_access_token()
        scene = search_latest_scene(token)
        file_path = download_and_prepare_scene(scene, token)
        return file_path, scene["date"]
        
    except Exception as e:
        logger.error(f"Live data pipeline failed: {e}")
        raise


if __name__ == "__main__":
    try:
        file_path, scene_date = fetch_and_prepare_live_data()
        print(f"\n✅ SUCCESS! Live data ready at: {file_path}")
        print(f"📅 Scene date: {scene_date}")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")