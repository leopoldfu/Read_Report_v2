console.log("LDA App Loaded");

document.addEventListener('DOMContentLoaded', () => {
    const btn = document.getElementById('predictBtn');
    const input = document.getElementById('textInput');
    const mediaSelect = document.getElementById('mediaSelect');
    const results = document.getElementById('results');

    btn.addEventListener('click', async () => {
        const text = input.value;
        const media = mediaSelect.value;

        if (!text) return;

        btn.disabled = true;
        btn.innerText = "Analyzing...";
        results.innerHTML = "";

        try {
            const response = await fetch('/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ text, media })
            });

            const data = await response.json();

            if (data.error) {
                results.innerHTML = `<p style="color: red;">Error: ${data.error}</p>`;
            } else {
                let html = '';
                const stopwordPanel = document.getElementById('stopwordPanel');
                if (data.topics && data.topics.length > 0) {
                    stopwordPanel.style.display = 'block';
                }

                data.topics.forEach(topic => {
                    html += `<div class="topic-box">
                        <strong>Topic ${topic.topic_id}</strong> (Score: ${(topic.score * 100).toFixed(1)}%)<br>`;
                    topic.words.forEach((word, index) => {
                        html += `<span class="topic-word" ondblclick="toggleStopword(this, '${word}')" title="Double-click to ban">${word}</span>`;
                        if (index < topic.words.length - 1) {
                            html += "、";
                        }
                    });
                    html += `</div>`;
                });
                results.innerHTML = html;
            }
        } catch (e) {
            console.error(e);
            results.innerHTML = "<p style='color: red;'>An error occurred.</p>";
        } finally {
            btn.disabled = false;
            btn.innerText = "Analyze Topics";
        }
    });

    // --- Model Status Checker ---
    const modelInfo = document.getElementById('modelInfo');

    async function checkModelStatus(media) {
        modelInfo.innerText = "Checking model status...";
        modelInfo.style.color = "#888";

        try {
            const response = await fetch(`/model_status/${media}`);
            const data = await response.json();

            if (data.exists) {
                // Formatting timestamp 20241222_1500xx to readable if possible, or just show it
                const v = data.version;
                // Simple formatting: 20241222_150000 -> 2024-12-22 15:00:00
                // Or just display as is.
                modelInfo.innerText = `✅ Active Model Found: ${v}`;
                modelInfo.style.color = "green";
            } else {
                modelInfo.innerText = `⚠️ No model found for '${media}' (Training required)`;
                modelInfo.style.color = "orange";
            }
        } catch (e) {
            console.error(e);
            modelInfo.innerText = "Error checking status";
            modelInfo.style.color = "red";
        }
    }

    // Initial check
    checkModelStatus(mediaSelect.value);

    // On change check
    mediaSelect.addEventListener('change', () => {
        checkModelStatus(mediaSelect.value);
    });

    // Training Logic
    const trainBtn = document.getElementById('trainBtn');
    const trainStatus = document.getElementById('trainStatus');

    trainBtn.addEventListener('click', async () => {
        const media = mediaSelect.value;
        if (!confirm(`Are you sure you want to trigger training for ${media}?`)) return;

        await runTraining(media, false);
    });

    async function runTraining(media, force) {
        trainBtn.disabled = true;
        trainBtn.innerText = force ? "Force Retraining..." : "Training...";
        trainStatus.innerText = force ? "Force retraining started..." : "Checking model status / Training...";
        trainStatus.style.color = "#666";

        try {
            const response = await fetch('/train', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ media, force })
            });
            const data = await response.json();

            if (response.ok && data.success) {
                if (data.skipped) {
                    trainStatus.innerText = "Skipped: " + data.message;
                    trainStatus.style.color = "orange";

                    // Ask user if they want to force
                    if (confirm("Model already exists. Do you want to FORCE a retrain? This will overwrite the existing model.")) {
                        await runTraining(media, true);
                        return; // Exit this execution, the recursive call handles the rest
                    }
                } else {
                    trainStatus.innerText = "Success: " + data.message;
                    trainStatus.style.color = "green";

                    // Log detailed scores to dev console
                    console.log("--- Training Coherence Scores ---");
                    if (data.scores) {
                        data.scores.forEach(item => {
                            console.log(`K=${item.k} → Coherence=${item.score.toFixed(4)}`);
                        });
                    }
                    console.log("---------------------------------");
                    alert("Training complete!");
                    // Refresh status
                    checkModelStatus(media);
                }
            } else {
                trainStatus.innerText = "Error: " + (data.message || "Unknown error");
                trainStatus.style.color = "red";
            }
        } catch (e) {
            console.error(e);
            trainStatus.innerText = "Network Error";
            trainStatus.style.color = "red";
        } finally {
            // Only re-enable if we are not recursively calling force train
            // actually, the recursive awaited call will finish before we get here, so we might re-enable twice, which is fine.
            trainBtn.disabled = false;
            trainBtn.innerText = "Train Model for Selected Media";
        }
    }

    // --- Stopword Refinement Logic ---
    const pendingWords = new Set();
    const updateBtn = document.getElementById('updateStopwordsBtn');
    const pendingDiv = document.getElementById('pendingStopwords');

    // Make global so onclick can see it
    window.toggleStopword = (element, word) => {
        if (pendingWords.has(word)) {
            pendingWords.delete(word);
            element.classList.remove('selected');
        } else {
            pendingWords.add(word);
            element.classList.add('selected');
        }
        updateUI();
    };

    function updateUI() {
        if (pendingWords.size > 0) {
            pendingDiv.innerText = "To remove: " + Array.from(pendingWords).join(", ");
            updateBtn.style.display = 'inline-block';
        } else {
            pendingDiv.innerText = "";
            updateBtn.style.display = 'none';
        }
    }

    if (updateBtn) {
        updateBtn.addEventListener('click', async () => {
            const media = mediaSelect.value;
            const words = Array.from(pendingWords);

            if (!confirm(`Ban ${words.length} words and retrain model?`)) return;

            updateBtn.disabled = true;
            updateBtn.innerText = "Updating & Retraining...";

            try {
                // 1. Send stopwords
                await fetch('/stopwords', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ media, words })
                });

                // 2. Trigger Retrain
                // Reuse the existing train logic via fetch
                const trainResponse = await fetch('/train', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ media, force: true })
                });
                const trainData = await trainResponse.json();

                if (trainResponse.ok && trainData.success) {
                    alert("Success! Model retrained without banned words.");
                    // Clear UI
                    pendingWords.clear();
                    results.innerHTML = ""; // Clear old results
                    updateUI();
                    document.getElementById('trainStatus').innerText = "Retraining complete.";
                } else {
                    alert("Error during retraining: " + trainData.message);
                }

            } catch (e) {
                console.error(e);
                alert("Network error.");
            } finally {
                updateBtn.disabled = false;
                updateBtn.innerText = "Ban Words & Retrain";
            }
        });
    }
});

