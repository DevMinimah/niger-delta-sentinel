# 🛰️ Niger Delta Sentinel

**Status:** ✅ **Phase 2 (Web Interface) LIVE** | Phase 3 (Live API Integration) In Development

## 🌍 Mission
Niger Delta Sentinel is an automated **OSINT (Open-Source Intelligence)** and **GEOINT (Geospatial Intelligence)** platform designed to monitor ecological degradation in the Niger Delta. 

By leveraging satellite imagery and advanced spectral analysis, this project aims to provide verifiable, independent data on deforestation and oil pollution to support environmental governance and community justice.

##  Live Demo
🔗 **Try it now:** https://niger-delta-sentinel.onrender.com

## 🛠️ Current Capabilities (Phase 1 & 2 Complete)
✅ **NDVI Calculation Engine:** Computing the Normalized Difference Vegetation Index from Sentinel-2 multispectral imagery.  
✅ **Web Interface:** User-friendly FastAPI + Leaflet.js dashboard for uploading and analyzing satellite imagery.  
✅ **Geospatial Visualization:** Interactive map overlay showing vegetation health with geographic accuracy.  
✅ **Statistical Reporting:** Automated categorization and percentage analysis of vegetation health.  
✅ **Synthetic Data Generator:** Testing pipeline for validating algorithms.

## 🗺️ Roadmap (Phase 3 - Upcoming)
- **Live API Integration:** Automated fetching of the latest Sentinel-2 data from Copernicus Data Space.
- **Scheduled Monitoring:** Weekly automated deforestation reports.
- **Alert System:** Real-time notifications for rapid vegetation loss.
- **Multi-Index Support:** Add EVI, SAVI, and other vegetation indices.

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

**Copyright & License:**<br>
Copyright © 2026 Abiegbu Minimah. All rights reserved.<br>
This project is proprietary. The source code is provided for portfolio and academic demonstration purposes only.
