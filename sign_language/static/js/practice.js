const video = document.getElementById("webcam-feed");
const canvas = document.getElementById("detection-overlay");
const ctx = canvas.getContext("2d");
const referenceVideo = document.getElementById("reference-video");
const successMessage = document.getElementById("success-message");
const nextBtn = document.getElementById("next-btn");

let streaming = false;
let detectionInProgress = false;
let targetSpan = document.getElementById("target");

let startTime = Date.now();
let framesTaken = 0;

async function startCamera() {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true });
    video.srcObject = stream;
    video.play();
    streaming = true;
}

startCamera();

// Set canvas size
video.addEventListener("loadedmetadata", () => {
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
});

// Send frame to backend
async function sendFrame() {
    if (!streaming || detectionInProgress) return;
    detectionInProgress = true;

    framesTaken++;

    const frameCanvas = document.createElement("canvas");
    frameCanvas.width = video.videoWidth;
    frameCanvas.height = video.videoHeight;
    const frameCtx = frameCanvas.getContext("2d");
    frameCtx.drawImage(video, 0, 0, frameCanvas.width, frameCanvas.height);
    const frameData = frameCanvas.toDataURL("image/jpeg");

    const data = {
        frame: frameData,
        current_level: currentLevel,
        target_text: targetLetter,
        frames_taken: framesTaken,
        current_word: currentWord || ""
    };

    try {
        const response = await fetch("/detect_asl/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        if (result.bbox) {
            const { x_min, y_min, x_max, y_max } = result.bbox;
            ctx.strokeStyle = "lime";
            ctx.lineWidth = 3;
            ctx.strokeRect(x_min, y_min, x_max - x_min, y_max - y_min);
            ctx.font = "29px Arial";
            ctx.fillStyle = "black";
            ctx.fillText(result.letter + " (" + result.accuracy.toFixed(1) + "%)", x_min, y_min - 10);
        }

        if (result.letter_success) {
            const timeTaken = (Date.now() - startTime) / 1000;

            if (currentLevel === "level-4") {
                handleLevel4LetterProgress();
            } else {
                successMessage.textContent = `YAY!Good Job!You performed ${targetLetter} correctly in ${framesTaken} frames! 🎉🎉🎉`;
                nextBtn.style.display = "inline-block";
            }
        }
    } catch (err) {
        console.error(err);
    } finally {
        detectionInProgress = false;
    }
}

setInterval(sendFrame, 1000);

function handleLevel4LetterProgress() {
    let currentLetterIndex = completedPart.length;
    const nextLetterIndex = currentLetterIndex + 1;

    if (nextLetterIndex < currentWord.length) {
        completedPart = currentWord.substring(0, nextLetterIndex);
        successMessage.textContent = `Letter "${targetLetter}" matched! Progress: "${completedPart}"`;

        targetLetter = currentWord[nextLetterIndex];
        targetSpan.textContent = targetLetter;
        referenceVideo.src = `/static/media/VideoSign/${targetLetter}.mp4`;
        referenceVideo.load();
        referenceVideo.play();
    } else {
        const timeTaken = (Date.now() - startTime) / 1000;
        successMessage.textContent = `Word "${currentWord}" completed in ${framesTaken} frames! 🎉🎉🎉`;
        nextBtn.style.display = "inline-block";
    }
}

function goToNext() {
    window.location.href = `/practice/${currentLevel}/next/`;
}
