"""
Flood Disaster Monitoring System - Synthetic Data Generator
Generates realistic multi-modal disaster datasets:
1. Satellite Images (Multispectral / Flood Extent Maps)
2. Drone Aerial Footage / Frames (Reconnaissance images & video metadata)
3. IoT Water-Level Sensors (Telemetry time-series data)
4. Weather Reports (Precipitation & Doppler Radar bulletins)
5. Emergency Alerts (State Emergency Operation Center alerts)
"""

import os
import json
import math
import random
from datetime import datetime, timedelta, timezone
import pandas as pd
from PIL import Image, ImageDraw

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASETS_DIR = os.path.join(BASE_DIR, "datasets")

DISTRICTS = [
    {"name": "Cuttack", "state": "Odisha", "lat": 20.4625, "lon": 85.8828, "river": "Mahanadi River"},
    {"name": "Wayanad", "state": "Kerala", "lat": 11.6854, "lon": 76.1320, "river": "Kabini River"},
    {"name": "Patna", "state": "Bihar", "lat": 25.5941, "lon": 85.1376, "river": "Ganges River"},
    {"name": "Guwahati", "state": "Assam", "lat": 26.1445, "lon": 91.7362, "river": "Brahmaputra River"},
    {"name": "Kolhapur", "state": "Maharashtra", "lat": 16.7050, "lon": 74.2433, "river": "Panchganga River"}
]

def ensure_dirs():
    dirs = [
        "satellite-images",
        "drone-videos",
        "sensor-data",
        "weather-reports",
        "emergency-alerts"
    ]
    for d in dirs:
        os.makedirs(os.path.join(DATASETS_DIR, d), exist_ok=True)
    print("[+] Directory structure initialized in", DATASETS_DIR)

def create_synthetic_image(filepath, title, subtitle, bg_color=(20, 40, 80), flood_level="Severe"):
    """Creates a high-contrast informative synthetic flood visual asset."""
    img = Image.new("RGB", (800, 600), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # Grid lines to mimic geospatial satellite / drone HUD
    for x in range(0, 800, 40):
        draw.line([(x, 0), (x, 600)], fill=(40, 60, 110), width=1)
    for y in range(0, 600, 40):
        draw.line([(0, y), (800, y)], fill=(40, 60, 110), width=1)
        
    # Draw simulated water body / flood polygon (randomized per image so scenes look distinct)
    flood_color = (0, 119, 182) if flood_level in ["Normal", "Moderate"] else (193, 18, 31)
    cx, cy = random.randint(300, 500), random.randint(380, 480)
    num_points = random.randint(6, 9)
    points = []
    for i in range(num_points):
        angle = (2 * 3.14159 * i / num_points) + random.uniform(-0.2, 0.2)
        radius_x = random.randint(150, 320)
        radius_y = random.randint(80, 160)
        px = cx + radius_x * math.cos(angle)
        py = cy + radius_y * math.sin(angle)
        points.append((max(30, min(770, px)), max(350, min(590, py))))
    draw.polygon(points, fill=flood_color, outline=(255, 255, 255))
    
    # Title Box
    draw.rectangle([(20, 20), (780, 100)], fill=(10, 20, 40), outline=(0, 200, 255), width=2)
    draw.text((40, 30), f"FLOOD DISASTER MONITORING - {title.upper()}", fill=(255, 255, 255))
    draw.text((40, 60), subtitle, fill=(0, 220, 255))
    
    # Status telemetry HUD overlay
    draw.rectangle([(20, 480), (450, 580)], fill=(15, 25, 45), outline=(255, 200, 0), width=1)
    draw.text((30, 490), f"STATUS: {flood_level.upper()} INUNDATION DETECTED", fill=(255, 220, 0))
    draw.text((30, 515), f"TIMESTAMP: {datetime.now(timezone.utc).isoformat()}", fill=(200, 200, 200))
    draw.text((30, 540), f"SURVEILLANCE MODE: SENTINEL-2 / THERMAL UAV", fill=(0, 255, 180))

    img.save(filepath, format="JPEG", quality=90)

def generate_satellite_datasets():
    print("[*] Generating Satellite Image Datasets...")
    sub_dir = os.path.join(DATASETS_DIR, "satellite-images")
    satellites = ["Sentinel-2B", "Landsat-9", "RISAT-1A_SAR", "Cartosat-3"]
    
    for dist in DISTRICTS:
        for sat in satellites:
            timestamp = (datetime.now(timezone.utc) - timedelta(days=random.randint(0, 5), hours=random.randint(1, 23))).strftime("%Y%m%d_%H%M%S")
            filename = f"SAT_{sat}_{dist['name']}_{timestamp}.jpg"
            filepath = os.path.join(sub_dir, filename)
            
            flood_levels = ["Normal", "Moderate", "Severe", "Critical"]
            flood_level = random.choice(flood_levels)
            
            title = f"Satellite Sensor: {sat}"
            subtitle = f"Region: {dist['name']}, {dist['state']} | Basin: {dist['river']} | Res: 10m Multispectral"
            create_synthetic_image(filepath, title, subtitle, bg_color=(15, 30, 50), flood_level=flood_level)
            
            meta = {
                "Filename": filename,
                "Location": f"{dist['name']}, {dist['state']}",
                "District": dist["name"],
                "Coordinates": f"{dist['lat']},{dist['lon']}",
                "River_Basin": dist["river"],
                "Satellite": sat,
                "Timestamp": timestamp,
                "Flood_Level": flood_level,
                "Cloud_Cover_Pct": round(random.uniform(5.0, 45.0), 2),
                "Resolution_Meters": 10.0,
                "Severity": "High" if flood_level in ["Severe", "Critical"] else "Low",
                "FileType": "image/jpeg"
            }
            with open(os.path.join(sub_dir, f"{filename}.meta.json"), "w") as f:
                json.dump(meta, f, indent=2)

def generate_drone_datasets():
    print("[*] Generating Drone Aerial Footage Datasets...")
    sub_dir = os.path.join(DATASETS_DIR, "drone-videos")
    uav_models = ["DJI-Matrice-300-RTK", "Autel-EVO-II-Dual", "IdeaForge-NETRA-V4"]
    
    for dist in DISTRICTS:
        for uav in uav_models:
            timestamp = (datetime.now(timezone.utc) - timedelta(days=random.randint(0, 3), hours=random.randint(1, 12))).strftime("%Y%m%d_%H%M%S")
            
            filename = f"UAV_{uav}_{dist['name']}_Sector_{random.randint(1, 4)}_{timestamp}.mp4"
            filepath = os.path.join(sub_dir, filename)

            flood_level = "Critical" if dist["name"] in ["Cuttack", "Wayanad"] else "Moderate"
            severity = "Extreme" if dist["name"] in ["Cuttack", "Wayanad"] else "Medium"

            frame_title = f"UAV Aerial Survey - {dist['name']}"
            frame_subtitle = f"Unit: {uav} | District: {dist['name']} | Altitude: {random.randint(120, 250)}m AGL"
            create_synthetic_image(filepath + ".jpg", frame_title, frame_subtitle, bg_color=(25, 45, 30), flood_level=flood_level)

            with open(filepath, "wb") as f:
                f.write(b"\x00\x00\x00 ftypisom\x00\x00\x02\x00isomiso2avc1mp41\x00\x00\x00\x08free" + (b"SIMULATED_UAV_SURVEILLANCE_STREAM_" * 100))

            meta = {
                "Filename": filename,
                "Location": f"{dist['name']}, {dist['state']}",
                "District": dist["name"],
                "Coordinates": f"{dist['lat'] + random.uniform(-0.05, 0.05):.4f},{dist['lon'] + random.uniform(-0.05, 0.05):.4f}",
                "Drone_ID": f"DRONE-{dist['name'][:3].upper()}-{random.randint(101, 999)}",
                "Model": uav,
                "Flight_Altitude_M": random.randint(120, 250),
                "Timestamp": timestamp,
                "Flood_Level": flood_level,
                "Severity": severity,
                "FileType": "video/mp4",
                "Duration_Sec": random.randint(180, 720)
            }
            with open(os.path.join(sub_dir, f"{filename}.meta.json"), "w") as f:
                json.dump(meta, f, indent=2)

def generate_sensor_datasets():
    print("[*] Generating IoT Water-Level Sensor Datasets...")
    sub_dir = os.path.join(DATASETS_DIR, "sensor-data")
    
    for dist in DISTRICTS:
        for station_id in range(1, 4):
            sensor_id = f"IOT-WL-{dist['name'][:3].upper()}-00{station_id}"
            now = datetime.now(timezone.utc)
            
            records = []
            base_level = 12.0 if dist["name"] in ["Cuttack", "Wayanad"] else 7.5
            danger_mark = 14.0
            
            for step in range(24):
                ts = now - timedelta(hours=24 - step)
                water_level = round(base_level + (step * 0.22) + random.uniform(-0.3, 0.4), 2)
                discharge = round(water_level * 185.5 + random.uniform(-20, 30), 1)
                rainfall_rate = round(max(0, random.uniform(5, 45) if water_level > 12.5 else random.uniform(0, 10)), 1)
                
                status = "CRITICAL_FLOOD" if water_level >= danger_mark else ("WARNING_ALERT" if water_level >= (danger_mark - 1.5) else "NORMAL")
                
                records.append({
                    "timestamp": ts.isoformat(),
                    "sensor_id": sensor_id,
                    "district": dist["name"],
                    "state": dist["state"],
                    "river": dist["river"],
                    "water_level_meters": water_level,
                    "danger_mark_meters": danger_mark,
                    "river_discharge_cumec": discharge,
                    "rainfall_rate_mm_hr": rainfall_rate,
                    "status": status,
                    "battery_pct": round(98 - (step * 0.3), 1)
                })
            
            df = pd.DataFrame(records)
            timestamp_str = now.strftime("%Y%m%d")
            csv_filename = f"SENSOR_{sensor_id}_{timestamp_str}.csv"
            json_filename = f"SENSOR_{sensor_id}_{timestamp_str}.json"
            
            df.to_csv(os.path.join(sub_dir, csv_filename), index=False)
            with open(os.path.join(sub_dir, json_filename), "w") as f:
                json.dump(records, f, indent=2)
                
            max_lvl = df["water_level_meters"].max()
            flood_status = "Critical" if max_lvl >= danger_mark else ("Severe" if max_lvl >= 12.5 else "Normal")
            severity = "High" if flood_status in ["Critical", "Severe"] else "Low"
            
            meta = {
                "Filename": csv_filename,
                "Sensor_ID": sensor_id,
                "Location": f"{dist['name']}, {dist['state']}",
                "District": dist["name"],
                "River_Basin": dist["river"],
                "Max_Water_Level_M": max_lvl,
                "Danger_Mark_M": danger_mark,
                "Timestamp": timestamp_str,
                "Flood_Level": flood_status,
                "Severity": severity,
                "FileType": "text/csv"
            }
            with open(os.path.join(sub_dir, f"{csv_filename}.meta.json"), "w") as f:
                json.dump(meta, f, indent=2)

def generate_weather_datasets():
    print("[*] Generating Weather Radar & Meteorological Bulletins...")
    sub_dir = os.path.join(DATASETS_DIR, "weather-reports")
    forecast_types = ["Doppler_Radar_Composite", "Precipitation_Nowcast", "Monsoon_Synoptic_Report"]
    
    for dist in DISTRICTS:
        for ftype in forecast_types:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H00")
            filename = f"WEATHER_{dist['name']}_{ftype}_{timestamp}.json"
            
            report = {
                "report_id": f"WR-{dist['name'][:3].upper()}-{random.randint(1000, 9999)}",
                "station_name": f"{dist['name']} IMD Doppler Radar Station",
                "district": dist["name"],
                "state": dist["state"],
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "report_type": ftype,
                "precipitation_24h_mm": round(random.uniform(45.0, 220.0), 1),
                "wind_speed_kmph": round(random.uniform(25.0, 75.0), 1),
                "barometric_pressure_hpa": round(random.uniform(988.0, 1005.0), 1),
                "cyclonic_circulation_detected": True if dist["name"] in ["Cuttack", "Guwahati"] else False,
                "flood_risk_index": round(random.uniform(0.65, 0.95), 2),
                "advisory": f"Heavy to very heavy rainfall forecast over {dist['river']} catchment area. Low-lying areas on high alert."
            }
            
            with open(os.path.join(sub_dir, filename), "w") as f:
                json.dump(report, f, indent=2)
                
            meta = {
                "Filename": filename,
                "Station_ID": report["report_id"],
                "Location": f"{dist['name']}, {dist['state']}",
                "District": dist["name"],
                "Timestamp": timestamp,
                "Flood_Level": "Severe" if report["precipitation_24h_mm"] > 100 else "Moderate",
                "Severity": "High" if report["flood_risk_index"] > 0.8 else "Medium",
                "FileType": "application/json"
            }
            with open(os.path.join(sub_dir, f"{filename}.meta.json"), "w") as f:
                json.dump(meta, f, indent=2)

def generate_emergency_alerts():
    print("[*] Generating Emergency Alert Bulletins...")
    sub_dir = os.path.join(DATASETS_DIR, "emergency-alerts")
    dates = [(datetime.now(timezone.utc) - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(4)]
    
    alert_templates = [
        {"code": "RED_ALERT", "severity": "Extreme", "flood_level": "Critical", "action": "Immediate evacuation ordered for riverbank residents along {river}."},
        {"code": "ORANGE_ALERT", "severity": "High", "flood_level": "Severe", "action": "NDRF deployment in low-lying wards of {district}. Relief shelters operational."},
        {"code": "YELLOW_ALERT", "severity": "Medium", "flood_level": "Moderate", "action": "Water levels rising above warning mark. Fishermen advised not to venture into {river}."},
        {"code": "FLASH_FLOOD_WARNING", "severity": "Extreme", "flood_level": "Critical", "action": "Upstream dam sluice gates opened. Rapid flood wave advancing downstream in {district}."}
    ]
    
    count = 1
    for date_str in dates:
        for dist in DISTRICTS:
            tmpl = random.choice(alert_templates)
            alert_id = f"ALERT-{date_str.replace('-', '')}-{dist['name'][:3].upper()}-{count:03d}"
            filename = f"ALERT_{dist['name']}_{date_str}_{count:03d}.json"
            
            payload = {
                "alert_id": alert_id,
                "issued_date": date_str,
                "timestamp": f"{date_str}T{random.randint(6, 22):02d}:{random.randint(10, 59):02d}:00Z",
                "issuing_authority": f"State Disaster Management Authority ({dist['state']})",
                "district": dist["name"],
                "state": dist["state"],
                "river_basin": dist["river"],
                "alert_code": tmpl["code"],
                "severity": tmpl["severity"],
                "flood_level": tmpl["flood_level"],
                "action_protocol": tmpl["action"].format(river=dist["river"], district=dist["name"]),
                "shelters_active": random.randint(12, 45),
                "affected_population_est": random.randint(5000, 45000)
            }
            
            with open(os.path.join(sub_dir, filename), "w") as f:
                json.dump(payload, f, indent=2)
                
            meta = {
                "Filename": filename,
                "Alert_ID": alert_id,
                "Location": f"{dist['name']}, {dist['state']}",
                "District": dist["name"],
                "Timestamp": date_str,
                "Flood_Level": tmpl["flood_level"],
                "Severity": tmpl["severity"],
                "FileType": "application/json"
            }
            with open(os.path.join(sub_dir, f"{filename}.meta.json"), "w") as f:
                json.dump(meta, f, indent=2)
            count += 1

if __name__ == "__main__":
    ensure_dirs()
    generate_satellite_datasets()
    generate_drone_datasets()
    generate_sensor_datasets()
    generate_weather_datasets()
    generate_emergency_alerts()
    print("\n[SUCCESS] Synthetic Flood Monitoring Datasets Generated Successfully!")
