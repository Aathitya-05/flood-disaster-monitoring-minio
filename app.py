"""
Flood Disaster Monitoring System - Streamlit Interactive Operations Dashboard
Provides interactive visualization and query interface over MinIO Object Storage.
"""

import io
import json
import streamlit as st
import pandas as pd
from datetime import timedelta
from minio import Minio
from PIL import Image

st.set_page_config(
    page_title="Flood Disaster Monitoring System | MinIO",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Connect to MinIO
MINIO_ENDPOINT = "127.0.0.1:9100"
ACCESS_KEY = "minioadmin"
SECRET_KEY = "minioadmin"

@st.cache_resource
def get_client():
    return Minio(
        MINIO_ENDPOINT,
        access_key=ACCESS_KEY,
        secret_key=SECRET_KEY,
        secure=False
    )

client = get_client()

# Header
st.title("🌊 Flood Disaster Monitoring System")
st.markdown("#### High-Performance Multi-Modal Object Storage Architecture powered by **MinIO**")
st.markdown("---")

# Sidebar
st.sidebar.markdown("## 🌊🛰️ MinIO")
st.sidebar.markdown("### 🎛️ Control Center")
menu = st.sidebar.radio(
    "Navigation",
    [
        "📊 Storage Overview & Buckets",
        "🛰️ Satellite Flood Maps",
        "🚁 Drone Aerial Surveillance",
        "🌊 IoT Sensor Telemetry",
        "🌦️ Weather Radar Reports",
        "🚨 Emergency Alert Bulletins",
        "🔍 Custom Query Workbench"
    ]
)

st.sidebar.markdown("---")
st.sidebar.info(
    f"**MinIO API:** `http://{MINIO_ENDPOINT}`\n\n"
    f"**MinIO Console:** `http://127.0.0.1:9101`\n\n"
    f"**S3 Storage Engine:** Active"
)

# -------------------------------------------------------------
# 1. Storage Overview & Buckets
# -------------------------------------------------------------
if menu == "📊 Storage Overview & Buckets":
    st.subheader("📦 MinIO Bucket Architecture & Storage Footprint")
    
    buckets = ["satellite-images", "drone-videos", "sensor-data", "weather-reports", "emergency-alerts"]
    
    cols = st.columns(len(buckets))
    stats = []
    
    for i, b in enumerate(buckets):
        objs = list(client.list_objects(b, recursive=True))
        total_sz = sum(o.size for o in objs)
        with cols[i]:
            st.metric(
                label=f"Bucket: {b}",
                value=f"{len(objs)} Objects",
                delta=f"{total_sz / 1024:.1f} KB"
            )
            
    st.markdown("### 📋 Bucket Inventory & Sample Objects")
    selected_bucket = st.selectbox("Select Bucket to Inspect:", buckets)
    
    objs = list(client.list_objects(selected_bucket, recursive=True))
    table_data = []
    for o in objs:
        stat = client.stat_object(selected_bucket, o.object_name)
        meta = stat.metadata
        table_data.append({
            "Object Key": o.object_name,
            "Size (Bytes)": o.size,
            "ETag Checksum": o.etag,
            "District": meta.get("x-amz-meta-district", "N/A"),
            "Flood Level": meta.get("x-amz-meta-flood-level", "N/A"),
            "Severity": meta.get("x-amz-meta-severity", "N/A"),
            "Sensor / Source ID": meta.get("x-amz-meta-sensor-id", "N/A"),
            "Last Modified": o.last_modified.strftime("%Y-%m-%d %H:%M:%S")
        })
    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True)

# -------------------------------------------------------------
# 2. Satellite Flood Maps
# -------------------------------------------------------------
elif menu == "🛰️ Satellite Flood Maps":
    st.subheader("🛰️ Satellite Inundation & Geospatial Imagery")
    
    district = st.selectbox("Select District:", ["All", "Cuttack", "Wayanad", "Patna", "Guwahati", "Kolhapur"])
    prefix = "" if district == "All" else f"raw/{district}/"
    
    objs = [o for o in client.list_objects("satellite-images", prefix=prefix, recursive=True) if o.object_name.endswith(".jpg")]
    
    st.write(f"Displaying **{len(objs)}** satellite scenes:")
    cols = st.columns(3)
    for idx, o in enumerate(objs):
        stat = client.stat_object("satellite-images", o.object_name)
        meta = stat.metadata
        
        # Read image
        response = client.get_object("satellite-images", o.object_name)
        img_bytes = response.read()
        response.close()
        response.release_conn()
        img = Image.open(io.BytesIO(img_bytes))
        
        with cols[idx % 3]:
            st.image(img, use_container_width=True)
            st.markdown(f"**Key:** `{o.object_name.split('/')[-1]}`")
            st.caption(
                f"📍 **Location:** {meta.get('x-amz-meta-location')}\n\n"
                f"🛰️ **Sensor:** {meta.get('x-amz-meta-sensor-id')} | ☁️ **Cloud:** {meta.get('x-amz-meta-cloud-cover')}%\n\n"
                f"⚠️ **Flood Level:** `{meta.get('x-amz-meta-flood-level')}`"
            )

# -------------------------------------------------------------
# 3. Drone Aerial Surveillance (Task 5.1 Demo)
# -------------------------------------------------------------
elif menu == "🚁 Drone Aerial Surveillance":
    st.subheader("🚁 Drone Aerial Reconnaissance Footage (Task 5.1)")
    st.info("Demonstrating retrieval of drone footage by district with high-speed S3 pre-signed URLs and keyframes.")
    
    district = st.selectbox("Select Surveillance District:", ["Cuttack", "Wayanad", "Patna", "Guwahati", "Kolhapur"])
    prefix = f"aerial/{district}/"
    
    objs = [o for o in client.list_objects("drone-videos", prefix=prefix, recursive=True) if o.object_name.endswith(".mp4")]
    
    st.write(f"Found **{len(objs)}** drone missions in **{district}**:")
    for o in objs:
        stat = client.stat_object("drone-videos", o.object_name)
        meta = stat.metadata
        
        url = client.presigned_get_object("drone-videos", o.object_name, expires=timedelta(hours=1))
        frame_key = o.object_name + ".jpg"
        
        c1, c2 = st.columns([1, 2])
        with c1:
            try:
                frame_res = client.get_object("drone-videos", frame_key)
                fimg = Image.open(io.BytesIO(frame_res.read()))
                frame_res.close()
                frame_res.release_conn()
                st.image(fimg, caption="Mission Reconnaissance Keyframe", use_container_width=True)
            except Exception:
                st.write("Frame preview unavailable")
                
        with c2:
            st.markdown(f"### 🚁 `{meta.get('x-amz-meta-sensor-id', 'Drone')}`")
            st.markdown(f"- **UAV Model:** {meta.get('x-amz-meta-model')} | **Altitude:** {meta.get('x-amz-meta-altitude-m')} m")
            st.markdown(f"- **District:** {meta.get('x-amz-meta-district')} (Coords: `{meta.get('x-amz-meta-coordinates')}`)")
            st.markdown(f"- **Inundation Severity:** `{meta.get('x-amz-meta-severity')}` | **Flood Level:** `{meta.get('x-amz-meta-flood-level')}`")
            st.markdown(f"- **Pre-Signed Secure Download URL:** [Download / Stream Video Stream]({url})")
            st.code(url, language="bash")
        st.markdown("---")

# -------------------------------------------------------------
# 4. IoT Sensor Telemetry (Task 5.2 Demo)
# -------------------------------------------------------------
elif menu == "🌊 IoT Sensor Telemetry":
    st.subheader("🌊 IoT Ultrasonic Water Level Sensor Telemetry (Task 5.2)")
    st.info("Demonstrating real-time streaming and analytical threshold filtering of river water levels directly from MinIO.")
    
    district = st.selectbox("Select River Basin District:", ["Cuttack", "Wayanad", "Patna", "Guwahati", "Kolhapur"])
    prefix = f"telemetry/{district}/"
    objs = [o for o in client.list_objects("sensor-data", prefix=prefix, recursive=True) if o.object_name.endswith(".csv")]
    
    for o in objs:
        stat = client.stat_object("sensor-data", o.object_name)
        meta = stat.metadata
        
        res = client.get_object("sensor-data", o.object_name)
        df = pd.read_csv(io.BytesIO(res.read()))
        res.close()
        res.release_conn()
        
        sensor_id = meta.get("x-amz-meta-sensor-id")
        danger_mark = float(meta.get("x-amz-meta-danger-mark", 14.0))
        max_level = float(meta.get("x-amz-meta-max-water-level", df["water_level_meters"].max()))
        
        st.markdown(f"#### 📡 Sensor Station: `{sensor_id}` ({meta.get('x-amz-meta-location')} - {meta.get('x-amz-meta-river-basin')})")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Current Danger Mark", f"{danger_mark:.1f} m")
        c2.metric("Peak Water Level", f"{max_level:.2f} m", delta=f"{max_level - danger_mark:+.2f} m vs Danger")
        critical_count = (df["water_level_meters"] >= danger_mark).sum()
        c3.metric("Critical Inundation Hours", f"{critical_count} / 24 hrs")
        
        # Plot time series chart
        st.line_chart(df.set_index("timestamp")[["water_level_meters", "danger_mark_meters"]])
        
        with st.expander("View Raw Telemetry Stream"):
            st.dataframe(df, use_container_width=True)
        st.markdown("---")

# -------------------------------------------------------------
# 5. Weather Radar Reports
# -------------------------------------------------------------
elif menu == "🌦️ Weather Radar Reports":
    st.subheader("🌦️ Weather Reports — Live Data (Open-Meteo)")
    st.caption("Real, live weather data fetched from the Open-Meteo public API for each district's actual coordinates. See data-source metadata on each object.")
    objs = [o for o in client.list_objects("weather-reports", recursive=True) if o.object_name.endswith(".json") and not o.object_name.endswith(".meta.json")]

    for o in objs:
        res = client.get_object("weather-reports", o.object_name)
        data = json.loads(res.read().decode("utf-8"))
        res.close()
        res.release_conn()

        report_type = data.get("report_type", "Weather Report")
        district = data.get("district", "Unknown")

        with st.expander(f"📡 {district} — {report_type}"):
            if report_type == "Live Current Conditions":
                c1, c2, c3 = st.columns(3)
                c1.metric("Temperature", f"{data.get('temperature_c')} °C")
                c2.metric("Precipitation (current)", f"{data.get('precipitation_mm')} mm")
                c3.metric("Wind Speed", f"{data.get('wind_speed_kmph')} km/h")
                c4, c5, c6 = st.columns(3)
                c4.metric("Humidity", f"{data.get('relative_humidity_pct')} %")
                c5.metric("Cloud Cover", f"{data.get('cloud_cover_pct')} %")
                c6.metric("Pressure (MSL)", f"{data.get('pressure_msl_hpa')} hPa")
            elif report_type == "3-Day Precipitation Forecast":
                dates = data.get("dates") or []
                precip = data.get("precipitation_sum_mm") or []
                prob = data.get("precipitation_probability_max_pct") or []
                if dates and precip:
                    forecast_df = pd.DataFrame({"Date": dates, "Precipitation (mm)": precip, "Max Probability (%)": prob})
                    st.dataframe(forecast_df, use_container_width=True, hide_index=True)
                    st.metric("Peak Forecast Precipitation", f"{max(p for p in precip if p is not None):.1f} mm")
            elif report_type == "Wind Synoptic Outlook":
                dates = data.get("dates") or []
                wind = data.get("windspeed_10m_max_kmph") or []
                if dates and wind:
                    wind_df = pd.DataFrame({"Date": dates, "Max Wind Speed (km/h)": wind})
                    st.dataframe(wind_df, use_container_width=True, hide_index=True)
                    st.metric("Peak Wind Speed", f"{max(w for w in wind if w is not None):.1f} km/h")
            st.caption(f"Fetched {data.get('fetched_at_utc', 'N/A')} · Source: {data.get('data_source', 'N/A')}")

# -------------------------------------------------------------
# 6. Emergency Alert Bulletins (Task 5.3 Demo)
# -------------------------------------------------------------
elif menu == "🚨 Emergency Alert Bulletins":
    st.subheader("🚨 State Emergency Operation Center Alert Bulletins (Task 5.3)")
    st.info("Demonstrating query retrieval of emergency alerts filtered by specific issuance dates.")
    
    dates = ["2026-08-23", "2026-08-22", "2026-08-21", "2026-08-20"]
    target_date = st.selectbox("Select Alert Issuance Date:", dates)
    
    prefix = f"bulletins/{target_date}/"
    objs = list(client.list_objects("emergency-alerts", prefix=prefix, recursive=True))
    
    st.write(f"Retrieved **{len(objs)}** official alert bulletins for **{target_date}**:")
    for o in objs:
        res = client.get_object("emergency-alerts", o.object_name)
        payload = json.loads(res.read().decode("utf-8"))
        res.close()
        res.release_conn()
        
        severity_color = "red" if payload["severity"] == "Extreme" else ("orange" if payload["severity"] == "High" else "blue")
        
        st.markdown(f"""
        <div style="border-left: 6px solid {severity_color}; padding: 12px 18px; margin-bottom: 12px; background: rgba(30, 40, 60, 0.4); border-radius: 4px;">
            <h4 style="margin: 0; color: #00d2ff;">🚨 {payload['alert_id']} - <span style="color: {'#ff4d4d' if payload['severity'] == 'Extreme' else '#ffa500'};">{payload['alert_code']}</span></h4>
            <p><strong>Authority:</strong> {payload['issuing_authority']} | <strong>District:</strong> {payload['district']}, {payload['state']} (Basin: {payload['river_basin']})</p>
            <p><strong>Action Protocol:</strong> {payload['action_protocol']}</p>
            <p><strong>Estimated Affected Population:</strong> {payload['affected_population_est']:,} | <strong>Active Shelters:</strong> {payload['shelters_active']}</p>
        </div>
        """, unsafe_allow_html=True)

# -------------------------------------------------------------
# 7. Custom Query Workbench
# -------------------------------------------------------------
elif menu == "🔍 Custom Query Workbench":
    st.subheader("🔍 MinIO S3 Metadata & Object Query Workbench")
    st.markdown("Execute live multi-criteria queries across MinIO buckets using custom metadata tags.")
    
    q_bucket = st.selectbox("Select Target Bucket:", ["satellite-images", "drone-videos", "sensor-data", "weather-reports", "emergency-alerts"])
    q_district = st.selectbox("Filter District:", ["Any", "Cuttack", "Wayanad", "Patna", "Guwahati", "Kolhapur"])
    q_flood_level = st.selectbox("Filter Flood Level:", ["Any", "Critical", "Severe", "Moderate", "Normal"])
    
    if st.button("🚀 Execute MinIO Query"):
        objs = list(client.list_objects(q_bucket, recursive=True))
        results = []
        for o in objs:
            if o.object_name.endswith(".meta.json"):
                continue
            stat = client.stat_object(q_bucket, o.object_name)
            meta = stat.metadata
            dist = meta.get("x-amz-meta-district", "")
            flevel = meta.get("x-amz-meta-flood-level", "")
            
            if q_district != "Any" and dist.lower() != q_district.lower():
                continue
            if q_flood_level != "Any" and flevel.lower() != q_flood_level.lower():
                continue
                
            results.append({
                "Object Key": o.object_name,
                "Size (Bytes)": o.size,
                "District": dist,
                "Flood Level": flevel,
                "Severity": meta.get("x-amz-meta-severity", ""),
                "Sensor ID": meta.get("x-amz-meta-sensor-id", ""),
                "Timestamp": meta.get("x-amz-meta-timestamp", "")
            })
            
        st.success(f"Query returned {len(results)} matching objects.")
        if results:
            st.dataframe(pd.DataFrame(results), use_container_width=True)
