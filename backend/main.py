from pathlib import Path
import shutil

from fastapi import (
    FastAPI,
    UploadFile,
    File
)

from fastapi.middleware.cors import CORSMiddleware

from bg_remover import BackgroundRemover

app = FastAPI(
    title="Background Remover API",
    description="AI Background Removal API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://fanciful-creponne-1bf047.netlify.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent.parent

UPLOAD_DIR = BASE_DIR / "uploads" / "input"

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

background_remover = BackgroundRemover(
    output_directory=str(OUTPUT_DIR)
)

@app.get("/")
def home():

    return {
        "message": "Background Remover API is running"
    }

@app.post("/remove-background")
async def remove_background(
    files: list[UploadFile] = File(...)
):

    for file in UPLOAD_DIR.iterdir():

        if file.is_file():
            file.unlink()

    for file in OUTPUT_DIR.iterdir():

        if file.is_file():
            file.unlink()

    uploaded_files = []

    for file in files:

        if not file.filename:
            continue

        extension = Path(
            file.filename
        ).suffix.lower()

        if extension not in (
            ".jpg",
            ".jpeg",
            ".png",
            ".webp"
        ):
            continue

        filename = Path(
            file.filename
        ).name

        file_path = (
            UPLOAD_DIR
            / filename
        )

        with open(
            file_path,
            "wb"
        ) as buffer:

            shutil.copyfileobj(
                file.file,
                buffer
            )

        uploaded_files.append(filename)

    result = background_remover.remove_background(
        str(UPLOAD_DIR)
    )

    result["uploaded"] = len(
        uploaded_files
    )

    result["output_directory"] = str(
        OUTPUT_DIR
    )

    return result