# 🛰️ Niger Delta Sentinel

**Status:** 🚧 **Phase 1 (Backend Engine) Complete** | **Phase 2 (Web Interface) In Development**

## 🌍 Mission
Niger Delta Sentinel is an automated **OSINT (Open-Source Intelligence)** and **GEOINT (Geospatial Intelligence)** engine designed to monitor ecological degradation in the Niger Delta. 

By leveraging satellite imagery and advanced spectral analysis, this project aims to provide verifiable, independent data on deforestation and oil pollution to support environmental governance and community justice.

## 🛠️ Current Capabilities (Phase 1)
The core Python processing engine is currently operational and capable of:
*   **NDVI Calculation:** Computing the Normalized Difference Vegetation Index from Sentinel-2 multispectral imagery.
*   **Vegetation Health Analysis:** Automatically categorizing pixels into Healthy, Sparse, or Degraded vegetation.
*   **Statistical Reporting:** Generating precise data on the percentage of land cover changes.
*   **Synthetic Data Generation:** Includes a testing pipeline for validating algorithms without requiring heavy data downloads.

## 🗺️ Roadmap (Upcoming Features)
*   **Web Dashboard:** A user-friendly interface for NGOs and journalists to upload imagery and view results (FastAPI + Leaflet.js).
*   **Live API Integration:** Automated fetching of the latest Sentinel-2 data from the Copernicus Data Space.
*   **Alert System:** Automated alerts for rapid deforestation events.

## 💻 Tech Stack
*   **Core:** Python 3.10
*   **Geospatial:** Rasterio, NumPy, GeoPandas
*   **Visualization:** Matplotlib, Leaflet.js (Planned)
*   **Backend:** FastAPI (Planned)

## 🚀 Installation & Usage

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/DevMinimah/niger-delta-sentinel.git
    cd niger-delta-sentinel
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the NDVI Processor:**
    ```bash
    python ndvi_processor.py data/test_image.tif
    ```

## 🤝 Contributing & License
This project is developed as an independent research initiative.
    ```
**Copyright & License:**<br>
Copyright © 2026 Abiegbu Minimah. All rights reserved.<br>
This project is proprietary. The source code is provided for portfolio and academic demonstration purposes only.
