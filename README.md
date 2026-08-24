# Flood Disaster Monitoring System — MinIO Object Storage

Micro project: an S3-compatible object storage architecture built on MinIO for a flood disaster monitoring case study across 5 Indian districts (Cuttack, Wayanad, Patna, Guwahati, Kolhapur). See [PROJECT_REPORT.md](PROJECT_REPORT.md) for full design, architecture, and results.

## Requirements

- **Python 3.10+**
- **MinIO server binary** — included at `minio_bin/minio.exe` (pulled via Git LFS; run `git lfs install` before cloning, or `git lfs pull` after, if you get a small pointer-file stub instead of the real ~113MB binary)
- **ffmpeg** (optional) — used to generate real playable drone-mission video clips; falls back to a placeholder file if not found. [Download here](https://ffmpeg.org/download.html) if you don't have it.
- Internet access — only needed if you regenerate the dataset (`real_data_fetcher.py` calls live public APIs)

## Setup

```bash
pip install -r requirements.txt
```

## Running the project

### Quick start (uses the dataset already included in this repo)

```bash
start_project.bat
```

This starts the MinIO server (S3 API on port 9100, web console on port 9101) and the Streamlit dashboard (port 8501) against the existing `minio_data/` — no regeneration needed.

- Dashboard: http://localhost:8501
- MinIO Console: http://127.0.0.1:9101 (login `minioadmin` / `minioadmin`)

### Full pipeline (regenerate the dataset from scratch)

Run these one at a time, from the project root, with the MinIO server already running (start it first via `start_project.bat`, or manually — see below):

```bash
python real_data_fetcher.py   # fetches REAL weather, river discharge, satellite imagery, and drone keyframe photos
python data_generator.py      # generates the simulated emergency-alerts bulletins (no public real-time alert API exists)
python minio_uploader.py      # creates buckets, uploads everything to MinIO with full metadata
```

### Verification / demo scripts

```bash
python dataset_verifier.py    # Task 2: integrity + metadata compliance audit across all buckets
python minio_retriever.py     # Task 5: demonstrates all retrieval queries (drone by district, sensor data, alerts by date, etc.)
```

### Starting MinIO manually (if not using start_project.bat)

```bash
set MINIO_ROOT_USER=minioadmin
set MINIO_ROOT_PASSWORD=minioadmin
minio_bin\minio.exe server minio_data --address "127.0.0.1:9100" --console-address "127.0.0.1:9101"
```

### Starting just the dashboard

```bash
streamlit run app.py --server.port 8501
```

## Data authenticity

Weather, river discharge, and satellite imagery are 100% real, live public data (Open-Meteo, NASA GIBS). Drone keyframe photos are real, location-verified photography (Wikimedia Commons); the accompanying video clips are `ffmpeg`-generated pan/zoom clips over those real photos, not raw drone footage. Emergency alerts remain simulated (no public API exists for this). Full detail and per-object disclosure in [PROJECT_REPORT.md](PROJECT_REPORT.md) §7.
