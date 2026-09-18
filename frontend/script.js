const folderInput = document.getElementById("folderInput");
const folderName = document.getElementById("folderName");
const imageCount = document.getElementById("imageCount");
const processButton = document.getElementById("processButton");

const progressContainer =
    document.getElementById("progressContainer");

const progressBar =
    document.getElementById("progressBar");

const progressText =
    document.getElementById("progressText");

const result =
    document.getElementById("result");


const API_URL =
    "http://127.0.0.1:8000/remove-background";

const SUPPORTED_EXTENSIONS = [
    ".jpg",
    ".jpeg",
    ".png",
    ".webp"
];



folderInput.addEventListener("change", () => {

    const files = Array.from(folderInput.files);

    const imageFiles = files.filter(file => {

        const extension =
            "." +
            file.name
                .split(".")
                .pop()
                .toLowerCase();

        return SUPPORTED_EXTENSIONS.includes(
            extension
        );
    });


    if (imageFiles.length === 0) {

        folderName.textContent =
            "No supported images found";

        imageCount.textContent =
            "0 images";

        processButton.disabled = true;

        return;
    }


    const firstFile = files[0];

    const pathParts =
        firstFile.webkitRelativePath.split("/");

    const selectedFolder =
        pathParts[0];


    folderName.textContent =
        ` ${selectedFolder}`;


    imageCount.textContent =
        `${imageFiles.length} images selected`;


    processButton.disabled = false;


    result.innerHTML = "";

});

processButton.addEventListener(
    "click",
    async () => {

        const files =
            Array.from(folderInput.files);

        const imageFiles = files.filter(file => {

            const extension =
                "." +
                file.name
                    .split(".")
                    .pop()
                    .toLowerCase();

            return SUPPORTED_EXTENSIONS.includes(
                extension
            );
        });


        if (imageFiles.length === 0) {

            alert("Please select an image folder.");

            return;
        }

        processButton.disabled = true;

        progressContainer.style.display =
            "block";

        progressBar.style.width =
            "5%";

        progressText.textContent =
            "Uploading images...";


        result.innerHTML = "";

        const formData =
            new FormData();


        imageFiles.forEach(file => {

            formData.append(
                "files",
                file,
                file.name
            );

        });


        try {

            progressBar.style.width =
                "20%";

            progressText.textContent =
                `Uploading ${imageFiles.length} images...`;


            const response =
                await fetch(
                    API_URL,
                    {
                        method: "POST",
                        body: formData
                    }
                );


            if (!response.ok) {

                throw new Error(
                    `Server error: ${response.status}`
                );

            }

            progressBar.style.width =
                "90%";

            progressText.textContent =
                "Processing completed. Preparing results...";


            const data =
                await response.json();

            progressBar.style.width =
                "100%";

            progressText.textContent =
                "Completed ";


            if (data.success) {

                result.innerHTML = `

                    <div class="success">

                        <h3>
                            Background Removal Completed ✓
                        </h3>

                        <br>

                        <p>
                            <strong>Total:</strong>
                            ${data.total}
                        </p>

                        <p>
                            <strong>Processed:</strong>
                            ${data.processed}
                        </p>

                        <p>
                            <strong>Failed:</strong>
                            ${data.failed}
                        </p>

                        <p>
                            <strong>Total Time:</strong>
                            ${data.total_time} seconds
                        </p>

                        <br>

                        <p>
                             Output saved to:
                        </p>

                        <code>
                            outputs/bg_removed/
                        </code>

                    </div>

                `;

            } else {

                result.innerHTML = `

                    <div class="error">

                        ${data.message}

                    </div>

                `;

            }


        } catch (error) {

            console.error(error);


            progressBar.style.width =
                "0%";


            progressText.textContent =
                "Processing failed";


            result.innerHTML = `

                <div class="error">

                    <h3>
                         Error
                    </h3>

                    <p>
                        ${error.message}
                    </p>

                    <br>

                    <p>
                        Make sure FastAPI backend
                        is running.
                    </p>

                </div>

            `;

        }


        // Enable button again

        processButton.disabled = false;

    }
);