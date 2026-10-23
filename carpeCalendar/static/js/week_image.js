const poster = document.getElementById("week-poster");
const posterDays = document.getElementById("week-poster-days");
const preview = poster.parentElement;

// Shrink the text until every event fits on the poster
function fitPosterText() {
    let fontSize = 30;
    poster.style.fontSize = fontSize + "px";
    while (posterDays.scrollHeight > posterDays.clientHeight && fontSize > 14) {
        fontSize -= 1;
        poster.style.fontSize = fontSize + "px";
    }
}

function fitPreview() {
    preview.style.setProperty("--preview-scale", Math.min(0.5, preview.parentElement.clientWidth / 1080));
}

async function downloadPoster(format) {
    // Render at full size, without the preview scaling
    const options = { width: 1080, height: 1350, pixelRatio: 1, style: { transform: "none" } };
    const dataUrl = format === "png"
        ? await htmlToImage.toPng(poster, options)
        : await htmlToImage.toJpeg(poster, { ...options, quality: 0.95, backgroundColor: "#fff" });
    const link = document.createElement("a");
    link.download = posterFilename + "." + format;
    link.href = dataUrl;
    link.click();
}

document.getElementById("download-png").addEventListener("click", () => downloadPoster("png"));
document.getElementById("download-jpg").addEventListener("click", () => downloadPoster("jpg"));
window.addEventListener("resize", fitPreview);
document.fonts.ready.then(fitPosterText);
fitPreview();
fitPosterText();
