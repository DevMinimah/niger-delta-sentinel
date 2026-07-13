# 🛰️ Niger Delta Sentinel - OSINT/GEOINT Engine

**Automated ecological monitoring platform using live satellite imagery from the European Space Agency's Copernicus program.**

##  Features
- **Live Satellite Data Integration**: Fetches latest Sentinel-2 imagery directly from Copernicus Data Space Ecosystem
- **Real-Time NDVI Analysis**: Processes 120+ million pixels to calculate vegetation health indices
- **Interactive Web Dashboard**: Professional Leaflet.js map with automated geospatial visualization
- **Bandwidth Optimization**: Intelligent caching system prevents redundant downloads
- **Cloud-Native Architecture**: FastAPI backend with async processing

## 🚀 Live Demo
- **Link**: https://niger-delta-sentinel.onrender.com/

## 📸 Demo Screenshot
![Niger Delta Sentinel Dashboard](screenshots/dashboard.png)

## 🛠️ Tech Stack
- **Backend**: FastAPI (Python 3.13)
- **Frontend**: Leaflet.js + Vanilla JavaScript
- **Geospatial**: Rasterio, NumPy, GDAL
- **Data Source**: ESA Copernicus Sentinel-2 L2A
- **Authentication**: OAuth2 (CDSE)

## 📊 How It Works
1. Authenticates with Copernicus Data Space via OAuth2
2. Queries OData API for latest cloud-free Sentinel-2 scene over Niger Delta
3. Downloads ~1GB satellite archive and extracts Red/NIR bands
4. Calculates NDVI (Normalized Difference Vegetation Index)
5. Generates georeferenced visualization and statistics
6. Displays results on interactive web map

## 🌍 Use Cases
- Environmental monitoring in the Niger Delta
- Vegetation health assessment
- Deforestation detection
- Agricultural monitoring
- Disaster response and damage assessment

## 🔧 Installation
```bash
git clone https://github.com/Devminimah/niger-delta-sentinel.git
cd niger-delta-sentinel
pip install -r requirements.txt


## 🤝 Contributing & License

This project is developed as an independent research initiative.

**Copyright & License:**<br>
Copyright © 2026 Abiegbu Minimah. All rights reserved.<br>
This project is proprietary. The source code is provided for portfolio and academic demonstration purposes only.
