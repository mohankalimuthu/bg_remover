
from pathlib import Path
import time

from rembg import remove, new_session
from PIL import Image


class BackgroundRemover:

    # ============================================================
    # SUPPORTED IMAGE FORMATS
    # ============================================================

    SUPPORTED_EXTENSIONS = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp"
    }


    # ============================================================
    # MAX IMAGE SIZE
    # ============================================================

    MAX_SIZE = 1280


    # ============================================================
    # INITIALIZATION
    # ============================================================

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


        # IMPORTANT:
        # Do NOT load the AI model here.
        #
        # Loading the model during FastAPI startup can cause
        # Render to run out of memory before the server opens
        # its port.
        #

        self.session = None


    # ============================================================
    # LAZY MODEL LOADING
    # ============================================================

    def get_session(self):

        """
        Load the U2NetP model only when required.

        The model is loaded once and then reused for all
        subsequent images.
        """

        if self.session is None:

            print(
                "Loading background removal model..."
            )

            start = time.time()


            self.session = new_session(
                "u2netp"
            )


            elapsed = (
                time.time() - start
            )


            print(
                f"Model loaded in "
                f"{elapsed:.2f} seconds"
            )


        return self.session


    # ============================================================
    # REMOVE BACKGROUND
    # ============================================================

    def remove_background(
        self,
        input_directory: str
    ):

        input_directory = Path(
            input_directory
        )


        # --------------------------------------------------------
        # Get supported images
        # --------------------------------------------------------

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


        total_images = len(
            image_files
        )


        # --------------------------------------------------------
        # No images
        # --------------------------------------------------------

        if total_images == 0:

            return {

                "success": False,

                "message":
                    "No supported images found.",

                "total": 0,

                "processed": 0,

                "failed": 0,

                "total_time": 0,

                "results": []
            }


        # --------------------------------------------------------
        # Load model
        # --------------------------------------------------------
        #
        # The model will be loaded ONLY when the user
        # actually sends images for processing.
        #

        session = self.get_session()


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

                / f"{image_path.stem}_bg_rem.png"

            )


            try:

                print(
                    f"[{index}/{total_images}] "
                    f"Processing: "
                    f"{image_path.name}"
                )


                # ------------------------------------------------
                # Open image
                # ------------------------------------------------

                with Image.open(
                    image_path
                ) as image:


                    # --------------------------------------------
                    # Convert unsupported image modes
                    # --------------------------------------------

                    if image.mode not in (
                        "RGB",
                        "RGBA"
                    ):

                        image = image.convert(
                            "RGB"
                        )


                    # --------------------------------------------
                    # Resize large images
                    # --------------------------------------------

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


                    # --------------------------------------------
                    # Remove background
                    # --------------------------------------------

                    output_image = remove(

                        image,

                        session=session
                    )


                    # --------------------------------------------
                    # Save transparent PNG
                    # --------------------------------------------

                    output_image.save(

                        output_path,

                        "PNG",

                        optimize=False
                    )


                    # Explicitly close output image
                    output_image.close()


                # ------------------------------------------------
                # Processing completed
                # ------------------------------------------------

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


                print(

                    f"    ✓ Saved: "
                    f"{output_path.name} "
                    f"({elapsed:.2f}s)"

                )


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


                print(

                    f"    ✗ Failed: "
                    f"{image_path.name}"

                )

                print(
                    f"      Error: {error}"
                )


        # ========================================================
        # TOTAL TIME
        # ========================================================

        total_time = (

            time.time()
            - total_start

        )


        # ========================================================
        # RESPONSE
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

