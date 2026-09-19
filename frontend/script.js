const folderInput =
    document.getElementById("folderInput");

const folderName =
    document.getElementById("folderName");

const imageCount =
    document.getElementById("imageCount");

const processButton =
    document.getElementById("processButton");

const progressContainer =
    document.getElementById("progressContainer");

const progressBar =
    document.getElementById("progressBar");

const progressText =
    document.getElementById("progressText");

const result =
    document.getElementById("result");

const processingLogContainer =
    document.getElementById("processingLogContainer");

const processLog =
    document.getElementById("processLog");


// ============================================================
// API URL
// ============================================================

const API_URL =
    "http://127.0.0.1:8000/remove-background";

// Render:
// const API_URL =
//     "https://bg-remover-vysf.onrender.com/remove-background";


const SUPPORTED_EXTENSIONS = [
    ".jpg",
    ".jpeg",
    ".png",
    ".webp"
];


// ============================================================
// FOLDER SELECTION
// ============================================================

folderInput.addEventListener(
    "change",
    () => {

        const files =
            Array.from(
                folderInput.files
            );

        const imageFiles =
            files.filter(
                (file) => {

                    const extension =
                        "." +
                        file.name
                            .split(".")
                            .pop()
                            .toLowerCase();

                    return SUPPORTED_EXTENSIONS
                        .includes(
                            extension
                        );
                }
            );


        if (
            imageFiles.length === 0
        ) {

            folderName.textContent =
                "No supported images found";

            imageCount.textContent =
                "0 images";

            processButton.disabled =
                true;

            return;
        }


        const firstFile =
            files[0];

        const pathParts =
            firstFile
                .webkitRelativePath
                .split("/");

        const selectedFolder =
            pathParts[0];


        folderName.textContent =
            selectedFolder;

        imageCount.textContent =
            `${imageFiles.length} images selected`;

        processButton.disabled =
            false;

        result.innerHTML = "";

        processingLogContainer.style.display =
            "none";

        processLog.textContent = "";
    }
);


// ============================================================
// PROCESS BUTTON
// ============================================================

processButton.addEventListener(
    "click",
    async () => {

        const files =
            Array.from(
                folderInput.files
            );


        const imageFiles =
            files.filter(
                (file) => {

                    const extension =
                        "." +
                        file.name
                            .split(".")
                            .pop()
                            .toLowerCase();

                    return SUPPORTED_EXTENSIONS
                        .includes(
                            extension
                        );
                }
            );


        if (
            imageFiles.length === 0
        ) {

            alert(
                "Please select an image folder."
            );

            return;
        }


        // ====================================================
        // INITIAL UI
        // ====================================================

        processButton.disabled =
            true;

        progressContainer.style.display =
            "block";

        processingLogContainer.style.display =
            "block";

        progressBar.style.width =
            "5%";

        progressText.textContent =
            "Preparing images...";

        processLog.textContent =
            "";

        result.innerHTML =
            "";


        // ====================================================
        // FORM DATA
        // ====================================================

        const formData =
            new FormData();


        imageFiles.forEach(
            (file) => {

                formData.append(
                    "files",
                    file,
                    file.name
                );

            }
        );


        try {

            // =================================================
            // UPLOADING
            // =================================================

            progressBar.style.width =
                "10%";

            progressText.textContent =
                `Uploading ${imageFiles.length} images...`;


            // =================================================
            // SEND REQUEST
            // =================================================

            const response =
                await fetch(
                    API_URL,
                    {
                        method: "POST",
                        body: formData
                    }
                );


            if (
                !response.ok
            ) {

                throw new Error(
                    `Server error: ${response.status}`
                );
            }


            // =================================================
            // CHECK STREAM
            // =================================================

            if (
                !response.body
            ) {

                throw new Error(
                    "Streaming response is not supported by the browser."
                );
            }


            const reader =
                response.body.getReader();


            const decoder =
                new TextDecoder();


            let buffer =
                "";

            let finalData =
                null;


            // =================================================
            // READ STREAM
            // =================================================

            while (true) {

                const {
                    value,
                    done
                } =
                    await reader.read();


                if (done) {

                    break;
                }


                buffer +=
                    decoder.decode(
                        value,
                        {
                            stream: true
                        }
                    );


                const lines =
                    buffer.split("\n");


                buffer =
                    lines.pop();


                for (
                    const line
                    of lines
                ) {

                    if (
                        !line.trim()
                    ) {

                        continue;
                    }


                    let data;


                    try {

                        data =
                            JSON.parse(
                                line
                            );

                    } catch (jsonError) {

                        console.warn(
                            "Invalid stream data:",
                            line
                        );

                        continue;
                    }


                    // =========================================
                    // INFO / PROGRESS
                    // =========================================

                    if (
                        data.type === "info" ||
                        data.type === "progress"
                    ) {

                        processLog.textContent +=
                            data.message +
                            "\n";


                        processLog.scrollTop =
                            processLog.scrollHeight;


                        // =====================================
                        // IMAGE PROGRESS
                        // =====================================

                        const match =
                            data.message.match(
                                /\[(\d+)\/(\d+)\]/
                            );


                        if (
                            match
                        ) {

                            const current =
                                parseInt(
                                    match[1],
                                    10
                                );

                            const total =
                                parseInt(
                                    match[2],
                                    10
                                );


                            const percentage =
                                20 +
                                (
                                    current /
                                    total
                                ) *
                                70;


                            progressBar.style.width =
                                `${percentage}%`;


                            progressText.textContent =
                                `Processing ${current}/${total}`;
                        }


                        // =====================================
                        // MODEL LOADING
                        // =====================================

                        else if (
                            data.message.includes(
                                "Loading background removal model"
                            )
                        ) {

                            progressText.textContent =
                                "Loading AI model...";
                        }


                        // =====================================
                        // MODEL LOADED
                        // =====================================

                        else if (
                            data.message.includes(
                                "Model loaded"
                            )
                        ) {

                            progressText.textContent =
                                "AI model loaded. Processing images...";
                        }


                        // =====================================
                        // COMPLETED
                        // =====================================

                        if (
                            data.message.includes(
                                "Completed:"
                            )
                        ) {

                            progressBar.style.width =
                                "95%";

                            progressText.textContent =
                                "Finalizing...";
                        }
                    }


                    // =========================================
                    // FINAL RESULT
                    // =========================================

                    if (
                        data.type === "result"
                    ) {

                        finalData =
                            data.data;
                    }


                    // =========================================
                    // ERROR
                    // =========================================

                    if (
                        data.type === "error"
                    ) {

                        throw new Error(
                            data.message
                        );
                    }
                }
            }


            // =================================================
            // FINISHED
            // =================================================

            progressBar.style.width =
                "100%";

            progressText.textContent =
                "Completed ✓";


            // =================================================
            // DISPLAY RESULT
            // =================================================

            if (
                finalData &&
                finalData.success
            ) {

                result.innerHTML = `

                    <div class="success">

                        <h3>
                            Background Removal Completed ✓
                        </h3>

                        <br>

                        <p>
                            <strong>Total:</strong>
                            ${finalData.total}
                        </p>

                        <p>
                            <strong>Processed:</strong>
                            ${finalData.processed}
                        </p>

                        <p>
                            <strong>Failed:</strong>
                            ${finalData.failed}
                        </p>

                        <p>
                            <strong>Total Time:</strong>
                            ${finalData.total_time}
                            seconds
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
            }


        } catch (error) {

            console.error(
                "Processing error:",
                error
            );


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


        // ====================================================
        // ENABLE BUTTON
        // ====================================================

        processButton.disabled =
            false;
    }
);