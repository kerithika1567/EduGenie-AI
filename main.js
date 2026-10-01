/**
 * EduGenie Frontend Application Script
 */

let currentQuizData = null;

document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    checkHealthStatus();
    initForms();
});

/* ----------------------------------------------------
 * Tab Switching Logic
 * ---------------------------------------------------- */
function initTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.getAttribute('data-tab');

            tabBtns.forEach(b => b.classList.remove('active'));
            tabPanes.forEach(p => p.classList.remove('active'));

            btn.classList.add('active');
            const activePane = document.getElementById(targetId);
            if (activePane) {
                activePane.classList.add('active');
            }
        });
    });
}

/* ----------------------------------------------------
 * System Health & API Key Status
 * ---------------------------------------------------- */
async function checkHealthStatus() {
    const badge = document.getElementById('statusBadge');
    try {
        const response = await fetch('/health');
        if (!response.ok) throw new Error('Server health check failed');
        const data = await response.json();

        if (data.gemini_configured) {
            badge.textContent = `● Gemini Ready (${data.gemini_model})`;
            badge.className = 'status-badge online';
        } else {
            badge.textContent = `⚠️ API Key Missing (.env)`;
            badge.className = 'status-badge warning';
            showAlert('Gemini API Key is not set. Please add GEMINI_API_KEY to your .env file to enable AI features.', 'warning');
        }
    } catch (err) {
        badge.textContent = '❌ System Offline';
        badge.className = 'status-badge warning';
    }
}

/* ----------------------------------------------------
 * Alert Banner Helpers
 * ---------------------------------------------------- */
function showAlert(message, type = 'error') {
    const banner = document.getElementById('alertBanner');
    const msg = document.getElementById('alertMessage');
    const icon = document.getElementById('alertIcon');

    msg.textContent = message;
    banner.className = `alert-banner ${type}`;
    icon.textContent = type === 'warning' ? '⚠️' : '❌';
    banner.classList.remove('hidden');
}

function hideAlert() {
    document.getElementById('alertBanner').classList.add('hidden');
}

/* ----------------------------------------------------
 * Request Loading & Double-Click Prevention
 * ---------------------------------------------------- */
function setButtonLoading(btn, isLoading) {
    if (!btn) return;
    const textSpan = btn.querySelector('.btn-text');
    const spinner = btn.querySelector('.spinner');

    btn.disabled = isLoading;
    if (isLoading) {
        if (textSpan) textSpan.dataset.origText = textSpan.textContent;
        if (spinner) spinner.classList.remove('hidden');
    } else {
        if (spinner) spinner.classList.add('hidden');
    }
}

/* ----------------------------------------------------
 * Helper for Safe Text Rendering (Prevents HTML Injection)
 * ---------------------------------------------------- */
function renderSafeText(container, text) {
    container.innerHTML = ''; // Clear container
    const lines = text.split('\n');
    lines.forEach(line => {
        const p = document.createElement('p');
        p.textContent = line;
        if (line.trim() === '') {
            p.style.height = '10px';
        }
        container.appendChild(p);
    });
}

/* ----------------------------------------------------
 * Form Submissions
 * ---------------------------------------------------- */
function initForms() {
    // 1. Q&A Form
    const qaForm = document.getElementById('qaForm');
    if (qaForm) {
        qaForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            hideAlert();
            const submitBtn = document.getElementById('qaSubmitBtn');
            const question = document.getElementById('qaQuestion').value.trim();
            const context = document.getElementById('qaContext').value.trim();

            if (!question) return;

            setButtonLoading(submitBtn, true);
            try {
                const res = await fetch('/api/qa', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ question, context: context || null })
                });

                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || 'Q&A request failed');

                const resultCard = document.getElementById('qaResult');
                const answerBody = document.getElementById('qaAnswerBody');
                const modelBadge = document.getElementById('qaModelBadge');

                modelBadge.textContent = data.model_used || 'Gemini API';
                renderSafeText(answerBody, data.answer);
                resultCard.classList.remove('hidden');
            } catch (err) {
                showAlert(err.message, 'error');
            } finally {
                setButtonLoading(submitBtn, false);
            }
        });
    }

    // 2. Concept Explainer Form
    const explainForm = document.getElementById('explainForm');
    if (explainForm) {
        explainForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            hideAlert();
            const submitBtn = document.getElementById('explainSubmitBtn');
            const concept = document.getElementById('explainConcept').value.trim();
            const mode = document.getElementById('explainMode').value;

            if (!concept) return;

            setButtonLoading(submitBtn, true);
            try {
                const res = await fetch('/api/explain', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ concept, mode })
                });

                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || 'Concept explanation failed');

                const resultCard = document.getElementById('explainResult');
                const explainBody = document.getElementById('explainBody');
                const modeBadge = document.getElementById('explainModeBadge');
                const warningBox = document.getElementById('explainWarning');

                modeBadge.textContent = data.mode_used || mode;

                if (data.warning) {
                    warningBox.textContent = `ℹ️ ${data.warning}`;
                    warningBox.classList.remove('hidden');
                } else {
                    warningBox.classList.add('hidden');
                }

                renderSafeText(explainBody, data.explanation);
                resultCard.classList.remove('hidden');
            } catch (err) {
                showAlert(err.message, 'error');
            } finally {
                setButtonLoading(submitBtn, false);
            }
        });
    }

    // 3. Quiz Generator Form
    const quizForm = document.getElementById('quizForm');
    if (quizForm) {
        quizForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            hideAlert();
            const submitBtn = document.getElementById('quizSubmitBtn');
            const topic = document.getElementById('quizTopic').value.trim();

            if (!topic) return;

            setButtonLoading(submitBtn, true);
            try {
                const res = await fetch('/api/quiz', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ topic, num_questions: 3 })
                });

                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || 'Quiz generation failed');

                currentQuizData = data;
                renderQuiz(data);
            } catch (err) {
                showAlert(err.message, 'error');
            } finally {
                setButtonLoading(submitBtn, false);
            }
        });
    }

    // Quiz Grading Button
    const submitAnswersBtn = document.getElementById('submitQuizAnswersBtn');
    if (submitAnswersBtn) {
        submitAnswersBtn.addEventListener('click', gradeQuiz);
    }

    // 4. Text Summarizer Form
    const summarizeForm = document.getElementById('summarizeForm');
    if (summarizeForm) {
        summarizeForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            hideAlert();
            const submitBtn = document.getElementById('summarizeSubmitBtn');
            const text = document.getElementById('summarizeText').value.trim();
            const length = document.getElementById('summarizeLength').value;

            if (!text || text.length < 10) {
                showAlert('Please enter at least 10 characters to summarize.', 'warning');
                return;
            }

            setButtonLoading(submitBtn, true);
            try {
                const res = await fetch('/api/summarize', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text, length })
                });

                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || 'Text summarization failed');

                const resultCard = document.getElementById('summarizeResult');
                const summarizeBody = document.getElementById('summarizeBody');
                const origCount = document.getElementById('origWordCount');
                const summaryCount = document.getElementById('summaryWordCount');

                origCount.textContent = `Original: ${data.original_length} words`;
                summaryCount.textContent = `Summary: ${data.summary_length} words`;

                renderSafeText(summarizeBody, data.summary);
                resultCard.classList.remove('hidden');
            } catch (err) {
                showAlert(err.message, 'error');
            } finally {
                setButtonLoading(submitBtn, false);
            }
        });
    }

    // 5. Learning Path Form
    const pathForm = document.getElementById('pathForm');
    if (pathForm) {
        pathForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            hideAlert();
            const submitBtn = document.getElementById('pathSubmitBtn');
            const topic = document.getElementById('pathTopic').value.trim();
            const level = document.getElementById('pathLevel').value;
            const goal = document.getElementById('pathGoal').value.trim();

            if (!topic) return;

            setButtonLoading(submitBtn, true);
            try {
                const res = await fetch('/api/learning-path', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ topic, current_level: level, goal: goal || null })
                });

                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || 'Learning path generation failed');

                renderLearningPath(data);
            } catch (err) {
                showAlert(err.message, 'error');
            } finally {
                setButtonLoading(submitBtn, false);
            }
        });
    }
}

/* ----------------------------------------------------
 * Interactive Quiz Rendering & Grading
 * ---------------------------------------------------- */
function renderQuiz(quizData) {
    const resultCard = document.getElementById('quizResult');
    const topicTitle = document.getElementById('quizTopicTitle');
    const container = document.getElementById('quizQuestionsContainer');
    const scoreCard = document.getElementById('quizScoreCard');

    topicTitle.textContent = quizData.topic;
    scoreCard.classList.add('hidden');
    container.innerHTML = '';

    quizData.questions.forEach((q, idx) => {
        const qCard = document.createElement('div');
        qCard.className = 'quiz-card';

        const qTitle = document.createElement('div');
        qTitle.className = 'quiz-question-title';
        qTitle.textContent = `Q${idx + 1}. ${q.question}`;
        qCard.appendChild(qTitle);

        const optionsDiv = document.createElement('div');
        optionsDiv.className = 'quiz-options';

        q.options.forEach((opt, optIdx) => {
            const label = document.createElement('label');
            label.className = 'quiz-option-label';
            label.id = `q${q.id}_opt${optIdx}`;

            const radio = document.createElement('input');
            radio.type = 'radio';
            radio.name = `quiz_q_${q.id}`;
            radio.value = opt;

            const optText = document.createTextNode(` ${opt}`);

            label.appendChild(radio);
            label.appendChild(optText);
            optionsDiv.appendChild(label);
        });

        qCard.appendChild(optionsDiv);

        const explBox = document.createElement('div');
        explBox.className = 'quiz-explanation hidden';
        explBox.id = `q${q.id}_expl`;
        explBox.textContent = `💡 Explanation: ${q.explanation}`;
        qCard.appendChild(explBox);

        container.appendChild(qCard);
    });

    resultCard.classList.remove('hidden');
}

function gradeQuiz() {
    if (!currentQuizData || !currentQuizData.questions) return;

    let score = 0;
    const total = currentQuizData.questions.length;

    currentQuizData.questions.forEach(q => {
        const radios = document.querySelectorAll(`input[name="quiz_q_${q.id}"]`);
        let selectedValue = null;

        radios.forEach((r, idx) => {
            const label = document.getElementById(`q${q.id}_opt${idx}`);
            if (label) {
                label.classList.remove('correct', 'incorrect');
            }

            if (r.checked) {
                selectedValue = r.value;
            }

            // Highlight correct answer in green
            if (r.value === q.correct_answer && label) {
                label.classList.add('correct');
            }
        });

        // If user selected an incorrect option, highlight in red
        if (selectedValue) {
            if (selectedValue === q.correct_answer) {
                score++;
            } else {
                radios.forEach((r, idx) => {
                    if (r.checked) {
                        const label = document.getElementById(`q${q.id}_opt${idx}`);
                        if (label) label.classList.add('incorrect');
                    }
                });
            }
        }

        // Reveal explanation
        const explBox = document.getElementById(`q${q.id}_expl`);
        if (explBox) explBox.classList.remove('hidden');
    });

    // Show score card
    const scoreCard = document.getElementById('quizScoreCard');
    const scoreNumber = document.getElementById('scoreNumber');
    const scoreFeedback = document.getElementById('scoreFeedback');

    scoreNumber.textContent = `${score} / ${total}`;
    if (score === total) {
        scoreFeedback.textContent = '🌟 Outstanding! Perfect Score!';
    } else if (score >= 2) {
        scoreFeedback.textContent = '👍 Great job! You have a good grasp of this topic.';
    } else {
        scoreFeedback.textContent = '📚 Keep practicing! Review the explanations above to learn more.';
    }

    scoreCard.classList.remove('hidden');
}

/* ----------------------------------------------------
 * Learning Path Timeline Rendering
 * ---------------------------------------------------- */
function renderLearningPath(pathData) {
    const resultCard = document.getElementById('pathResult');
    const topicTitle = document.getElementById('pathTopicTitle');
    const levelBadge = document.getElementById('pathLevelBadge');
    const timeline = document.getElementById('pathTimeline');

    topicTitle.textContent = pathData.topic;
    levelBadge.textContent = `Current Level: ${pathData.current_level.toUpperCase()}`;
    timeline.innerHTML = '';

    pathData.modules.forEach((mod) => {
        const modCard = document.createElement('div');
        modCard.className = 'timeline-module';

        const header = document.createElement('div');
        header.className = 'module-header';

        const title = document.createElement('div');
        title.className = 'module-title';
        title.textContent = mod.title;

        const levelTag = document.createElement('div');
        levelTag.className = 'module-level-tag';
        levelTag.textContent = mod.level;

        header.appendChild(title);
        header.appendChild(levelTag);
        modCard.appendChild(header);

        const summary = document.createElement('div');
        summary.className = 'module-summary';
        summary.textContent = mod.summary;
        modCard.appendChild(summary);

        const listsGrid = document.createElement('div');
        listsGrid.className = 'module-lists';

        // Key Takeaways
        const takeawaysBlock = document.createElement('div');
        takeawaysBlock.className = 'module-list-block';
        const takeawaysH5 = document.createElement('h5');
        takeawaysH5.textContent = 'Key Concepts';
        takeawaysBlock.appendChild(takeawaysH5);
        const takeawaysUl = document.createElement('ul');
        (mod.key_takeaways || []).forEach(t => {
            const li = document.createElement('li');
            li.textContent = t;
            takeawaysUl.appendChild(li);
        });
        takeawaysBlock.appendChild(takeawaysUl);
        listsGrid.appendChild(takeawaysBlock);

        // Action Steps
        const actionsBlock = document.createElement('div');
        actionsBlock.className = 'module-list-block';
        const actionsH5 = document.createElement('h5');
        actionsH5.textContent = 'Action Steps';
        actionsBlock.appendChild(actionsH5);
        const actionsUl = document.createElement('ul');
        (mod.action_steps || []).forEach(a => {
            const li = document.createElement('li');
            li.textContent = a;
            actionsUl.appendChild(li);
        });
        actionsBlock.appendChild(actionsUl);
        listsGrid.appendChild(actionsBlock);

        modCard.appendChild(listsGrid);
        timeline.appendChild(modCard);
    });

    resultCard.classList.remove('hidden');
}
