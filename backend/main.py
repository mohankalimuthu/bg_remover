import os
import shutil
import json
import queue
import threading
import asyncio
import tempfile
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from bg_remover import BackgroundRemover

app = FastAPI(
    title="Background Remover API",
    description="AI Background Removal API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

TEMP_BASE = Path(tempfile.gettempdir()) / "bg_remover_app"
UPLOAD_DIR = TEMP_BASE / "uploads"
OUTPUT_DIR = TEMP_BASE / "outputs"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

background_remover = BackgroundRemover(output_directory=str(OUTPUT_DIR))
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

@app.get("/")
def home():
    return {"status": "running", "message": "Background Remover API is running", "version": "1.0.0"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/remove-background")
async def remove_background(files: list[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")
    
    print(f"Received {len(files)} files")

    # Clean old temp files to prevent Cloud Run memory leaks
    for item in UPLOAD_DIR.iterdir():
        if item.is_file(): item.unlink()
        elif item.is_dir(): shutil.rmtree(item)

    for item in OUTPUT_DIR.iterdir():
        if item.is_file(): item.unlink()
        elif item.is_dir(): shutil.rmtree(item)

    # Save Uploaded Files
    uploaded_files = []
    for file in files:
        if not file.filename:
            continue
        
        filename = Path(file.filename).name
        extension = Path(filename).suffix.lower()
        
        if extension not in SUPPORTED_EXTENSIONS:
            print(f"Skipping unsupported file: {filename}")
            continue

        file_path = UPLOAD_DIR / filename
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            uploaded_files.append(filename)
        finally:
            await file.close()

    if not uploaded_files:
        raise HTTPException(status_code=400, detail="No supported images found. Use JPG, JPEG, PNG or WEBP.")


    progress_queue = queue.Queue()

    def send_progress(message):
        progress_queue.put({"type": "progress", "message": message})

    def process_images():
        try:
            result = background_remover.remove_background(
                str(UPLOAD_DIR), 
                progress_callback=send_progress
            )
            progress_queue.put({"type": "result", "data": result})
        except Exception as error:
            print(f"Background removal error: {error}")
            progress_queue.put({"type": "error", "message": str(error)})
        finally:
            progress_queue.put({"type": "done"})

    thread = threading.Thread(target=process_images, daemon=True)
    thread.start()

    async def event_stream():
        yield json.dumps({
            "type": "info", 
            "message": f"Received {len(uploaded_files)} files"
        }) + "\n"
        
        while True:
            message = await asyncio.to_thread(progress_queue.get)
            yield json.dumps(message) + "\n"
            if message["type"] == "done":
                break

    return StreamingResponse(
        event_stream(),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@app.get("/download/{filename}")
def download_file(filename: str):
    safe_filename = Path(filename).name
    file_path = OUTPUT_DIR / safe_filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found.")

    return FileResponse(path=file_path, filename=safe_filename, media_type="image/png")