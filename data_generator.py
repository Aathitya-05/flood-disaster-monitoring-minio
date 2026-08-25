"""
Flood Disaster Monitoring System - Simulated Emergency Alert Generator

Satellite imagery, drone keyframe photography, sensor telemetry, and
weather reports are all sourced from real public data by
real_data_fetcher.py. Emergency alerts remain simulated here since no
public API serves official district-level flood alerts filterable by
date - see PROJECT_REPORT.md section 7 for the full authenticity
breakdown.
"""

import os
import json
import random
from datetime import datetime, timedelta, timezone

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
    generate_emergency_alerts()
    print("\n[SUCCESS] Emergency alert bulletins generated successfully!")
