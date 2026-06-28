// ===============================
// AUDIO ENGINE (STABLE)
// ===============================

let audioCtx = null;

function initAudio() {
    if (!audioCtx) {
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }

    if (audioCtx.state === "suspended") {
        audioCtx.resume();
    }
}

// unlock audio on first click
document.addEventListener("click", initAudio, { once: true });

function beep(duration = 180, frequency = 880, volume = 0.3) {

    if (!audioCtx) return;

    if (audioCtx.state === "suspended") {
        audioCtx.resume();
    }

    const oscillator = audioCtx.createOscillator();
    const gainNode = audioCtx.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(audioCtx.destination);

    oscillator.type = "sine";
    oscillator.frequency.value = frequency;
    gainNode.gain.value = volume;

    oscillator.start();

    setTimeout(() => {
        oscillator.stop();
    }, duration);
}

// ===============================
// ALERT CONFIG (LOCAL)
// ===============================

let alertSeconds = 3;
let lastBeepTime = 0;

// get alert seconds from UI
function getAlertSeconds() {

    const value = document.getElementById("alertTime").value;

    if (value === "custom") {
        const custom = document.getElementById("customAlert").value;
        return parseInt(custom || "3");
    }

    return parseInt(value);
}

// sync settings (no backend needed for timing)
function updateAlertSettings() {
    alertSeconds = getAlertSeconds();
}

// ===============================
// UI EVENTS
// ===============================

document.addEventListener("DOMContentLoaded", () => {

    const alertTime = document.getElementById("alertTime");
    const customAlert = document.getElementById("customAlert");

    alertTime.addEventListener("change", () => {

        if (alertTime.value === "custom") {
            customAlert.style.display = "block";
        } else {
            customAlert.style.display = "none";
        }

        updateAlertSettings();
    });

    customAlert.addEventListener("input", updateAlertSettings);

    updateAlertSettings();
});

// ===============================
// CHARTS
// ===============================

const attentionChart = new Chart(
    document.getElementById("attentionChart"),
    {
        type: "line",
        data: {
            labels: [],
            datasets: [{
                label: "Attention",
                data: [],
                borderColor: "#00ff88",
                backgroundColor: "rgba(0,255,136,.2)",
                fill: true,
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { ticks: { color: "white" } },
                y: { min: 0, max: 100, ticks: { color: "white" } }
            }
        }
    }
);

const emotionChart = new Chart(
    document.getElementById("emotionChart"),
    {
        type: "doughnut",
        data: {
            labels: ["Neutral", "Focused", "Sad", "Surprised"],
            datasets: [{
                data: [0, 0, 0, 0]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: "white" } }
            }
        }
    }
);

// ===============================
// MAIN LOOP
// ===============================

async function update() {

    const res = await fetch("/status");
    const data = await res.json();

    document.getElementById("status").innerHTML =
        data.focused ? "🟢 Focused" : "🔴 Not Focused";

    document.getElementById("attention").innerText = data.attention;
    document.getElementById("emotion").innerText = data.emotion;
    document.getElementById("focusTime").innerText = Math.round(data.focus_time || 0);
    document.getElementById("awayTime").innerText = Math.round(data.away_time || 0);
    document.getElementById("message").innerText = data.message;

    // ===============================
    // ALERT LOGIC (FRONTEND CONTROLLED)
    // ===============================

    const now = Date.now();

    if (data.current_away >= alertSeconds) {

        // prevent spam (2 sec cooldown)
        if (now - lastBeepTime > 2000) {
            beep();
            lastBeepTime = now;
        }
    }

    // ===============================
    // CHART UPDATE
    // ===============================

    attentionChart.data.labels = data.history.map((_, i) => i);
    attentionChart.data.datasets[0].data = data.history;
    attentionChart.update();

    emotionChart.data.datasets[0].data = [
        data.emotion_history.neutral,
        data.emotion_history.focused,
        data.emotion_history.sad,
        data.emotion_history.surprised
    ];
    emotionChart.update();
}

// ===============================
// ACTIONS
// ===============================

async function toggleCamera() {
    await fetch("/toggle_camera", { method: "POST" });
}

async function resetStats() {
    await fetch("/reset_stats", { method: "POST" });
}

// ===============================
// START
// ===============================

setInterval(update, 1000);
update();