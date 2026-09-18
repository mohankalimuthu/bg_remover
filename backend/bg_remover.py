from pathlib import Path
from rembg import remove, new_session
from PIL import Image
import time


class BackgroundRemover:

    SUPPORTED_EXTENSIONS = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp"
    }

    MAX_SIZE = 1280

    def __init__(self, output_directory: str = "outputs/bg_removed"):

        self.output_directory = Path(output_directory)

        self.output_directory.mkdir(
            parents=True,
            exist_ok=True
        )

        print("Loading background removal model...")

        start = time.time()

        # Load model ONLY ONCE
        self.session = new_session("u2net")

        print(
            f"Model loaded in "
            f"{time.time() - start:.2f} seconds"
        )

    def remove_background(
        self,
        input_directory: str
    ):

        input_directory = Path(input_directory)

        image_files = sorted(
            file
            for file in input_directory.iterdir()
            if (
                file.is_file()
                and file.suffix.lower()
                in self.SUPPORTED_EXTENSIONS
            )
        )

        total_images = len(image_files)

        if total_images == 0:
            return {
                "success": False,
                "message": "No supported images found.",
                "processed": 0
            }

        processed = 0
        failed = 0
        results = []

        total_start = time.time()

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
                    f"Processing: {image_path.name}"
                )

                with Image.open(image_path) as image:

                    if image.mode not in (
                        "RGB",
                        "RGBA"
                    ):
                        image = image.convert("RGB")

                    # Resize large images
                    if max(image.size) > self.MAX_SIZE:

                        image.thumbnail(
                            (
                                self.MAX_SIZE,
                                self.MAX_SIZE
                            ),
                            Image.Resampling.LANCZOS
                        )

                    # Remove background
                    output_image = remove(
                        image,
                        session=self.session
                    )

                    # Save as PNG
                    output_image.save(
                        output_path,
                        "PNG",
                        optimize=False
                    )

                elapsed = time.time() - start_time

                processed += 1

                results.append({
                    "input": image_path.name,
                    "output": output_path.name,
                    "status": "success",
                    "time": round(elapsed, 2)
                })

                print(
                    f"    ✓ Saved: "
                    f"{output_path.name} "
                    f"({elapsed:.2f}s)"
                )

            except Exception as error:

                failed += 1

                results.append({
                    "input": image_path.name,
                    "output": None,
                    "status": "failed",
                    "error": str(error)
                })

                print(
                    f"    ✗ Failed: "
                    f"{image_path.name}"
                )

        total_time = time.time() - total_start

        return {
            "success": True,
            "message": "Background removal completed.",
            "total": total_images,
            "processed": processed,
            "failed": failed,
            "total_time": round(total_time, 2),
            "results": results
        }