const downloadButton = document.querySelector("#download-button");
const url_input = document.querySelector("#url-input");
const statusArea = document.querySelector("#status-area");
const statusLabel = document.querySelector("#status-label");
const downloadLink = document.querySelector("#download-link");
const statusLine = document.querySelector("#status-line");
const subtitleLink = document.querySelector("#subtitle-link")


// New: references for the format/subtitle radio groups
const formatRadios = document.querySelectorAll('input[name="format"]');
const embedSubtitleRadio = document.querySelector('input[name="subtitles"][value="embed"]');
const noneSubtitleRadio = document.querySelector('input[name="subtitles"][value="none"]');

// Disable "embed subtitles" whenever "Audio only" is selected — you can't embed
// subtitles into a video track that isn't being downloaded.
formatRadios.forEach((radio) => {
    radio.addEventListener("change", () => {
        const isAudioOnly = document.querySelector('input[name="format"]:checked').value === "audio_only";

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

    statusArea.hidden = false;
    statusLabel.textContent = "Starting download…";
    downloadLink.hidden = true;


    const url = url_input.value;

    // Read the currently-selected format and subtitle choices
    const format = document.querySelector('input[name="format"]:checked').value;
    const subtitles = document.querySelector('input[name="subtitles"]:checked').value;

    const response = await fetch("/download", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, format, subtitles })
    });

    //parsed data
    const data = await response.json();

    const job_id = data.download_id;

     //Topic: Polling — check the download's status every 2 seconds
    const pollTimer = setInterval(async () => {
        const statusResponse = await fetch(`/status/${job_id}`);
        const data = await statusResponse.json();

        // Guard: if the response has no log (e.g. a 404 error object), skip this tick safely
        if (data.log && data.log.length > 0) {
            statusLine.textContent = data.log[data.log.length - 1];
        }

        if (data.status === "done") {
            clearInterval(pollTimer);
            statusLabel.textContent = "Download ready";
            downloadLink.hidden = false;
            downloadLink.href = `/file/${job_id}`;

            if (data.subtitle_path != null){
                subtitleLink.hidden = false;
                subtitleLink.href = `/file/${job_id}/subtitle`;
            }

        }

        else if (data.status === "error") {
            clearInterval(pollTimer);
            statusLabel.textContent = "Something went wrong. Please try again.";
        }
        else {
            statusLabel.textContent = "Downloading…";
        }
    }, 2000);

});

downloadSubtitleButton.addEventListener("click", async(event) => {



});