const downloadButton = document.querySelector("#download-button");
const url_input = document.querySelector("#url-input")
const statusArea = document.querySelector("#status-area");
const statusLabel = document.querySelector("#status-label");
const downloadLink = document.querySelector("#download-link");
const statusLine = document.querySelector("#status-line");





downloadButton.addEventListener("click", async(event) => {
    event.preventDefault();

    statusArea.hidden = false;
    statusLabel.textContent = "Starting download…";
    downloadLink.hidden = true;
    // Why: the instant they click, they see the status area appear with a message. 
    // The downloadLink.hidden = true line resets the link in case they're doing a 
    // second download — otherwise an old "download ready" link could still be showing 
    // from last time. Resetting UI state at the start of an action is a good habit.


    const url = url_input.value

    const response = await fetch("/download", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url })
    });

    //parsed data
    const data = await response.json();
    
    const job_id = data.download_id

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


