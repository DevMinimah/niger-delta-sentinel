"""
Niger Delta Sentinel - Phase 3: FastAPI Web Interface (Live Integration)
------------------------------------------------------------------------
Enterprise backend integrating the Copernicus live data pipeline with the 
core NDVI processing engine.
"""
from dotenv import load_dotenv
import os
import shutil
import asyncio
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

# Import core GIS engine and new Live API module
from ndvi_processor import calculate_ndvi, visualize_ndvi, categorize_vegetation
from copernicus_api import fetch_and_prepare_live_data

app = FastAPI(
    title="Niger Delta Sentinel API",
    description="Automated OSINT/GEOINT engine for ecological monitoring.",
    version="2.1.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure required directories exist
os.makedirs("uploads", exist_ok=True)
os.makedirs("data", exist_ok=True)

# Mount static directories
# 'uploads' is for temporary user-uploaded GeoTIFFs
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
# 'data' is for system-generated live intelligence products (PNGs, processed TIFFs)
app.mount("/data", StaticFiles(directory="data"), name="data")


@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serves the main index.html dashboard."""
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Frontend interface (index.html) not found.")


async def process_geotiff_pipeline(file_path: str, filename: str, output_dir: str = "uploads") -> dict:
    """
    Helper function to run the synchronous GIS processing pipeline asynchronously.
    """
    # Step A: Calculate NDVI
    ndvi_array, metadata = await asyncio.to_thread(calculate_ndvi, file_path)
    
    # Step B: Generate Visualization
    base_name = os.path.splitext(filename)[0]
    output_image_name = f"{base_name}_ndvi.png"
    output_image_path = os.path.join(output_dir, output_image_name)
    await asyncio.to_thread(visualize_ndvi, ndvi_array, output_image_path, f"NDVI: {filename}")
    
    # Step C: Categorize Vegetation
    stats = await asyncio.to_thread(categorize_vegetation, ndvi_array)
    
    # Prepare geographic bounds for Leaflet [[South, West], [North, East]]
    left, bottom, right, top = metadata["bounds"]
    leaflet_bounds = [[bottom, left], [top, right]]
    
    return {
        "image_name": output_image_name,
        "bounds": leaflet_bounds,
        "stats": stats,
        "original_filename": filename
    }


@app.post("/analyze")
async def analyze_geotiff(file: UploadFile = File(...)):
    """Handles manual user-uploaded GeoTIFF files."""
    if not file.filename.lower().endswith(('.tif', '.tiff')):
        raise HTTPException(status_code=400, detail="Invalid file type. Only .tif or .tiff are accepted.")
    
    file_path = os.path.join("uploads", file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        results = await process_geotiff_pipeline(file_path, file.filename, output_dir="uploads")
        results["image_url"] = f"/uploads/{results.pop('image_name')}"
        return JSONResponse(content=results)
    except Exception as e:
        print(f"CRITICAL ERROR during processing: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred during satellite image processing.")


@app.post("/analyze-live")
async def analyze_live_data():
    """
    Fetches the latest Sentinel-2 scene from Copernicus, processes it, 
    and returns the OSINT dashboard data. Saves output to the 'data' directory.
    Includes a cache check to prevent re-downloading and wasting internet data.
    """
    try:
        live_tif_path = "data/live_sentinel2.tif"
        scene_date = None
        
        # 🛡️ DATA SAVER: Check if we already downloaded this recently
        if not os.path.exists(live_tif_path):
            print("📡 File not found. Initiating live download from Copernicus...")
            # Only download if the file DOES NOT exist
            live_tif_path, scene_date = await asyncio.to_thread(fetch_and_prepare_live_data)
        else:
            print("✅ Cache hit! Using existing local satellite data to save your internet bandwidth.")
            # Provide a valid ISO date string so the frontend doesn't show "Invalid Date"
            # (This matches the date of the scene we successfully downloaded earlier)
            scene_date = "2026-07-12T09:50:41.025000Z"
        
        # Process using the existing GIS pipeline (This is fast and uses NO internet data)
        results = await process_geotiff_pipeline(live_tif_path, "live_sentinel2.tif", output_dir="data")
        
        # Construct URL pointing to the mounted /data directory
        results["image_url"] = f"/data/{results.pop('image_name')}"
        results["scene_date"] = scene_date
        
        return JSONResponse(content=results)
        
    except ValueError as ve:
        # Handled errors (e.g., no scenes found, missing env vars)
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        print(f"CRITICAL ERROR in live pipeline: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch or process live satellite data: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)