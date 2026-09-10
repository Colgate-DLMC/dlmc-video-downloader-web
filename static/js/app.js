const downloadButton = document.querySelector("#download-button");
const url_input = document.querySelector("#url-input");
const statusArea = document.querySelector("#status-area");
const statusLabel = document.querySelector("#status-label");
const downloadLink = document.querySelector("#download-link");
const statusLine = document.querySelector("#status-line");
const subtitleLink = document.querySelector("#subtitle-link")
const emailInput = document.querySelector("#email-input");

const languageDetectSection = document.querySelector("#language-detect-section");
const languageInput = document.querySelector("#language-input");
const detectButton = document.querySelector("#detect-button");
const detectResult = document.querySelector("#detect-result");
const detectResultMessage = document.querySelector("#detect-result-message");
const detectResultList = document.querySelector("#detect-result-list");

// New: references for the format/subtitle radio groups
const formatRadios = document.querySelectorAll('input[name="format"]');
const embedSubtitleRadio = document.querySelector('input[name="subtitles"][value="embed"]');
const noneSubtitleRadio = document.querySelector('input[name="subtitles"][value="none"]');

// Disable "embed subtitles" whenever "Audio only" is selected — you can't embed
// subtitles into a video track that isn't being downloaded.
formatRadios.forEach((radio) => {
    radio.addEventListener("change", () => {
        const selectedFormat = document.querySelector('input[name="format"]:checked').value;
        const isAudioOnly = selectedFormat === "audio_only" || selectedFormat === "audio_only_wav";

        embedSubtitleRadio.disabled = isAudioOnly;

        // If the user had "embed" selected and then switches to audio-only,
        // fall back to "none" so we never submit an invalid combination.
        if (isAudioOnly && embedSubtitleRadio.checked) {
            noneSubtitleRadio.checked = true;
        }
    });
});


downloadButton.addEventListener("click", async(event) => {
    event.preventDefault();

    const url = url_input.value;

    if (!url) {
        alert("Please paste a video URL first.");
        return;
    }

    // Disable the start button so the user cannot start multiple downloads accidentally
    downloadButton.disabled = true;

    statusArea.hidden = false;
    statusLabel.textContent = "Starting download…";
    downloadLink.hidden = true;

    // Read the currently-selected format and subtitle choices
    const format = document.querySelector('input[name="format"]:checked').value;
    const subtitles = document.querySelector('input[name="subtitles"]:checked').value;
    const language = languageInput.value.trim();
    const email = emailInput.value
    
    
    const response = await fetch("/download", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, format, subtitles, email, language })
    });

    let data;
    try {
        data = await response.json();
    } catch (parseError) {
        // Body wasn't valid JSON at all (e.g. a raw Flask 500 traceback page)
        statusLabel.textContent = "Something went wrong. Please try again.";
        statusArea.hidden = false;
        downloadButton.disabled = false;
        return;
    }



    if (!response.ok) {
        statusLabel.textContent = data.error || "Something went wrong. Please try again.";
        statusArea.hidden = false;
        downloadButton.disabled = false;
        return;
    }

    const job_id = data.download_id;


    //Topic: Polling — check the download's status every 2 seconds
    const pollTimer = setInterval(async () => {
        try {
            const statusResponse = await fetch(`/status/${job_id}`);
            const statusData = await statusResponse.json();

            // Guard: if the response has no log (e.g. a 404 error object), skip this tick safely
            if (statusData.log && statusData.log.length > 0) {
                statusLine.textContent = statusData.log[statusData.log.length - 1];
            }

            if (statusData.status === "done") {
                clearInterval(pollTimer);
                statusLabel.textContent = "Download ready";
                downloadLink.hidden = false;
                downloadLink.href = `/file/${job_id}`;

                if (statusData.subtitle_path != null) {
                    subtitleLink.hidden = false;
                    subtitleLink.href = `/file/${job_id}/subtitle`;
                }

                // Terminal state: re-enable the button so a new download can start
                downloadButton.disabled = false;
            }

            else if (statusData.status === "error") {
                clearInterval(pollTimer);
                statusLabel.textContent = "Something went wrong. Please try again.";

                // Terminal state: re-enable the button so a new download can start
                downloadButton.disabled = false;
            }
            else {
                statusLabel.textContent = "Downloading…";
            }

        } catch (error) {
            // Network failure or bad JSON. Stop polling — otherwise this same
            // error repeats every 2 seconds forever.
            clearInterval(pollTimer);
            statusLabel.textContent = "Error";
            statusLine.textContent = error.message;

            // Terminal state: re-enable the button so a new download can start
            downloadButton.disabled = false;
        }
    }, 2000);

});


// Show/hide the language section based on the subtitle choice.
// Reuses the same radio-group pattern as the existing formatRadios listener.
const subtitleRadios = document.querySelectorAll('input[name="subtitles"]');
subtitleRadios.forEach((radio) => {
    radio.addEventListener("change", () => {
        const selectedSubtitle = document.querySelector('input[name="subtitles"]:checked').value;
        const wantsSubtitles = selectedSubtitle !== "none";

        languageDetectSection.hidden = !wantsSubtitles;

        // Reset any previous result when the user changes their subtitle choice
        if (!wantsSubtitles) {
            detectResult.hidden = true;
        }
    });
});

detectButton.addEventListener("click", async (event) => {
    event.preventDefault();

    const url = url_input.value;
    const languageCode = languageInput.value.trim();

    if (!url) {
        alert("Please paste a video URL first.");
        return;
    }

    if (!languageCode) {
        alert("Please enter a language code to check (e.g. en, es, fr).");
        return;
    }

    detectButton.disabled = true;
    detectButton.textContent = "Checking…";
    detectResult.hidden = true;

    let data;
    try {
        const response = await fetch("/detect-subtitles", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url, language_code: languageCode })
        });

        try {
            data = await response.json();
        } catch (parseError) {
            // Body wasn't valid JSON at all (e.g. a raw Flask 500 traceback page)
            detectResult.hidden = false;
            detectResult.className = "detect-result is-not-found";
            detectResultMessage.textContent = "Something went wrong. Please try again.";
            detectResultList.textContent = "";
            return;
        }

        if (!response.ok) {
            detectResult.hidden = false;
            detectResult.className = "detect-result is-not-found";
            detectResultMessage.textContent = data.error || "Something went wrong. Please try again.";
            detectResultList.textContent = "";
            return;
        }

        // Render the result
        detectResult.hidden = false;

        if (data.found) {
            detectResult.className = "detect-result is-found";
            const typeLabel = data.found_as === "both"
                ? "manual and auto-generated"
                : data.found_as === "manual"
                    ? "manual"
                    : "auto-generated";
            detectResultMessage.textContent = `✅ "${languageCode}" subtitles found (${typeLabel})`;
        } else {
            detectResult.className = "detect-result is-not-found";
            detectResultMessage.textContent = `❌ "${languageCode}" subtitles not found for this video`;
        }

        detectResultList.textContent = data.all_available_languages.length > 0
            ? `Available languages: ${data.all_available_languages.join(", ")}`
            : "No subtitles (manual or auto) are available for this video.";

    } catch (error) {
        // Network failure
        detectResult.hidden = false;
        detectResult.className = "detect-result is-not-found";
        detectResultMessage.textContent = "Error";
        detectResultList.textContent = error.message;
    } finally {
        detectButton.disabled = false;
        detectButton.textContent = "Detect";
    }
});