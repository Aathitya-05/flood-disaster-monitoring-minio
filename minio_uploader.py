"""
Flood Disaster Monitoring System - MinIO Ingestion & Metadata Manager
Implements Task 2, Task 3, and Task 4:
- Connects to MinIO server (S3 compatible)
- Creates structured disaster buckets
- Attaches standardized custom object metadata & tags
- Ingests datasets and performs integrity verification
"""

import os
import json
import glob
from minio import Minio
from minio.error import S3Error
from minio.commonconfig import Tags

MINIO_ENDPOINT = "127.0.0.1:9100"
ACCESS_KEY = "minioadmin"
SECRET_KEY = "minioadmin"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASETS_DIR = os.path.join(BASE_DIR, "datasets")

# Task 3: Bucket Structure
BUCKETS = [
    "satellite-images",
    "drone-videos",
    "sensor-data",
    "weather-reports",
    "emergency-alerts"
]

def get_minio_client():
    """Initializes and returns the MinIO client."""
    return Minio(
        MINIO_ENDPOINT,
        access_key=ACCESS_KEY,
        secret_key=SECRET_KEY,
        secure=False
    )

def initialize_buckets(client):
    """Task 2 & 3: Creates buckets if they don't exist."""
    print("=" * 60)
    print("[TASK 3] INITIALIZING MINIO BUCKET ARCHITECTURE")
    print("=" * 60)
    for bucket in BUCKETS:
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
            print(f" [+] Created bucket: {bucket}")
        else:
            print(f" [OK] Bucket already exists: {bucket}")
    print("[SUCCESS] All 5 disaster monitoring buckets initialized.\n")

def upload_satellite_images(client):
    bucket = "satellite-images"
    folder = os.path.join(DATASETS_DIR, bucket)
    files = [f for f in glob.glob(os.path.join(folder, "SAT_*.jpg")) if not f.endswith(".meta.json")]
    print(f"[*] Ingesting {len(files)} Satellite Image objects into '{bucket}'...")
    
    for fpath in files:
        fname = os.path.basename(fpath)
        meta_path = fpath + ".meta.json"
        
        metadata = {}
        tags = Tags.new_object_tags()
        mdata = {}
        if os.path.exists(meta_path):
            with open(meta_path, "r") as mf:
                mdata = json.load(mf)
                metadata = {
                    "location": mdata.get("Location", "Unknown"),
                    "district": mdata.get("District", "Unknown"),
                    "coordinates": mdata.get("Coordinates", ""),
                    "timestamp": mdata.get("Timestamp", ""),
                    "sensor-id": mdata.get("Satellite", "Sentinel"),
                    "flood-level": mdata.get("Flood_Level", "Moderate"),
                    "severity": mdata.get("Severity", "Medium"),
                    "file-type": mdata.get("FileType", "image/jpeg"),
                    "cloud-cover": str(mdata.get("Cloud_Cover_Pct", "0")),
                    "river-basin": mdata.get("River_Basin", ""),
                    "data-source": mdata.get("Data_Source", "Synthetic Placeholder")
                }
                tags["District"] = mdata.get("District", "")
                tags["Severity"] = mdata.get("Severity", "")
                tags["FloodLevel"] = mdata.get("Flood_Level", "")

        object_name = f"raw/{mdata.get('District', 'General')}/{fname}"
        
        client.fput_object(
            bucket_name=bucket,
            object_name=object_name,
            file_path=fpath,
            content_type="image/jpeg",
            metadata=metadata
        )
        client.set_object_tags(bucket, object_name, tags)
        print(f"  -> Uploaded {object_name} [Metadata: FloodLevel={metadata.get('flood-level')}, District={metadata.get('district')}]")

def upload_drone_videos(client):
    bucket = "drone-videos"
    folder = os.path.join(DATASETS_DIR, bucket)
    files = [f for f in glob.glob(os.path.join(folder, "UAV_*.mp4")) if not f.endswith(".meta.json")]
    print(f"\n[*] Ingesting {len(files)} Drone Footage assets into '{bucket}'...")
    
    for fpath in files:
        fname = os.path.basename(fpath)
        meta_path = fpath + ".meta.json"
        
        metadata = {}
        tags = Tags.new_object_tags()
        mdata = {}
        if os.path.exists(meta_path):
            with open(meta_path, "r") as mf:
                mdata = json.load(mf)
                metadata = {
                    "location": mdata.get("Location", "Unknown"),
                    "district": mdata.get("District", "Unknown"),
                    "coordinates": mdata.get("Coordinates", ""),
                    "timestamp": mdata.get("Timestamp", ""),
                    "sensor-id": mdata.get("Drone_ID", "UAV-UNKNOWN"),
                    "model": mdata.get("Model", ""),
                    "altitude-m": str(mdata.get("Flight_Altitude_M", "")),
                    "flood-level": mdata.get("Flood_Level", "Severe"),
                    "severity": mdata.get("Severity", "High"),
                    "file-type": mdata.get("FileType", "video/mp4"),
                    "keyframe-credit": mdata.get("Keyframe_Photo_Credit", ""),
                    "keyframe-license": mdata.get("Keyframe_Photo_License", ""),
                    "keyframe-source": mdata.get("Keyframe_Data_Source", "Synthetic Placeholder"),
                    "video-source": mdata.get("Video_Source", "Simulated Placeholder (no public real drone video of this location exists)")
                }
                tags["District"] = mdata.get("District", "")
                tags["DroneID"] = mdata.get("Drone_ID", "")
                tags["Severity"] = mdata.get("Severity", "")

        object_name = f"aerial/{mdata.get('District', 'General')}/{fname}"
        client.fput_object(
            bucket_name=bucket,
            object_name=object_name,
            file_path=fpath,
            content_type="video/mp4",
            metadata=metadata
        )
        client.set_object_tags(bucket, object_name, tags)
        
        frame_path = fpath + ".jpg"
        if os.path.exists(frame_path):
            frame_obj = f"aerial/{mdata.get('District', 'General')}/{fname}.jpg"
            client.fput_object(
                bucket_name=bucket,
                object_name=frame_obj,
                file_path=frame_path,
                content_type="image/jpeg",
                metadata=metadata
            )
        print(f"  -> Uploaded {object_name} [Metadata: DroneID={metadata.get('sensor-id')}, District={metadata.get('district')}]")

def upload_sensor_data(client):
    bucket = "sensor-data"
    folder = os.path.join(DATASETS_DIR, bucket)
    files = [f for f in glob.glob(os.path.join(folder, "SENSOR_*.csv")) if not f.endswith(".meta.json")]
    print(f"\n[*] Ingesting {len(files)} IoT Water Sensor telemetry datasets into '{bucket}'...")
    
    for fpath in files:
        fname = os.path.basename(fpath)
        meta_path = fpath + ".meta.json"
        
        metadata = {}
        tags = Tags.new_object_tags()
        mdata = {}
        if os.path.exists(meta_path):
            with open(meta_path, "r") as mf:
                mdata = json.load(mf)
                metadata = {
                    "location": mdata.get("Location", "Unknown"),
                    "district": mdata.get("District", "Unknown"),
                    "river-basin": mdata.get("River_Basin", ""),
                    "timestamp": mdata.get("Timestamp", ""),
                    "sensor-id": mdata.get("Sensor_ID", ""),
                    "flood-level": mdata.get("Flood_Level", "Moderate"),
                    "max-water-level": str(mdata.get("Max_Water_Level_M", "")),
                    "danger-mark": str(mdata.get("Danger_Mark_M", "")),
                    "severity": mdata.get("Severity", "Medium"),
                    "file-type": mdata.get("FileType", "text/csv"),
                    "data-source": mdata.get("Data_Source", "Synthetic Placeholder")
                }
                tags["District"] = mdata.get("District", "")
                tags["SensorID"] = mdata.get("Sensor_ID", "")
                tags["Severity"] = mdata.get("Severity", "")

        object_name = f"telemetry/{mdata.get('District', 'General')}/{fname}"
        client.fput_object(
            bucket_name=bucket,
            object_name=object_name,
            file_path=fpath,
            content_type="text/csv",
            metadata=metadata
        )
        client.set_object_tags(bucket, object_name, tags)
        print(f"  -> Uploaded {object_name} [Metadata: SensorID={metadata.get('sensor-id')}, MaxLevel={metadata.get('max-water-level')}m]")

def upload_weather_reports(client):
    bucket = "weather-reports"
    folder = os.path.join(DATASETS_DIR, bucket)
    files = [f for f in glob.glob(os.path.join(folder, "WEATHER_*.json")) if not f.endswith(".meta.json")]
    print(f"\n[*] Ingesting {len(files)} Doppler & Radar Weather Reports into '{bucket}'...")
    
    for fpath in files:
        fname = os.path.basename(fpath)
        meta_path = fpath + ".meta.json"
        
        metadata = {}
        tags = Tags.new_object_tags()
        mdata = {}
        if os.path.exists(meta_path):
            with open(meta_path, "r") as mf:
                mdata = json.load(mf)
                metadata = {
                    "location": mdata.get("Location", "Unknown"),
                    "district": mdata.get("District", "Unknown"),
                    "timestamp": mdata.get("Timestamp", ""),
                    "sensor-id": mdata.get("Station_ID", ""),
                    "flood-level": mdata.get("Flood_Level", "Moderate"),
                    "severity": mdata.get("Severity", "Medium"),
                    "file-type": mdata.get("FileType", "application/json"),
                    "data-source": mdata.get("Data_Source", "Synthetic Placeholder")
                }
                tags["District"] = mdata.get("District", "")
                tags["StationID"] = mdata.get("Station_ID", "")

        object_name = f"forecasts/{mdata.get('District', 'General')}/{fname}"
        client.fput_object(
            bucket_name=bucket,
            object_name=object_name,
            file_path=fpath,
            content_type="application/json",
            metadata=metadata
        )
        client.set_object_tags(bucket, object_name, tags)
        print(f"  -> Uploaded {object_name} [Metadata: StationID={metadata.get('sensor-id')}, Severity={metadata.get('severity')}]")

def upload_emergency_alerts(client):
    bucket = "emergency-alerts"
    folder = os.path.join(DATASETS_DIR, bucket)
    files = [f for f in glob.glob(os.path.join(folder, "ALERT_*.json")) if not f.endswith(".meta.json")]
    print(f"\n[*] Ingesting {len(files)} Emergency Alert Bulletins into '{bucket}'...")
    
    for fpath in files:
        fname = os.path.basename(fpath)
        meta_path = fpath + ".meta.json"
        
        metadata = {}
        tags = Tags.new_object_tags()
        mdata = {}
        if os.path.exists(meta_path):
            with open(meta_path, "r") as mf:
                mdata = json.load(mf)
                metadata = {
                    "location": mdata.get("Location", "Unknown"),
                    "district": mdata.get("District", "Unknown"),
                    "timestamp": mdata.get("Timestamp", ""),
                    "sensor-id": mdata.get("Alert_ID", ""),
                    "flood-level": mdata.get("Flood_Level", "Critical"),
                    "severity": mdata.get("Severity", "Extreme"),
                    "file-type": mdata.get("FileType", "application/json"),
                    "data-source": "Simulated (no public official-alert API exists for arbitrary district/date lookups)"
                }
                tags["District"] = mdata.get("District", "")
                tags["AlertDate"] = mdata.get("Timestamp", "")
                tags["Severity"] = mdata.get("Severity", "")

        object_name = f"bulletins/{mdata.get('Timestamp', 'archive')}/{fname}"
        client.fput_object(
            bucket_name=bucket,
            object_name=object_name,
            file_path=fpath,
            content_type="application/json",
            metadata=metadata
        )
        client.set_object_tags(bucket, object_name, tags)
        print(f"  -> Uploaded {object_name} [Metadata: AlertID={metadata.get('sensor-id')}, Date={metadata.get('timestamp')}]")

def verify_storage(client):
    """Task 2: Verifies storage integrity and prints bucket audit."""
    print("\n" + "=" * 60)
    print("[TASK 2] MINIO OBJECT STORAGE INGESTION VERIFICATION")
    print("=" * 60)
    
    total_objects = 0
    total_bytes = 0
    
    for bucket in BUCKETS:
        objects = list(client.list_objects(bucket, recursive=True))
        count = len(objects)
        bucket_size = sum(obj.size for obj in objects)
        total_objects += count
        total_bytes += bucket_size
        
        print(f"\n[*] Bucket: '{bucket}' | Objects: {count} | Total Size: {bucket_size / 1024:.2f} KB")
        for obj in objects[:3]:
            stat = client.stat_object(bucket, obj.object_name)
            meta_summary = ", ".join([f"{k}={v}" for k, v in stat.metadata.items() if k.startswith("x-amz-meta-")])
            print(f"   - {obj.object_name} ({obj.size} bytes, ETag: {obj.etag})")
            if meta_summary:
                print(f"     [Meta] {meta_summary}")
        if count > 3:
            print(f"   ... and {count - 3} more objects.")

    print("\n" + "-" * 60)
    print(f"TOTAL OBJECTS STORED : {total_objects}")
    print(f"TOTAL STORAGE FOOTPRINT: {total_bytes / (1024 * 1024):.3f} MB")
    print("=" * 60)
    print("[SUCCESS] MinIO storage verified with all buckets, datasets, and metadata!")

if __name__ == "__main__":
    client = get_minio_client()
    initialize_buckets(client)
    upload_satellite_images(client)
    upload_drone_videos(client)
    upload_sensor_data(client)
    upload_weather_reports(client)
    upload_emergency_alerts(client)
    verify_storage(client)
