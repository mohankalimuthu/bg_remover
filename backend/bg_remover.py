from pathlib import Path
import time
from rembg import remove, new_session
from PIL import Image

class BackgroundRemover:
    SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
    MAX_SIZE = 1280

    def __init__(self, output_directory: str):
        self.output_directory = Path(output_directory)
        self.output_directory.mkdir(parents=True, exist_ok=True)
        self.session = None

    def get_session(self, progress_callback=None):
        if self.session is None:
            msg = "Loading background removal model..."
            print(msg)
            if progress_callback:
                progress_callback(msg)

            start = time.time()
            self.session = new_session("u2netp")
            elapsed = time.time() - start

            msg = f"Model loaded in {elapsed:.2f} seconds"
            print(msg)
            if progress_callback:
                progress_callback(msg)

        return self.session

    def remove_background(self, input_directory: str, progress_callback=None):
        input_directory = Path(input_directory)

        image_files = sorted(
            file for file in input_directory.iterdir()
            if file.is_file() and file.suffix.lower() in self.SUPPORTED_EXTENSIONS
        )

        total_images = len(image_files)

        if total_images == 0:
            return {
                "success": False,
                "message": "No supported images found.",
                "total": 0, "processed": 0, "failed": 0,
                "total_time": 0, "results": []
            }

        msg = f"Starting background removal for {total_images} images..."
        print(msg)
        if progress_callback: progress_callback(msg)

        session = self.get_session(progress_callback)
        processed = 0
        failed = 0
        results = []
        total_start = time.time()

        for index, image_path in enumerate(image_files, start=1):
            start_time = time.time()
            output_path = self.output_directory / f"{image_path.stem}_bg_rem.png"

            try:
                msg = f"[{index}/{total_images}] Processing: {image_path.name}"
                print(msg)
                if progress_callback: progress_callback(msg)

                with Image.open(image_path) as image:
                    if image.mode not in ("RGB", "RGBA"):
                        image = image.convert("RGB")

                    if max(image.size) > self.MAX_SIZE:
                        image.thumbnail((self.MAX_SIZE, self.MAX_SIZE), Image.Resampling.LANCZOS)

                    output_image = remove(image, session=session)
                    output_image.save(output_path, "PNG", optimize=False)
                    output_image.close()

                elapsed = time.time() - start_time
                processed += 1
                
                results.append({
                    "input": image_path.name,
                    "output": output_path.name,
                    "status": "success",
                    "time": round(elapsed, 2)
                })

                msg = f"    ✓ Saved: {output_path.name} ({elapsed:.2f}s)"
                print(msg)
                if progress_callback: progress_callback(msg)

            except Exception as error:
                failed += 1
                results.append({
                    "input": image_path.name,
                    "output": None,
                    "status": "failed",
                    "error": str(error)
                })

                msg_fail = f"    ✗ Failed: {image_path.name}"
                msg_err = f"      Error: {error}"
                print(msg_fail)
                print(msg_err)
                if progress_callback:
                    progress_callback(msg_fail)
                    progress_callback(msg_err)

        total_time = time.time() - total_start
        msg_comp = f"Completed: {processed}/{total_images}"
        msg_time = f"Total time: {total_time:.2f} seconds"

        print(msg_comp)
        print(msg_time)
        if progress_callback:
            progress_callback(msg_comp)
            progress_callback(msg_time)

        return {
            "success": True,
            "message": "Background removal completed.",
            "total": total_images,
            "processed": processed,
            "failed": failed,
            "total_time": round(total_time, 2),
            "results": results
        }