
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
let currentSessionReportText = "";

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

async function startSession() {
    const startBtn = document.getElementById("startSessionBtn");
    const endBtn = document.getElementById("endSessionBtn");
    const sessionStatus = document.getElementById("sessionStatus");

    try {
        const res = await fetch("/start_session", { method: "POST" });
        const data = await res.json();

        startBtn.disabled = true;
        endBtn.disabled = false;
        endBtn.classList.add("end-btn-active");

        sessionStatus.innerText = "⏱ Session in progress...";
        sessionStatus.style.color = "#00ff88";
        
        // Reset local charts if any
        if (attentionChart) {
            attentionChart.data.labels = [];
            attentionChart.data.datasets[0].data = [];
            attentionChart.update();
        }
        if (emotionChart) {
            emotionChart.data.datasets[0].data = [0, 0, 0, 0];
            emotionChart.update();
        }
    } catch (e) {
        console.error("Failed to start session:", e);
        sessionStatus.innerText = "Error starting session";
        sessionStatus.style.color = "#ff4a4a";
    }
}

async function endSession() {
    const startBtn = document.getElementById("startSessionBtn");
    const endBtn = document.getElementById("endSessionBtn");
    const sessionStatus = document.getElementById("sessionStatus");

    sessionStatus.innerText = "🤖 Generating report...";
    sessionStatus.style.color = "#ffb000";
    endBtn.disabled = true;
    endBtn.classList.remove("end-btn-active");

    try {
        const res = await fetch("/end_session", { method: "POST" });
        const data = await res.json();

        startBtn.disabled = false;
        sessionStatus.innerText = "No active session";
        sessionStatus.style.color = "#c7d0da";

        currentSessionReportText = data.session_report;
        renderReportCharts(data.history, data.emotion_history);
        showReport(data.session_report);
    } catch (e) {
        console.error("Failed to end session:", e);
        sessionStatus.innerText = "Error generating report";
        sessionStatus.style.color = "#ff4a4a";
        endBtn.disabled = false;
        endBtn.classList.add("end-btn-active");
    }
}

function showReport(reportMd) {
    const reportContent = document.getElementById("reportContent");
    if (reportContent) {
        reportContent.innerHTML = parseMarkdown(reportMd);
    }
    const modal = document.getElementById("reportModal");
    if (modal) {
        modal.style.display = "block";
    }
}

function closeReport() {
    const modal = document.getElementById("reportModal");
    if (modal) {
        modal.style.display = "none";
    }
}

function parseMarkdown(md) {
    if (!md) return "";
    return md
        .replace(/^### (.*$)/gim, '<h3>$1</h3>')
        .replace(/^## (.*$)/gim, '<h2>$1</h2>')
        .replace(/^# (.*$)/gim, '<h1>$1</h1>')
        .replace(/^\* (.*$)/gim, '<li>$1</li>')
        .replace(/^- (.*$)/gim, '<li>$1</li>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`(.*?)`/g, '<code>$1</code>')
        .replace(/\n/g, '<br>');
}

// CHARTS (GUARDED FROM REF ERROR)
let attentionChart = null;
let emotionChart = null;
let reportAttentionChart = null;
let reportEmotionChart = null;

function initCharts() {
    if (typeof Chart === "undefined") {
        console.warn("Chart.js is not loaded. Dashboard charts are disabled.");
        document.querySelectorAll(".chart-card").forEach(card => {
            card.innerHTML = `<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#c7d0da;font-size:14px;padding:20px;text-align:center;">📊 Chart.js could not be loaded. Graphs are unavailable.</div>`;
        });
        return;
    }

    attentionChart = new Chart(
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

    emotionChart = new Chart(
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
}

function renderReportCharts(history, emotionHistory) {
    if (typeof Chart === "undefined") {
        const modalCharts = document.querySelector(".modal-charts-grid");
        if (modalCharts) {
            modalCharts.innerHTML = `<div style="grid-column: span 2; display:flex;align-items:center;justify-content:center;height:150px;color:#c7d0da;font-size:14px;">📊 Chart.js could not be loaded. Report graphs are unavailable.</div>`;
        }
        return;
    }

    if (reportAttentionChart) reportAttentionChart.destroy();
    if (reportEmotionChart) reportEmotionChart.destroy();

    const attCanvas = document.getElementById("reportAttentionChart");
    const emoCanvas = document.getElementById("reportEmotionChart");
    if (!attCanvas || !emoCanvas) return;

    reportAttentionChart = new Chart(
        attCanvas,
        {
            type: "line",
            data: {
                labels: history.map((_, i) => i),
                datasets: [{
                    label: "Attention Timeline",
                    data: history,
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

    reportEmotionChart = new Chart(
        emoCanvas,
        {
            type: "doughnut",
            data: {
                labels: ["Neutral", "Focused", "Sad", "Surprised"],
                datasets: [{
                    data: [
                        emotionHistory.neutral,
                        emotionHistory.focused,
                        emotionHistory.sad,
                        emotionHistory.surprised
                    ]
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
}

// Initialize charts on DOM content loaded
document.addEventListener("DOMContentLoaded", () => {
    initCharts();
});

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

    // Synchronize session button states
    const startBtn = document.getElementById("startSessionBtn");
    const endBtn = document.getElementById("endSessionBtn");
    const sessionStatus = document.getElementById("sessionStatus");
    if (startBtn && endBtn) {
        startBtn.disabled = data.session_active;
        endBtn.disabled = !data.session_active;
        if (data.session_active) {
            endBtn.classList.add("end-btn-active");
            sessionStatus.innerText = "⏱ Session in progress...";
            sessionStatus.style.color = "#00ff88";
        } else {
            endBtn.classList.remove("end-btn-active");
            if (sessionStatus.innerText === "⏱ Session in progress...") {
                sessionStatus.innerText = "No active session";
                sessionStatus.style.color = "#c7d0da";
            }
        }
    }

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
    if (attentionChart && emotionChart) {
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
}

// CALIBRATION WIZARD
let calibInterval = null;
let lastRawYaw = 1.0;
let lastRawPitch = 1.5;
let lastRawEar = 0.25;

let calibYawCenter = 1.0;
let calibPitchCenter = 1.5;
let calibEarClosed = 0.11;

let capturedYawSamples = [];
let capturedPitchSamples = [];
let capturedEarSamples = [];

function openCalibration() {
    // Open modal
    const modal = document.getElementById("calibrationModal");
    if (modal) modal.style.display = "block";
    
    // Reset steps
    document.getElementById("calibStep1").style.display = "block";
    document.getElementById("calibStep2").style.display = "none";
    document.getElementById("calibStep3").style.display = "none";
    
    // Reset buttons in modal
    const btn1 = document.querySelector("#calibStep1 button");
    if (btn1) {
        btn1.disabled = false;
        btn1.innerText = "🎯 Capture Baseline Center";
    }
    const btn2 = document.querySelector("#calibStep2 button");
    if (btn2) {
        btn2.disabled = false;
        btn2.innerText = "👁️ Capture Blink / Sleep Threshold";
    }
    const btn3 = document.querySelector("#calibStep3 button");
    if (btn3) {
        btn3.disabled = false;
        btn3.innerText = "💾 Save & Activate Calibration";
    }
    
    // Ensure camera is unpaused for preview
    fetch("/status").then(res => res.json()).then(data => {
        if (data.paused) {
            fetch("/toggle_camera", { method: "POST" });
        }
    });
    
    startCalibTelemetry();
}

function closeCalibration() {
    const modal = document.getElementById("calibrationModal");
    if (modal) modal.style.display = "none";
    
    if (calibInterval) {
        clearInterval(calibInterval);
        calibInterval = null;
    }
    
    // Re-pause camera if session is not active
    if (!sessionActive) {
        fetch("/status").then(res => res.json()).then(data => {
            if (!data.paused) {
                fetch("/toggle_camera", { method: "POST" });
            }
        });
    }
}

function startCalibTelemetry() {
    if (calibInterval) clearInterval(calibInterval);
    
    calibInterval = setInterval(async () => {
        try {
            const res = await fetch("/status");
            const data = await res.json();
            
            const yawEl = document.getElementById("calibYawVal");
            const pitchEl = document.getElementById("calibPitchVal");
            const earEl = document.getElementById("calibEarVal");
            
            if (yawEl) yawEl.innerText = data.raw_yaw.toFixed(2);
            if (pitchEl) pitchEl.innerText = data.raw_pitch.toFixed(2);
            if (earEl) earEl.innerText = data.raw_ear.toFixed(2);
            
            lastRawYaw = data.raw_yaw;
            lastRawPitch = data.raw_pitch;
            lastRawEar = data.raw_ear;
        } catch (e) {
            console.error("Calibration telemetry fetch failed:", e);
        }
    }, 200);
}

function captureCenterStep() {
    const btn = document.querySelector("#calibStep1 button");
    if (btn) {
        btn.disabled = true;
        btn.innerText = "⏳ Capturing (Keep Still)...";
    }
    
    capturedYawSamples = [];
    capturedPitchSamples = [];
    
    let count = 0;
    const interval = setInterval(() => {
        capturedYawSamples.push(lastRawYaw);
        capturedPitchSamples.push(lastRawPitch);
        count++;
        if (count >= 5) {
            clearInterval(interval);
            
            calibYawCenter = capturedYawSamples.reduce((a, b) => a + b, 0) / capturedYawSamples.length;
            calibPitchCenter = capturedPitchSamples.reduce((a, b) => a + b, 0) / capturedPitchSamples.length;
            
            document.getElementById("calibStep1").style.display = "none";
            document.getElementById("calibStep2").style.display = "block";
        }
    }, 200);
}

function captureBlinkStep() {
    const btn = document.querySelector("#calibStep2 button");
    if (btn) {
        btn.disabled = true;
        btn.innerText = "⏳ Capturing Blink...";
    }
    
    capturedEarSamples = [];
    
    let count = 0;
    const interval = setInterval(() => {
        capturedEarSamples.push(lastRawEar);
        count++;
        if (count >= 5) {
            clearInterval(interval);
            
            calibEarClosed = capturedEarSamples.reduce((a, b) => a + b, 0) / capturedEarSamples.length;
            
            document.getElementById("summaryYaw").innerText = calibYawCenter.toFixed(2);
            document.getElementById("summaryPitch").innerText = calibPitchCenter.toFixed(2);
            document.getElementById("summaryEar").innerText = calibEarClosed.toFixed(2);
            
            document.getElementById("calibStep2").style.display = "none";
            document.getElementById("calibStep3").style.display = "block";
        }
    }, 200);
}

async function saveCalibration() {
    const btn = document.querySelector("#calibStep3 button");
    if (btn) {
        btn.disabled = true;
        btn.innerText = "💾 Saving Calibration...";
    }
    
    try {
        const res = await fetch("/calibrate", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                yaw_center: calibYawCenter,
                pitch_center: calibPitchCenter,
                ear_closed: calibEarClosed
            })
        });
        
        const data = await res.json();
        if (data.ok) {
            closeCalibration();
            alert("🟢 Calibration saved successfully! Custom limits are now active.");
        } else {
            throw new Error("API responded with failure");
        }
    } catch (e) {
        console.error("Save calibration failed:", e);
        if (btn) {
            btn.disabled = false;
            btn.innerText = "❌ Error. Try Again";
        }
    }
}

// EXPORT REPORT FUNCTION
function downloadReport() {
    const focusTime = document.getElementById("focusTime").innerText;
    const awayTime = document.getElementById("awayTime").innerText;
    const attentionScore = document.getElementById("attention").innerText;
    const emotionText = document.getElementById("emotion").innerText;
    
    const reportText = currentSessionReportText || "No report text available.";

    // Clean report text from markdown characters for PDF presentation
    const cleanReport = reportText
        .replace(/###/g, '')
        .replace(/##/g, '')
        .replace(/#/g, '')
        .replace(/\*\*/g, '')
        .replace(/\*/g, '');

    const docContent = `==================================================
🎓 STUDENT FOCUS ANALYSIS REPORT
==================================================

📊 METRICS SUMMARY
--------------------------------------------------
* Focus Duration: ${focusTime}s
* Away Duration: ${awayTime}s
* Average Attention Score: ${attentionScore}%
* Dominant Emotional Tone: ${emotionText}

📝 AI ANALYSIS & RECOMMENDATIONS
--------------------------------------------------
${cleanReport}
`;

    // Check if jsPDF library is available (loaded via CDN)
    if (typeof window.jspdf !== "undefined") {
        const { jsPDF } = window.jspdf;
        const doc = new jsPDF();
        
        // Header card
        doc.setFillColor(22, 27, 34); // Slate background
        doc.rect(0, 0, 210, 40, "F");
        
        doc.setFont("helvetica", "bold");
        doc.setFontSize(22);
        doc.setTextColor(0, 255, 136); // Brand Green
        doc.text("🎓 FOCUS MONITOR PRO REPORT", 20, 26);
        
        // Metrics section
        doc.setTextColor(50, 50, 50);
        doc.setFontSize(14);
        doc.setFont("helvetica", "bold");
        doc.text("📊 Metrics Summary", 20, 55);
        
        doc.setFont("helvetica", "normal");
        doc.setFontSize(11);
        doc.text(`• Focus Time: ${focusTime} seconds`, 25, 65);
        doc.text(`• Distracted (Away) Time: ${awayTime} seconds`, 25, 72);
        doc.text(`• Average Attention Score: ${attentionScore}%`, 25, 79);
        doc.text(`• Dominant Emotion: ${emotionText}`, 25, 86);
        
        // AI Feedback section
        doc.setFont("helvetica", "bold");
        doc.setFontSize(14);
        doc.text("📝 AI Analysis & Feedback", 20, 100);
        
        doc.setFont("helvetica", "normal");
        doc.setFontSize(10);
        
        // Wrap lines
        const wrappedText = doc.splitTextToSize(cleanReport, 170);
        doc.text(wrappedText, 20, 110);
        
        // Save PDF
        doc.save("Student_Focus_Report.pdf");
    } else {
        // Fallback: Download TXT file
        console.warn("jsPDF not loaded. Downloading report as TXT file.");
        const blob = new Blob([docContent], { type: "text/plain;charset=utf-8" });
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = "Student_Focus_Report.txt";
        link.click();
    }
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