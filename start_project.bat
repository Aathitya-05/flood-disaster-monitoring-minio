@echo off
echo ======================================================================
echo    FLOOD DISASTER MONITORING SYSTEM - MINIO OBJECT STORAGE
echo ======================================================================
echo [1] Starting MinIO Server on port 9100 (Console on 9101)...
set MINIO_ROOT_USER=minioadmin
set MINIO_ROOT_PASSWORD=minioadmin
start "MinIO Server" "%~dp0minio_bin\minio.exe" server "%~dp0minio_data" --address "127.0.0.1:9100" --console-address "127.0.0.1:9101"

timeout /t 3 >nul

echo [2] Starting Streamlit Interactive Operations Dashboard...
start "Flood Monitoring UI" cmd /k "python -m streamlit run app.py --server.port 8501"

echo.
echo ======================================================================
echo System started successfully!
echo - MinIO S3 API Endpoint : http://127.0.0.1:9100
echo - MinIO Web Console     : http://127.0.0.1:9101 (minioadmin / minioadmin)
echo - Streamlit Dashboard   : http://localhost:8501
echo ======================================================================
pause
