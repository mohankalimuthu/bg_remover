from pathlib import Path
import shutil

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException
)

from fastapi.middleware.cors import CORSMiddleware

from bg_remover import BackgroundRemover


# ============================================================
# FASTAPI APP
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

    allow_origins=[
        "https://fanciful-creponne-1bf047.netlify.app"
    ],

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
#
# IMPORTANT:
# BackgroundRemover object is created,
# but model should NOT load inside __init__().
#
# bg_remover.py must use:
#
# self.session = None
#
# and load u2netp only when processing starts.
#

background_remover = BackgroundRemover(
    output_directory=str(OUTPUT_DIR)
)


# ============================================================
# SUPPORTED EXTENSIONS
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
        "message": "Background Remover API is running",
        "version": "1.0.0"
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


# ============================================================
# REMOVE BACKGROUND
# ============================================================

@app.post("/remove-background")
async def remove_background(
    files: list[UploadFile] = File(...)
):

    print(
        f"Received {len(files)} files"
    )


    # --------------------------------------------------------
    # Validate files
    # --------------------------------------------------------

    if not files:

        raise HTTPException(
            status_code=400,
            detail="No files uploaded."
        )


    # --------------------------------------------------------
    # Clean previous files
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # Save uploaded images
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # Validate uploaded images
    # --------------------------------------------------------

    if not uploaded_files:

        raise HTTPException(
            status_code=400,
            detail=(
                "No supported images found. "
                "Use JPG, JPEG, PNG or WEBP."
            )
        )


    # --------------------------------------------------------
    # Process images
    # --------------------------------------------------------

    try:

        print(
            f"Starting background removal "
            f"for {len(uploaded_files)} images..."
        )


        result = (
            background_remover
            .remove_background(
                str(UPLOAD_DIR)
            )
        )


    except Exception as error:

        print(
            f"Background removal error: {error}"
        )

        raise HTTPException(
            status_code=500,
            detail="Background removal failed."
        )


    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    return {

        "success": True,

        "message":
            "Background removal completed.",

        "uploaded":
            len(uploaded_files),

        "total":
            result.get(
                "total",
                0
            ),

        "processed":
            result.get(
                "processed",
                0
            ),

        "failed":
            result.get(
                "failed",
                0
            ),

        "total_time":
            result.get(
                "total_time",
                0
            ),

        "results":
            result.get(
                "results",
                []
            )
    }