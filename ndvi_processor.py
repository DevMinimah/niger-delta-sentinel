"""
Niger Delta Sentinel - Phase 1: NDVI Processor
------------------------------------------------
An OSINT/GEOINT engine module for calculating the Normalized Difference 
Vegetation Index (NDVI) from Sentinel-2 multi-band GeoTIFF imagery.

Author: [Your Name]
Project: Niger Delta Sentinel (OSINT/GEOINT Engine)
"""

import os
import sys
import logging
from typing import Tuple, Dict, Optional
import numpy as np
import rasterio
from rasterio.warp import transform_bounds
from rasterio.errors import RasterioIOError
import matplotlib.pyplot as plt

# Configure professional logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Sentinel-2 MSI Band Indices (1-based indexing for Rasterio)
# Band 4: Red (665 nm) | Band 8: Near-Infrared (842 nm)
SENTINEL2_RED_BAND = 4
SENTINEL2_NIR_BAND = 8


def calculate_ndvi(
    file_path: str, 
    red_band_idx: int = SENTINEL2_RED_BAND, 
    nir_band_idx: int = SENTINEL2_NIR_BAND
) -> Tuple[np.ndarray, dict]:
    """
    Reads a multi-band GeoTIFF and calculates the NDVI.
    """
    logger.info(f"Initiating NDVI calculation for: {file_path}")
    
    # 1. Strict Input Validation
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"The file {file_path} does not exist.")
        
    try:
        with rasterio.open(file_path) as src:
            max_band = max(red_band_idx, nir_band_idx)
            if src.count < max_band:
                raise ValueError(
                    f"Image has {src.count} bands, but requires at least {max_band} bands "
                    f"for Red (Band {red_band_idx}) and NIR (Band {nir_band_idx})."
                )
            
            # Read bands and cast to float32 immediately to prevent underflow
            red = src.read(red_band_idx).astype(np.float32)
            nir = src.read(nir_band_idx).astype(np.float32)
            
            # 🌍 FIX: Convert UTM Meters to Lat/Lng (WGS84) for Leaflet
            wgs84_bounds = transform_bounds(src.crs, "EPSG:4326", *src.bounds)
            
            metadata = {
                "crs": str(src.crs),
                "transform": src.transform,
                "width": src.width,
                "height": src.height,
                "bounds": wgs84_bounds  # Now sends correct Lat/Lng degrees!
            }
            
    except RasterioIOError as e:
        logger.error(f"Failed to read raster file: {e}")
        raise

    # 2. NDVI Calculation with Safe Division
    logger.info("Computing NDVI values...")
    denominator = nir + red
    
    # Handle division by zero
    ndvi = np.where(denominator == 0, np.nan, (nir - red) / denominator)
    
    # Clip values to the theoretical NDVI range [-1, 1]
    ndvi = np.clip(ndvi, -1.0, 1.0)
    
    logger.info("NDVI calculation completed successfully.")
    return ndvi, metadata


def visualize_ndvi(
    ndvi_array: np.ndarray, 
    output_path: str, 
    title: str = "Niger Delta NDVI Analysis"
) -> None:
    """
    Generates and saves a visual map of the NDVI results.
    
    Args:
        ndvi_array (np.ndarray): The calculated NDVI array.
        output_path (str): File path to save the generated PNG image.
        title (str): Title for the plot.
    """
    # Downsample massive satellite images to prevent Matplotlib memory crashes
    max_dim = 2048
    h, w = ndvi_array.shape
    if h > max_dim or w > max_dim:
        scale = max(h, w) / max_dim
        ndvi_array = ndvi_array[::int(scale), ::int(scale)]
        logger.info(f"Downsampled image from {h}x{w} to {ndvi_array.shape[0]}x{ndvi_array.shape[1]} for web visualization.")
    
    logger.info(f"Generating visualization and saving to: {output_path}")
    
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # RdYlGn colormap: Red (low/negative) -> Yellow (neutral) -> Green (high/positive)
    im = ax.imshow(ndvi_array, cmap='RdYlGn', vmin=-1.0, vmax=1.0, interpolation='nearest')
    
    # Add colorbar legend
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label('NDVI Value', rotation=270, labelpad=15, fontsize=12)
    
    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
    ax.axis('off') # Hide axes for a clean map look
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=100, bbox_inches='tight')
    plt.close(fig)
    
    logger.info("Visualization saved successfully.")


def categorize_vegetation(ndvi_array: np.ndarray) -> Dict[str, float]:
    """
    Categorizes NDVI pixels into vegetation health classes and calculates percentages.
    
    Args:
        ndvi_array (np.ndarray): The calculated NDVI array.
        
    Returns:
        Dict[str, float]: Dictionary containing counts and percentages for each category.
    """
    logger.info("Categorizing vegetation health...")
    
    # Filter out NaN values (water, clouds, no-data)
    valid_pixels = ndvi_array[~np.isnan(ndvi_array)]
    total_valid_pixels = valid_pixels.size
    
    if total_valid_pixels == 0:
        logger.warning("No valid pixels found in the NDVI array. Check input data.")
        return {"total_valid_pixels": 0}

    # Categorization thresholds based on standard remote sensing literature
    healthy_mask = valid_pixels > 0.4
    sparse_mask = (valid_pixels >= 0.2) & (valid_pixels <= 0.4)
    bare_mask = valid_pixels < 0.2
    
    stats = {
        "total_valid_pixels": int(total_valid_pixels),
        "healthy_count": int(np.sum(healthy_mask)),
        "healthy_pct": float(np.sum(healthy_mask) / total_valid_pixels * 100),
        "sparse_count": int(np.sum(sparse_mask)),
        "sparse_pct": float(np.sum(sparse_mask) / total_valid_pixels * 100),
        "bare_count": int(np.sum(bare_mask)),
        "bare_pct": float(np.sum(bare_mask) / total_valid_pixels * 100),
    }
    
    # Print formatted statistics to console
    print("\n" + "="*50)
    print("  NIGER DELTA VEGETATION HEALTH STATISTICS")
    print("="*50)
    print(f"  Total Valid Pixels Analyzed : {stats['total_valid_pixels']:,}")
    print("-" * 50)
    print(f"  🟢 Healthy Vegetation (>0.4): {stats['healthy_pct']:6.2f}% ({stats['healthy_count']:>10,} px)")
    print(f"  🟡 Sparse Vegetation (0.2-0.4): {stats['sparse_pct']:6.2f}% ({stats['sparse_count']:>10,} px)")
    print(f"  🔴 Bare Soil/Degraded (<0.2)  : {stats['bare_pct']:6.2f}% ({stats['bare_count']:>10,} px)")
    print("="*50 + "\n")
    
    return stats


def main(input_tiff: str, output_image: str = "ndvi_map.png") -> None:
    """
    Main execution pipeline for the NDVI Processor.
    """
    try:
        # Step 1: Calculate NDVI
        ndvi_data, metadata = calculate_ndvi(input_tiff)
        
        # Step 2: Visualize
        visualize_ndvi(ndvi_data, output_image)
        
        # Step 3: Categorize and Report
        categorize_vegetation(ndvi_data)
        
        logger.info("Pipeline execution completed successfully.")
        
    except Exception as e:
        logger.critical(f"Pipeline failed with error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    # Professional command-line argument handling
    if len(sys.argv) < 2:
        print("\nUsage: python ndvi_processor.py <path_to_geotiff>")
        print("Example: python ndvi_processor.py data/test_image.tif\n")
        sys.exit(1)
    
    INPUT_FILE = sys.argv[1]
    
    if not os.path.exists(INPUT_FILE):
        logger.error(f"Input file not found: {INPUT_FILE}")
        sys.exit(1)
    
    # Generate output filename based on input
    base_name = os.path.splitext(os.path.basename(INPUT_FILE))[0]
    OUTPUT_FILE = f"{base_name}_ndvi_output.png"
    
    main(INPUT_FILE, output_image=OUTPUT_FILE)        