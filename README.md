# Flood Disaster Monitoring System — MinIO Object Storage

Micro project: an S3-compatible object storage architecture built on MinIO for a flood disaster monitoring case study across 5 Indian districts (Cuttack, Wayanad, Patna, Guwahati, Kolhapur). See [PROJECT_REPORT.md](PROJECT_REPORT.md) for full design, architecture, and results.

## Requirements

- **Python 3.10+**
- **MinIO server binary** — included at `minio_bin/minio.exe` (Windows) and `minio_bin_linux/minio` (Linux, used for hosted deployment — see below). Both pulled via Git LFS; run `git lfs install` before cloning, or `git lfs pull` after, if you get a small pointer-file stub instead of the real ~110MB binaries.
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

## Deploying to Streamlit Community Cloud

`app.py` is self-contained for hosted deployment: on startup it checks whether a MinIO server is reachable, and if not (there's no `start_project.bat` step on a hosted platform), it automatically launches the bundled Linux MinIO binary at `minio_bin_linux/minio` as a background process, pointed at the exact dataset already committed in `minio_data/`. No live API calls or manual setup needed at deploy time.

To deploy:
1. Push this repo to GitHub (already done if you're reading this from the repo).
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with your GitHub account.
3. Click **"New app"**, select this repository, branch `main`, and set the main file to `app.py`.
4. Deploy. First boot takes a little longer than usual while MinIO starts up in the background — subsequent reruns are instant since the health check short-circuits.

**Limitations of this setup** (it's a demo-grade deployment, not production object storage):
- Streamlit Community Cloud's filesystem is ephemeral — if the app container restarts or goes to sleep from inactivity, MinIO restarts fresh from the `minio_data/` snapshot committed in the repo. Any changes made *during* a live session (there aren't any write operations in this dashboard) would not persist across restarts.
- The bundled binary only runs on Linux; on Windows it's skipped (`platform.system() != "Linux"`) and local development continues to use `start_project.bat` + `minio_bin/minio.exe` exactly as before.
- Root credentials default to `minioadmin`/`minioadmin` but can be overridden without code changes — see Security below.

## Security

- **MinIO is never internet-facing.** It's bound to `127.0.0.1` only, on this deployment or any local run — nothing outside the process itself can reach the raw S3 API or admin console directly.
- **No write/delete/upload surface is exposed.** Every control in the dashboard is a fixed-choice dropdown; there is no file uploader, no free-text field, and no `put_object`/`remove_object` call anywhere in `app.py`. It's read-only by construction.
- **Object bodies are encrypted at rest with AES-256-GCM**, implemented in `crypto_utils.py`. This is application-level encryption, not MinIO's native server-side encryption — MinIO's SSE requires a full external Key Management Service (Vault / AWS KMS / MinIO KES) in current releases, verified empirically (`MINIO_KMS_SECRET_KEY` alone does nothing; the object body is stored as plain bytes regardless). Standing up a separate KES server was judged too large and fragile an addition for a self-contained deployment, so every object is encrypted before it ever reaches MinIO and decrypted after `app.py` reads it back. GCM's authentication tag also rejects any tampered ciphertext outright.
  - **Trade-off worth knowing:** because this is application-level (not MinIO-native) encryption, only code that knows the key — i.e. `app.py` — can produce usable plaintext. Anyone who somehow obtained direct API/credential access to MinIO would get ciphertext, not the real files, unlike real S3 SSE which decrypts transparently for any authenticated caller. Object *metadata* (district, flood-level, timestamps, etc.) is intentionally left in plaintext so bucket browsing and filtering keep working without decrypting every object first — this mirrors how real S3 server-side encryption also only covers the object body, never its metadata.
  - The encryption key defaults to a fixed demo value (`crypto_utils.py`). Set `OBJECT_ENC_KEY` (env var for local scripts) or the `OBJECT_ENC_KEY` Streamlit secret (deployed app) to a random 32-byte base64 key for a real deployment — **but note that rotating it requires re-running the full upload pipeline**, since existing objects stay encrypted under whichever key was active when they were written.
- **Root credentials are overridable** via `MINIO_ROOT_USER`/`MINIO_ROOT_PASSWORD` in Streamlit secrets, without needing to touch existing data (unlike the encryption key, MinIO's root credentials aren't tied to how already-written objects were stored).
- **No dashboard authentication** — anyone with the URL can view everything. This is a deliberate choice, not an oversight: all data is either genuine public information (Open-Meteo, NASA GIBS) or disclosed synthetic/simulated content, with no PII or real secrets involved.
- **Out of scope**: DDoS protection and rate limiting are Streamlit Community Cloud platform concerns, not something this application's code can meaningfully affect.

## Data authenticity

Weather, river discharge, and satellite imagery are 100% real, live public data (Open-Meteo, NASA GIBS). Drone keyframe photos are real, location-verified photography (Wikimedia Commons); the accompanying video clips are `ffmpeg`-generated pan/zoom clips over those real photos, not raw drone footage. Emergency alerts remain simulated (no public API exists for this). Full detail and per-object disclosure in [PROJECT_REPORT.md](PROJECT_REPORT.md) §7.
