"""
Flood Disaster Monitoring System - MinIO Data Retrieval Engine
Implements Task 5: Demonstrate Data Retrieval
1. Retrieve Drone footage of a specific district (e.g. Cuttack / Wayanad).
2. Retrieve Water-level sensor telemetry data (with analytical threshold filtering).
3. Retrieve Flood alerts issued on a particular date (with severity categorization).
4. Generate secure Pre-Signed URLs for emergency rescue response teams.
"""

import os
import io
import json
from datetime import timedelta
import pandas as pd
from minio import Minio
from minio.error import S3Error

MINIO_ENDPOINT = "127.0.0.1:9100"
ACCESS_KEY = "minioadmin"
SECRET_KEY = "minioadmin"

def get_minio_client():
    return Minio(
        MINIO_ENDPOINT,
        access_key=ACCESS_KEY,
        secret_key=SECRET_KEY,
        secure=False
    )

# -------------------------------------------------------------
# TASK 5.1: Retrieve Drone Footage for a Specific District
# -------------------------------------------------------------
def retrieve_drone_footage_by_district(client, target_district="Cuttack"):
    print("=" * 80)
    print(f"[TASK 5.1] QUERY: DRONE FOOTAGE FOR DISTRICT -> '{target_district.upper()}'")
    print("=" * 80)
    
    bucket = "drone-videos"
    prefix = f"aerial/{target_district}/"
    
    # 1. Query objects by prefix & inspect metadata
    objects = list(client.list_objects(bucket, prefix=prefix, recursive=True))
    video_objects = [obj for obj in objects if obj.object_name.endswith(".mp4")]
    
    print(f"Found {len(video_objects)} drone video assets for district: '{target_district}'\n")
    
    results = []
    for obj in video_objects:
        stat = client.stat_object(bucket, obj.object_name)
        meta = stat.metadata
        
        # Generate a secure pre-signed download URL valid for 2 hours
        presigned_url = client.presigned_get_object(
            bucket_name=bucket,
            object_name=obj.object_name,
            expires=timedelta(hours=2)
        )
        
        item = {
            "object_name": obj.object_name,
            "drone_id": meta.get("x-amz-meta-sensor-id", "Unknown"),
            "model": meta.get("x-amz-meta-model", "N/A"),
            "altitude_m": meta.get("x-amz-meta-altitude-m", "N/A"),
            "coordinates": meta.get("x-amz-meta-coordinates", "N/A"),
            "flood_level": meta.get("x-amz-meta-flood-level", "N/A"),
            "severity": meta.get("x-amz-meta-severity", "N/A"),
            "size_bytes": obj.size,
            "presigned_url": presigned_url
        }
        results.append(item)
        
        print(f"[+] Object Key: {item['object_name']}")
        print(f"    Drone ID: {item['drone_id']} | Model: {item['model']} | Alt: {item['altitude_m']}m")
        print(f"    Coordinates: {item['coordinates']} | Severity: {item['severity']} | Flood Level: {item['flood-level' if 'flood-level' in item else 'flood_level']}")
        print(f"    Pre-Signed Access URL: {item['presigned_url'][:75]}...")
        print("-" * 80)
        
    return results

# -------------------------------------------------------------
# TASK 5.2: Retrieve Water-Level Sensor Data & Filter Criticals
# -------------------------------------------------------------
def retrieve_water_level_sensor_data(client, target_district="Cuttack", threshold_only=True):
    print("\n" + "=" * 80)
    print(f"[TASK 5.2] QUERY: WATER-LEVEL SENSOR TELEMETRY -> DISTRICT '{target_district.upper()}'")
    print("=" * 80)
    
    bucket = "sensor-data"
    prefix = f"telemetry/{target_district}/"
    objects = list(client.list_objects(bucket, prefix=prefix, recursive=True))
    csv_objects = [obj for obj in objects if obj.object_name.endswith(".csv")]
    
    print(f"Found {len(csv_objects)} telemetry logs for district '{target_district}'. Streaming and analyzing...\n")
    
    all_telemetry = []
    for obj in csv_objects:
        # Stream CSV object directly from MinIO into pandas dataframe without disk caching
        response = client.get_object(bucket, obj.object_name)
        df = pd.read_csv(io.BytesIO(response.read()))
        response.close()
        response.release_conn()
        
        stat = client.stat_object(bucket, obj.object_name)
        sensor_id = stat.metadata.get("x-amz-meta-sensor-id", "Unknown")
        max_level = stat.metadata.get("x-amz-meta-max-water-level", "Unknown")
        danger_mark = stat.metadata.get("x-amz-meta-danger-mark", "Unknown")
        
        print(f"[*] Sensor Unit: {sensor_id} [Max Level Recorded: {max_level}m | Danger Mark: {danger_mark}m]")
        
        # Filter telemetry points exceeding danger threshold
        critical_df = df[df["water_level_meters"] >= float(danger_mark)]
        print(f"    Total Hourly Readings: {len(df)} | Critical Inundation Readings: {len(critical_df)}")
        
        if not critical_df.empty:
            sample = critical_df[["timestamp", "water_level_meters", "danger_mark_meters", "river_discharge_cumec", "status"]].tail(3)
            print("    Recent Critical Flood Telemetry Stream:")
            for _, row in sample.iterrows():
                print(f"      [{row['timestamp']}] Level: {row['water_level_meters']}m | Discharge: {row['river_discharge_cumec']} cumec | Status: {row['status']}")
        print("-" * 80)
        all_telemetry.append(df)
        
    return all_telemetry

# -------------------------------------------------------------
# TASK 5.3: Retrieve Flood Alerts Issued on a Particular Date
# -------------------------------------------------------------
def retrieve_flood_alerts_by_date(client, target_date="2026-08-23", min_severity=None):
    print("\n" + "=" * 80)
    print(f"[TASK 5.3] QUERY: FLOOD ALERTS ISSUED ON DATE -> '{target_date}'")
    print("=" * 80)
    
    bucket = "emergency-alerts"
    prefix = f"bulletins/{target_date}/"
    objects = list(client.list_objects(bucket, prefix=prefix, recursive=True))
    
    print(f"Found {len(objects)} alert bulletins issued on {target_date}.\n")
    
    matching_alerts = []
    for obj in objects:
        response = client.get_object(bucket, obj.object_name)
        payload = json.loads(response.read().decode("utf-8"))
        response.close()
        response.release_conn()
        
        stat = client.stat_object(bucket, obj.object_name)
        severity = stat.metadata.get("x-amz-meta-severity", payload.get("severity"))
        
        if min_severity and severity.lower() != min_severity.lower():
            continue
            
        matching_alerts.append(payload)
        
        print(f"[ALERT ID: {payload['alert_id']}]")
        print(f"  Authority : {payload['issuing_authority']}")
        print(f"  District  : {payload['district']}, {payload['state']} (Basin: {payload['river_basin']})")
        print(f"  Severity  : {payload['severity']} | Code: {payload['alert_code']} | Flood Level: {payload['flood_level']}")
        print(f"  Protocol  : {payload['action_protocol']}")
        print(f"  Impact    : ~{payload['affected_population_est']:,} population in danger zone | Active Shelters: {payload['shelters_active']}")
        print("-" * 80)
        
    return matching_alerts

# -------------------------------------------------------------
# EXTENDED TASK 5.4: Multi-Criteria Satellite Geospatial Search
# -------------------------------------------------------------
def retrieve_satellite_by_flood_severity(client, target_district="Wayanad", target_flood_level="Critical"):
    print("\n" + "=" * 80)
    print(f"[TASK 5.4] QUERY: SATELLITE IMAGERY -> DISTRICT='{target_district}', LEVEL='{target_flood_level}'")
    print("=" * 80)
    
    bucket = "satellite-images"
    prefix = f"raw/{target_district}/"
    objects = list(client.list_objects(bucket, prefix=prefix, recursive=True))
    
    matches = []
    for obj in objects:
        stat = client.stat_object(bucket, obj.object_name)
        flevel = stat.metadata.get("x-amz-meta-flood-level", "")
        if flevel.lower() == target_flood_level.lower():
            matches.append(obj)
            url = client.presigned_get_object(bucket, obj.object_name, expires=timedelta(hours=1))
            print(f"[+] Match Found: {obj.object_name}")
            print(f"    Satellite: {stat.metadata.get('x-amz-meta-sensor-id')} | Cloud Cover: {stat.metadata.get('x-amz-meta-cloud-cover')}%")
            print(f"    Location: {stat.metadata.get('x-amz-meta-location')} | Coords: {stat.metadata.get('x-amz-meta-coordinates')}")
            print(f"    Direct URL: {url[:70]}...")
            print("-" * 80)
    return matches

if __name__ == "__main__":
    client = get_minio_client()
    # 1. Demonstrate Drone retrieval for Cuttack & Wayanad
    retrieve_drone_footage_by_district(client, target_district="Cuttack")
    retrieve_drone_footage_by_district(client, target_district="Wayanad")
    
    # 2. Demonstrate Water level telemetry retrieval
    retrieve_water_level_sensor_data(client, target_district="Cuttack")
    
    # 3. Demonstrate Alert retrieval for specific date
    retrieve_flood_alerts_by_date(client, target_date="2026-08-23")
    
    # 4. Multi-criteria satellite retrieval
    # Level reflects real, current precipitation-derived classification (see
    # real_data_fetcher.py) - it will vary run to run as real weather changes.
    retrieve_satellite_by_flood_severity(client, target_district="Cuttack", target_flood_level="Moderate")
