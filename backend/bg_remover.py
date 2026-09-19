from pathlib import Path
import time

from rembg import remove, new_session
from PIL import Image


class BackgroundRemover:

    SUPPORTED_EXTENSIONS = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp"
    }

    MAX_SIZE = 1280

    def __init__(
        self,
        output_directory: str = "outputs/bg_removed"
    ):

        self.output_directory = Path(
            output_directory
        )

        self.output_directory.mkdir(
            parents=True,
            exist_ok=True
        )

        # Lazy loading
        self.session = None

    # ============================================================
    # LAZY MODEL
    # ============================================================

    def get_session(self, progress_callback=None):

        if self.session is None:

            if progress_callback:
                progress_callback(
                    "Loading background removal model..."
                )

            print(
                "Loading background removal model..."
            )

            start = time.time()

            self.session = new_session(
                "u2netp"
            )

            elapsed = time.time() - start

            message = (
                f"Model loaded in "
                f"{elapsed:.2f} seconds"
            )

            print(message)

            if progress_callback:
                progress_callback(message)

        return self.session

    # ============================================================
    # REMOVE BACKGROUND
    # ============================================================

    def remove_background(
        self,
        input_directory: str,
        progress_callback=None
    ):

        input_directory = Path(
            input_directory
        )

        image_files = sorted(

            file

            for file in input_directory.iterdir()

            if (
                file.is_file()
                and
                file.suffix.lower()
                in self.SUPPORTED_EXTENSIONS
            )
        )

        total_images = len(image_files)

        # --------------------------------------------------------
        # No images
        # --------------------------------------------------------

        if total_images == 0:

            return {
                "success": False,
                "message": "No supported images found.",
                "total": 0,
                "processed": 0,
                "failed": 0,
                "total_time": 0,
                "results": []
            }

        # --------------------------------------------------------
        # Starting
        # --------------------------------------------------------

        message = (
            f"Starting background removal "
            f"for {total_images} images..."
        )

        print(message)

        if progress_callback:
            progress_callback(message)

        # --------------------------------------------------------
        # Load model
        # --------------------------------------------------------

        session = self.get_session(
            progress_callback
        )

        processed = 0
        failed = 0
        results = []

        total_start = time.time()

        # ========================================================
        # PROCESS IMAGES
        # ========================================================

        for index, image_path in enumerate(
            image_files,
            start=1
        ):

            start_time = time.time()

            output_path = (

                self.output_directory
                /
                f"{image_path.stem}_bg_rem.png"

            )

            try:

                message = (
                    f"[{index}/{total_images}] "
                    f"Processing: "
                    f"{image_path.name}"
                )

                print(message)

                if progress_callback:
                    progress_callback(message)

                # ------------------------------------------------
                # Open image
                # ------------------------------------------------

                with Image.open(
                    image_path
                ) as image:

                    # Convert mode

                    if image.mode not in (
                        "RGB",
                        "RGBA"
                    ):

                        image = image.convert(
                            "RGB"
                        )

                    # Resize

                    if max(
                        image.size
                    ) > self.MAX_SIZE:

                        image.thumbnail(

                            (
                                self.MAX_SIZE,
                                self.MAX_SIZE
                            ),

                            Image.Resampling.LANCZOS
                        )

                    # ------------------------------------------------
                    # Remove background
                    # ------------------------------------------------

                    output_image = remove(
                        image,
                        session=session
                    )

                    # ------------------------------------------------
                    # Save
                    # ------------------------------------------------

                    output_image.save(
                        output_path,
                        "PNG",
                        optimize=False
                    )

                    output_image.close()

                elapsed = (
                    time.time()
                    - start_time
                )

                processed += 1

                results.append({

                    "input":
                        image_path.name,

                    "output":
                        output_path.name,

                    "status":
                        "success",

                    "time":
                        round(
                            elapsed,
                            2
                        )

                })

                message = (
                    f"    ✓ Saved: "
                    f"{output_path.name} "
                    f"({elapsed:.2f}s)"
                )

                print(message)

                if progress_callback:
                    progress_callback(message)

            except Exception as error:

                failed += 1

                results.append({

                    "input":
                        image_path.name,

                    "output":
                        None,

                    "status":
                        "failed",

                    "error":
                        str(error)

                })

                message = (
                    f"    ✗ Failed: "
                    f"{image_path.name}"
                )

                print(message)

                if progress_callback:
                    progress_callback(message)

                error_message = (
                    f"      Error: {error}"
                )

                print(error_message)

                if progress_callback:
                    progress_callback(
                        error_message
                    )

        # ========================================================
        # TOTAL TIME
        # ========================================================

        total_time = (
            time.time()
            - total_start
        )

        completed_message = (
            f"Completed: "
            f"{processed}/{total_images}"
        )

        total_message = (
            f"Total time: "
            f"{total_time:.2f} seconds"
        )

        print(completed_message)
        print(total_message)

        if progress_callback:
            progress_callback(
                completed_message
            )

            progress_callback(
                total_message
            )

        # ========================================================
        # RETURN
        # ========================================================

        return {

            "success": True,

            "message":
                "Background removal completed.",

            "total":
                total_images,

            "processed":
                processed,

            "failed":
                failed,

            "total_time":
                round(
                    total_time,
                    2
                ),

            "results":
                results
        }