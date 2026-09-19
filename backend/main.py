from pathlib import Path
import shutil
import json
import queue
import threading

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException
)

from fastapi.middleware.cors import CORSMiddleware

from fastapi.responses import StreamingResponse

from bg_remover import BackgroundRemover


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="Background Remover API",
    description="AI Background Removal API",
    version="1.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"]
)


# ============================================================
# DIRECTORIES
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

UPLOAD_DIR = (
    BASE_DIR
    / "uploads"
    / "input"
)

OUTPUT_DIR = (
    BASE_DIR
    / "outputs"
    / "bg_removed"
)

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# BACKGROUND REMOVER
# ============================================================

background_remover = BackgroundRemover(
    output_directory=str(
        OUTPUT_DIR
    )
)


# ============================================================
# EXTENSIONS
# ============================================================

SUPPORTED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp"
}


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def home():

    return {
        "status": "running",
        "message":
            "Background Remover API is running",
        "version": "1.0.0"
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


# ============================================================
# REMOVE BACKGROUND - STREAMING
# ============================================================

@app.post("/remove-background")
async def remove_background(
    files: list[UploadFile] = File(...)
):

    # ========================================================
    # VALIDATION
    # ========================================================

    if not files:

        raise HTTPException(
            status_code=400,
            detail="No files uploaded."
        )

    print(
        f"Received {len(files)} files"
    )

    # ========================================================
    # CLEAN OLD FILES
    # ========================================================

    for item in UPLOAD_DIR.iterdir():

        if item.is_file():
            item.unlink()

        elif item.is_dir():
            shutil.rmtree(item)

    for item in OUTPUT_DIR.iterdir():

        if item.is_file():
            item.unlink()

        elif item.is_dir():
            shutil.rmtree(item)

    # ========================================================
    # SAVE UPLOADS
    # ========================================================

    uploaded_files = []

    for file in files:

        if not file.filename:
            continue

        filename = Path(
            file.filename
        ).name

        extension = Path(
            filename
        ).suffix.lower()

        if extension not in SUPPORTED_EXTENSIONS:

            print(
                f"Skipping unsupported file: "
                f"{filename}"
            )

            continue

        file_path = (
            UPLOAD_DIR
            / filename
        )

        try:

            with open(
                file_path,
                "wb"
            ) as buffer:

                shutil.copyfileobj(
                    file.file,
                    buffer
                )

            uploaded_files.append(
                filename
            )

        finally:

            await file.close()

    # ========================================================
    # VALIDATE
    # ========================================================

    if not uploaded_files:

        raise HTTPException(
            status_code=400,
            detail=(
                "No supported images found. "
                "Use JPG, JPEG, PNG or WEBP."
            )
        )

    # ========================================================
    # PROGRESS QUEUE
    # ========================================================

    progress_queue = queue.Queue()

    # ========================================================
    # SEND PROGRESS
    # ========================================================

    def send_progress(message):

        progress_queue.put({
            "type": "progress",
            "message": message
        })

    # ========================================================
    # PROCESS IN BACKGROUND
    # ========================================================

    def process_images():

        try:

            result = (
                background_remover
                .remove_background(
                    str(UPLOAD_DIR),
                    progress_callback=send_progress
                )
            )

            progress_queue.put({

                "type": "result",

                "data": result

            })

        except Exception as error:

            print(
                f"Background removal error: "
                f"{error}"
            )

            progress_queue.put({

                "type": "error",

                "message":
                    str(error)

            })

        finally:

            progress_queue.put({
                "type": "done"
            })

    # ========================================================
    # START THREAD
    # ========================================================

    thread = threading.Thread(
        target=process_images,
        daemon=True
    )

    thread.start()

    # ========================================================
    # STREAM RESPONSE
    # ========================================================

    async def event_stream():

        # First message

        yield (
            json.dumps({
                "type": "info",
                "message":
                    f"Received "
                    f"{len(uploaded_files)} files"
            })
            + "\n"
        )

        while True:

            message = (
                await __import__(
                    "asyncio"
                ).to_thread(
                    progress_queue.get
                )
            )

            yield (
                json.dumps(message)
                + "\n"
            )

            if message["type"] == "done":

                break

    return StreamingResponse(

        event_stream(),

        media_type="application/x-ndjson",

        headers={

            "Cache-Control":
                "no-cache",

            "Connection":
                "keep-alive",

            "X-Accel-Buffering":
                "no"

        }
    )