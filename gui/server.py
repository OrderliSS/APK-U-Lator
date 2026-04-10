"""FastAPI web server for APK U Lator.

Replaces the pywebview native app, allowing the UI to run in a standard
web browser while communicating with the Python backend via REST.
"""
import os
import shutil
import aiofiles
from fastapi import FastAPI, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel

from gui.api import APKLatorAPI
from core.platform_utils import get_project_root

app = FastAPI(title="APK U Lator Web Server")
api = APKLatorAPI()

# Mount frontend files
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/app", StaticFiles(directory=static_dir, html=True), name="static")


class LocationPayload(BaseModel):
    lat: float
    lng: float

class KeycodePayload(BaseModel):
    keycode: int


@app.get("/")
def read_root():
    return RedirectResponse(url="/app/")


@app.get("/api/stats")
def get_stats():
    return api.get_stats()


@app.get("/api/logs")
def get_logs():
    return api.get_logs()


@app.post("/api/vm/start")
def vm_start():
    return api.vm_start()


@app.post("/api/vm/first-boot")
def vm_first_boot():
    return api.vm_first_boot()


@app.post("/api/vm/stop")
def vm_stop():
    return api.vm_stop()


@app.post("/api/vm/restart")
def vm_restart():
    return api.vm_restart()


@app.post("/api/adb/connect")
def adb_connect():
    return api.adb_connect()


@app.post("/api/adb/disconnect")
def adb_disconnect():
    return api.adb_disconnect()


@app.get("/api/adb/packages")
def get_installed_packages():
    return api.get_installed_packages()


@app.post("/api/apk/install")
async def install_apk(file: UploadFile = File(...)):
    """Accepts an APK file from the browser, saves to temp, and installs via ADB."""
    if not api.adb.is_connected:
        return {"ok": False, "message": "ADB not connected — connect first."}

    # Save the file to a temp local file
    temp_dir = os.path.join(get_project_root(), "temp")
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, file.filename)

    try:
        async with aiofiles.open(temp_path, 'wb') as out_file:
            while content := await file.read(1024 * 1024):  # read 1MB chunk
                await out_file.write(content)

        api._emit(f"✓ Uploaded {file.filename} to local temp.")
        
        # Call the existing install_apk function
        return api.install_apk(temp_path)
    except Exception as e:
        return {"ok": False, "message": f"Upload error: {str(e)}"}
    finally:
        # Cleanup uploaded file if it still exists
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass


@app.post("/api/screenshot")
def take_screenshot():
    return api.take_screenshot()


@app.post("/api/send-key")
def send_key(payload: KeycodePayload):
    return api.send_key_event(payload.keycode)


@app.post("/api/gps")
def set_gps(payload: LocationPayload):
    return api.set_gps_location(payload.lat, payload.lng)
