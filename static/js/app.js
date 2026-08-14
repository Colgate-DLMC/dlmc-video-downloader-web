const downloadButton = document.querySelector("#download-button");
const url_input = document.querySelector("#url-input");
const statusArea = document.querySelector("#status-area");
const statusLabel = document.querySelector("#status-label");
const downloadLink = document.querySelector("#download-link");
const statusLine = document.querySelector("#status-line");
const subtitleLink = document.querySelector("#subtitle-link")
const emailInput = document.querySelector("#email-input");

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
    const email = emailInput.value
    
    
    const response = await fetch("/download", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, format, subtitles, email })
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