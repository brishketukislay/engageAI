
// AUDIO ENGINE (STABLE)

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
// ALERT CONFIG (SYNCHRONIZED WITH BACKEND)

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

// sync settings with backend
async function updateAlertSettings() {
    const threshold = getAlertSeconds();
    const enabled = document.getElementById("enableAlert").checked;

    try {
        await fetch("/update_alert", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                threshold: threshold,
                enabled: enabled
            })
        });
    } catch (e) {
        console.error("Failed to update alert settings:", e);
    }
}

// UI EVENTS

document.addEventListener("DOMContentLoaded", () => {

    const alertTime = document.getElementById("alertTime");
    const customAlert = document.getElementById("customAlert");
    const enableAlert = document.getElementById("enableAlert");

    alertTime.addEventListener("change", () => {

        if (alertTime.value === "custom") {
            customAlert.style.display = "block";
        } else {
            customAlert.style.display = "none";
        }

        updateAlertSettings();
    });

    customAlert.addEventListener("input", updateAlertSettings);
    enableAlert.addEventListener("change", updateAlertSettings);

    updateAlertSettings();
});

async function toggleSession() {
    const button = document.getElementById("sessionButton");
    const active = button.dataset.active === "true";

    if (!active) {
        await fetch("/start_session", { method: "POST" });
        button.innerText = "⏹️ End Session";
        button.dataset.active = "true";
        document.getElementById("sessionReport").innerText = "Session in progress...";
        return;
    }

    const res = await fetch("/end_session", { method: "POST" });
    const data = await res.json();
    button.innerText = "▶️ Start Session";
    button.dataset.active = "false";
    document.getElementById("sessionReport").innerText = data.report || "Session ended. Report ready.";
}

// CHARTS

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

// MAIN LOOP

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
    document.getElementById("sessionReport").innerText = data.session_report || document.getElementById("sessionReport").innerText;
    document.getElementById("sessionButton").dataset.active = data.session_active ? "true" : "false";
    document.getElementById("sessionButton").innerText = data.session_active ? "⏹️ End Session" : "▶️ Start Session";

    // ALERT LOGIC (SYNCHRONIZED WITH BACKEND)

    const now = Date.now();

    if (data.alert_enabled && data.current_away >= data.alert_threshold) {

        // prevent spam (2 sec cooldown)
        if (now - lastBeepTime > 2000) {
            beep();
            lastBeepTime = now;
        }
    }

    // UPDATE ALERT STATUS TEXT
    const alertStatusEl = document.getElementById("alertStatus");
    if (!data.alert_enabled) {
        alertStatusEl.innerText = "⚪ Alerts Disabled";
        alertStatusEl.style.color = "#c7d0da";
    } else if (data.alert_triggered || data.current_away >= data.alert_threshold) {
        alertStatusEl.innerText = "🚨 Look at the screen!";
        alertStatusEl.style.color = "#ff4a4a";
    } else {
        alertStatusEl.innerText = "🟢 Monitoring...";
        alertStatusEl.style.color = "#00ff88";
    }


    // CHART UPDATE


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

// ACTIONS

async function toggleCamera() {
    await fetch("/toggle_camera", { method: "POST" });
}

async function resetStats() {
    await fetch("/reset_stats", { method: "POST" });
}

// START

setInterval(update, 1000);
update();