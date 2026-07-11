"""
Niger Delta Sentinel - Phase 1: Synthetic Data Generator
--------------------------------------------------------
Generates a mock Sentinel-2 L2A multi-band GeoTIFF for testing the NDVI pipeline.
Simulates healthy vegetation, sparse vegetation, bare soil, deep water, and sensor anomalies.

Author: [Your Name]
Project: Niger Delta Sentinel (OSINT/GEOINT Engine)
"""

import os
import sys
import logging
import numpy as np
import rasterio
from rasterio.transform import from_bounds
from rasterio.crs import CRS

# Configure professional logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Niger Delta approximate bounding box (WGS84)
# Lon: 5.5 to 6.5 | Lat: 4.0 to 5.0
DELTA_BOUNDS = (5.5, 4.0, 6.5, 5.0) 


def generate_band_data(height: int, width: int) -> np.ndarray:
    """
    Generates an 8-band numpy array simulating Sentinel-2 MSI surface reflectance.
    Values are scaled to uint16 (0-10000) to match ESA's L2A specification.
    
    Returns:
        np.ndarray: Array of shape (8, height, width) with dtype uint16.
    """
    logger.info("Generating synthetic spectral signatures...")
    
    # Initialize all 8 bands with a baseline reflectance (e.g., 1000)
    bands = np.ones((8, height, width), dtype=np.float32) * 1000.0
    
    # Create coordinate grids for spatial patterning
    y, x = np.mgrid[0:height, 0:width]
    
    # 1. Healthy Vegetation (Top-Left Quadrant)
    # High NIR, Low Red -> NDVI ~ 0.75
    bands[3, 0:height//2, 0:width//2] = 400.0   # Band 4: Red
    bands[7, 0:height//2, 0:width//2] = 3200.0  # Band 8: NIR
    
    # 2. Bare Soil / Degraded Land (Bottom-Right Quadrant)
    # Moderate NIR, High Red -> NDVI ~ 0.1
    bands[3, height//2:height, width//2:width] = 2200.0 # Band 4: Red
    bands[7, height//2:height, width//2:width] = 2400.0 # Band 8: NIR
    
    # 3. Sparse Vegetation / Transition Zone (Diagonal)
    # Moderate NIR, Moderate Red -> NDVI ~ 0.35
    mask_sparse = (x + y > height * 0.8) & (x + y < height * 1.2)
    bands[3, mask_sparse] = 1000.0
    bands[7, mask_sparse] = 2000.0
    
    # 4. Deep Water / Cloud Shadows (Center Circle)
    # Very Low NIR, Low Red -> NDVI < 0
    cy, cx = height // 2, width // 2
    dist_from_center = np.sqrt((x - cx)**2 + (y - cy)**2)
    water_mask = dist_from_center <= (height // 6)
    bands[3, water_mask] = 200.0
    bands[7, water_mask] = 100.0
    
    # 5. Sensor Anomaly / No-Data (Top-Right Corner Square)
    # Zero values to explicitly test division-by-zero handling in NDVI processor
    bands[3, 0:30, width-30:width] = 0.0
    bands[7, 0:30, width-30:width] = 0.0
    
    # Add simulated sensor noise (Gaussian distribution) to make it realistic
    noise = np.random.normal(loc=0.0, scale=50.0, size=(8, height, width))
    bands += noise
    
    # Clip to valid Sentinel-2 uint16 range [0, 10000] and cast
    bands = np.clip(bands, 0, 10000).astype(np.uint16)
    
    return bands


def create_test_geotiff(output_path: str, width: int = 256, height: int = 256) -> None:
    """
    Creates a synthetic multi-band GeoTIFF and saves it to disk.
    
    Args:
        output_path (str): Destination file path for the GeoTIFF.
        width (int): Image width in pixels.
        height (int): Image height in pixels.
        
    Raises:
        OSError: If the directory cannot be created or file cannot be written.
        ValueError: If the output path is invalid.
    """
    # Security & Stability: Sanitize and validate path
    abs_path = os.path.abspath(output_path)
    if not abs_path.endswith('.tif'):
        raise ValueError("Output file must have a .tif extension.")
        
    # Ensure directory exists
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    
    logger.info(f"Initializing synthetic raster creation: {width}x{height} pixels")
    
    # Generate the spectral data
    data = generate_band_data(height, width)
    
    # Define GeoTIFF metadata
    # Transform maps pixel coordinates to geographic coordinates (Niger Delta bounds)
    transform = from_bounds(*DELTA_BOUNDS, width, height)
    
    profile = {
        'driver': 'GTiff',
        'dtype': 'uint16',
        'nodata': 0,
        'width': width,
        'height': height,
        'count': 8,             # 8 Bands to match Sentinel-2 L2A structure
        'crs': CRS.from_epsg(4326), # WGS84
        'transform': transform,
        'compress': 'lzw'       # Enterprise best practice: compress to save disk space
    }
    
    try:
        with rasterio.open(abs_path, 'w', **profile) as dst:
            dst.write(data)
            # Add band descriptions for professional metadata standards
            band_names = [
                "Coastal Aerosol", "Blue", "Green", "Red", 
                "VRE1", "VRE2", "VRE3", "NIR"
            ]
            for i, name in enumerate(band_names, start=1):
                dst.update_tags(band=i, description=name)
                
        logger.info(f"Successfully generated synthetic GeoTIFF at: {abs_path}")
        logger.info("You can now run 'ndvi_processor.py' using this file as input.")
        
    except Exception as e:
        logger.error(f"Failed to write GeoTIFF: {e}")
        raise


def main() -> None:
    """Main execution block."""
    output_file = "data/test_image.tif"
    try:
        create_test_geotiff(output_file)
    except Exception as e:
        logger.critical(f"Data generation pipeline failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()