"""
Niger Delta Sentinel - Phase 2: FastAPI Web Interface
-----------------------------------------------------
Enterprise-grade backend for processing satellite imagery and serving the GEOINT dashboard.

Author: [Your Name]
Project: Niger Delta Sentinel (OSINT/GEOINT Engine)
"""

import os
import shutil
import asyncio
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Import our core GIS processing engine
from ndvi_processor import calculate_ndvi, visualize_ndvi, categorize_vegetation

app = FastAPI(
    title="Niger Delta Sentinel API",
    description="Automated OSINT/GEOINT engine for ecological monitoring.",
    version="1.0.0"
)

# CORS Middleware (Zero Trust / Security Best Practice)
# In a production EnvoShield integration, restrict allow_origins to specific domains.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure the uploads directory exists for saving incoming files and generated PNGs
os.makedirs("uploads", exist_ok=True)

# Mount the uploads folder as static files so the frontend can access the generated PNGs
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """
    Serves the main index.html dashboard.
    Using an explicit route instead of mounting the root directory prevents 
    static file routing conflicts with our API endpoints.
    """
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Frontend interface (index.html) not found.")


@app.post("/analyze")
async def analyze_geotiff(file: UploadFile = File(...)):
    """
    Accepts a GeoTIFF upload, processes it through the NDVI engine, 
    and returns the visual and statistical results.
    """
    # 1. Strict Input Validation
    if not file.filename.lower().endswith(('.tif', '.tiff')):
        raise HTTPException(status_code=400, detail="Invalid file type. Only .tif or .tiff are accepted.")
    
    # 2. Save the uploaded file securely
    file_path = os.path.join("uploads", file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        # 3. Process using the core GIS engine
        # WHY asyncio.to_thread? Rasterio and Matplotlib are synchronous, CPU-bound, and blocking.
        # Running them directly in an async endpoint would block the FastAPI event loop, 
        # freezing the server for all other users. Threading offloads this safely.
        
        # Step A: Calculate NDVI
        ndvi_array, metadata = await asyncio.to_thread(calculate_ndvi, file_path)
        
        # Step B: Generate Visualization
        base_name = os.path.splitext(file.filename)[0]
        output_image_name = f"{base_name}_ndvi.png"
        output_image_path = os.path.join("uploads", output_image_name)
        await asyncio.to_thread(visualize_ndvi, ndvi_array, output_image_path, f"NDVI: {file.filename}")
        
        # Step C: Categorize Vegetation
        stats = await asyncio.to_thread(categorize_vegetation, ndvi_array)
        
        # 4. Prepare JSON Response
        # Rasterio bounds format: (left, bottom, right, top) -> (West, South, East, North)
        left, bottom, right, top = metadata["bounds"]
        
        # Leaflet L.imageOverlay expects bounds in [[South, West], [North, East]] format
        leaflet_bounds = [[bottom, left], [top, right]]
        
        image_url = f"/uploads/{output_image_name}"
        
        return JSONResponse(content={
            "image_url": image_url,
            "bounds": leaflet_bounds,
            "stats": stats,
            "original_filename": file.filename
        })
        
    except Exception as e:
        # Enterprise error handling: Log the error and return a safe 500 response
        # without leaking internal stack traces to the client.
        print(f"CRITICAL ERROR during processing: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred during satellite image processing.")

if __name__ == "__main__":
    import uvicorn
    # Run the server. Access the dashboard at http://127.0.0.1:8000
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)