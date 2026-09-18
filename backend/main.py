
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
# FASTAPI APPLICATION
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
#https://fanciful-creponne-1bf047.netlify.app
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
# We create the object here, but the AI model should NOT
# be loaded during FastAPI startup.
#
# Your BackgroundRemover class should use:
#
# self.session = None
#
# and load the model only inside get_session().
#
# ============================================================

background_remover = BackgroundRemover(
    output_directory=str(OUTPUT_DIR)
)


# ============================================================
# SUPPORTED FILE TYPES
# ============================================================

SUPPORTED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp"
}


# ============================================================
# HELPER FUNCTION
# ============================================================

def clean_directory(directory: Path):

    """
    Delete all files from a directory.
    """

    if not directory.exists():
        return

    for item in directory.iterdir():

        try:

            if item.is_file():
                item.unlink()

            elif item.is_dir():
                shutil.rmtree(item)

        except Exception as error:

            print(
                f"Could not delete {item}: {error}"
            )


# ============================================================
# ROOT / HEALTH CHECK
# ============================================================

@app.get("/")
def home():

    return {
        "status": "running",
        "message": "Background Remover API is running",
        "version": "1.0.0"
    }


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

    # --------------------------------------------------------
    # Validate request
    # --------------------------------------------------------

    if not files:

        raise HTTPException(
            status_code=400,
            detail="No files were uploaded."
        )


    # --------------------------------------------------------
    # Clean previous temporary files
    # --------------------------------------------------------

    clean_directory(
        UPLOAD_DIR
    )

    clean_directory(
        OUTPUT_DIR
    )


    uploaded_files = []


    # --------------------------------------------------------
    # Save uploaded files
    # --------------------------------------------------------

    for file in files:

        if not file.filename:
            continue


        # Get safe filename

        filename = Path(
            file.filename
        ).name


        # Get extension

        extension = Path(
            filename
        ).suffix.lower()


        # Ignore unsupported files

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


        except Exception as error:

            print(
                f"Upload failed: "
                f"{filename} - {error}"
            )


        finally:

            await file.close()


    # --------------------------------------------------------
    # Check valid images
    # --------------------------------------------------------

    if not uploaded_files:

        raise HTTPException(
            status_code=400,
            detail=(
                "No supported images were uploaded. "
                "Supported formats: JPG, JPEG, PNG, WEBP."
            )
        )


    # --------------------------------------------------------
    # Background Removal
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
            f"Background removal failed: "
            f"{error}"
        )


        raise HTTPException(
            status_code=500,
            detail=(
                "Background removal failed. "
                "Please try again."
            )
        )


    # --------------------------------------------------------
    # API Response
    # --------------------------------------------------------

    return {

        "success": True,

        "message": (
            "Background removal completed successfully."
        ),

        "uploaded": len(
            uploaded_files
        ),

        "total": result.get(
            "total",
            len(uploaded_files)
        ),

        "processed": result.get(
            "processed",
            0
        ),

        "failed": result.get(
            "failed",
            0
        ),

        "total_time": result.get(
            "total_time",
            0
        ),

        "results": result.get(
            "results",
            []
        ),

        "output_directory": (
            "outputs/bg_removed"
        )
    }
