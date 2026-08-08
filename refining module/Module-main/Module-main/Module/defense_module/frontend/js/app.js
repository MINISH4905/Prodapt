/**
 * VentureX-Ray Defense Module - Frontend Application Controller (app.js)
 * ----------------------------------------------------------------------
 * Multi-stage interactive dashboard for the AI Refinement & Founder Defense Engine.
 * 
 * Application Architecture & State Machine:
 * - Stage 1 (Selection & Vulnerabilities): Startup catalog grid, original pitch pane, risk badges, and attacker findings list.
 * - Stage 2 (AI Refinement Comparison): Side-by-side comparison of original vs AI-refined fields with change rationale.
 * - Stage 3 (Founder Concern & Clarity Test): Form for founder input/doubts and AI-generated probing defensive questions.
 * - Stage 4 (Founder Evaluation Report): Score gauge, multi-metric bar charts, qualitative analysis, and weak area remedies.
 * 
 * Key Features:
 * - Dynamic stage transitions with visual step indicators and smooth scroll.
 * - Client-side API Key session persistence (`X-Gemini-API-Key` header injection).
 * - Button loading states with CSS animated spinners during backend API requests.
 */

document.addEventListener("DOMContentLoaded", () => {
    // ==========================================
    // GLOBAL STATE VARIABLES
    // ==========================================
    let selectedStartupKey = null;   // Active template startup identifier (e.g., 'ecopacker')
    let selectedStartupData = null;  // Loaded original profile and vulnerability map
    let refinedStartupData = null;   // Output from Module 4 POST /api/refine
    let clarityQuestions = [];       // Output from Module 5 POST /api/generate-questions

    // ==========================================
    // DOM ELEMENT REFERENCES
    // ==========================================
    const apiKeyInput = document.getElementById("apiKey");
    const saveKeyBtn = document.getElementById("saveKeyBtn");
    
    const startupSelectGrid = document.getElementById("startup-select-grid");
    const startupDetailsPane = document.getElementById("startup-details-pane");
    
    // Original Pitch Element Selectors
    const origName = document.getElementById("orig-name");
    const origProblem = document.getElementById("orig-problem");
    const origSolution = document.getElementById("orig-solution");
    const origCustomer = document.getElementById("orig-customer");
    const origBusiness = document.getElementById("orig-business");
    const origTech = document.getElementById("orig-tech");
    
    // Vulnerability & Risk Map Element Selectors
    const riskScoreBadge = document.getElementById("risk-score-badge");
    const vulnScoreBarFill = document.getElementById("vuln-score-bar-fill");
    const vulnList = document.getElementById("vuln-list");
    
    // Action Button Selectors
    const refineBtn = document.getElementById("refineBtn");
    const generateQuestionsBtn = document.getElementById("generateQuestionsBtn");
    const evaluateClarityBtn = document.getElementById("evaluateClarityBtn");
    const restartBtn = document.getElementById("restartBtn");
    
    // Founder Input Elements
    const founderConcernsTextarea = document.getElementById("founderConcerns");
    
    // Step Stage DOM Sections (Stages 1-4)
    const stages = [
        document.getElementById("stage-1"),
        document.getElementById("stage-2"),
        document.getElementById("stage-3"),
        document.getElementById("stage-4")
    ];
    
    // Step Navigation Indicators
    const indicators = [
        document.getElementById("step-indicator-1"),
        document.getElementById("step-indicator-2"),
        document.getElementById("step-indicator-3"),
        document.getElementById("step-indicator-4")
    ];
    
    // Step Connecting Lines
    const lines = [
        document.getElementById("step-line-1"),
        document.getElementById("step-line-2"),
        document.getElementById("step-line-3")
    ];

    // ==========================================
    // SESSION MANAGEMENT & API HEADERS
    // ==========================================

    // Restore saved API Key from sessionStorage on initialization
    if (sessionStorage.getItem("gemini_api_key")) {
        apiKeyInput.value = sessionStorage.getItem("gemini_api_key");
    }

    // Save or clear API Key in sessionStorage
    saveKeyBtn.addEventListener("click", () => {
        const key = apiKeyInput.value.trim();
        if (key) {
            sessionStorage.setItem("gemini_api_key", key);
            alert("API Key saved to browser session storage.");
        } else {
            sessionStorage.removeItem("gemini_api_key");
            alert("API Key removed. Backend will use server .env file.");
        }
    });

    /**
     * Constructs request headers.
     * Automatically attaches `X-Gemini-API-Key` if custom key is saved in sessionStorage.
     */
    function getHeaders() {
        const headers = {
            "Content-Type": "application/json"
        };
        const savedKey = sessionStorage.getItem("gemini_api_key");
        if (savedKey) {
            headers["X-Gemini-API-Key"] = savedKey;
        }
        return headers;
    }

    // ==========================================
    // STAGE 1: LOAD & SELECT STARTUP TEMPLATES
    // ==========================================

    /**
     * Fetches startup templates from GET /api/startups and renders cards in grid.
     */
    async function loadStartups() {
        try {
            const res = await fetch("/api/startups");
            if (!res.ok) throw new Error("Failed to fetch startups from server.");
            const startups = await res.json();
            
            startupSelectGrid.innerHTML = "";
            startups.forEach(item => {
                const card = document.createElement("div");
                card.className = "glass-card startup-select-card";
                card.dataset.key = item.key;
                
                // Determine risk level styling based on score
                const score = item.vulnerabilities.overall_risk_score;
                let riskClass = "dot-low";
                let riskText = "Low Risk";
                if (score >= 80) {
                    riskClass = "dot-high";
                    riskText = "High Risk";
                } else if (score >= 60) {
                    riskClass = "dot-medium";
                    riskText = "Medium Risk";
                }

                card.innerHTML = `
                    <h3>${item.name}</h3>
                    <p>${item.profile.problem}</p>
                    <div class="card-footer">
                        <div class="risk-level-indicator">
                            <span class="dot ${riskClass}"></span>
                            <span>${riskText} (${score}/100)</span>
                        </div>
                        <span class="badge badge-original">Select</span>
                    </div>
                `;
                
                card.addEventListener("click", () => selectStartup(item, card));
                startupSelectGrid.appendChild(card);
            });
        } catch (error) {
            startupSelectGrid.innerHTML = `<div class="error-msg" style="color:var(--danger-color)">Error: ${error.message}</div>`;
        }
    }

    /**
     * Handles selection of a startup card, populating the original pitch and risk map pane.
     */
    function selectStartup(item, cardEl) {
        // Deselect previous cards
        document.querySelectorAll(".startup-select-card").forEach(c => c.classList.remove("selected"));
        
        // Highlight active card
        cardEl.classList.add("selected");
        selectedStartupKey = item.key;
        selectedStartupData = item;
        
        // Populate Original Pitch section
        origName.textContent = item.profile.name;
        origProblem.textContent = item.profile.problem;
        origSolution.textContent = item.profile.solution;
        origCustomer.textContent = item.profile.target_customer;
        origBusiness.textContent = item.profile.business_model;
        origTech.textContent = item.profile.technology;
        
        // Populate Vulnerability Map header & risk score badge
        riskScoreBadge.textContent = item.vulnerabilities.overall_risk_score;
        const score = item.vulnerabilities.overall_risk_score;
        riskScoreBadge.style.backgroundColor = score >= 80 ? "var(--danger-color)" : (score >= 60 ? "var(--warning-color)" : "var(--success-color)");
        
        // Trigger smooth fill animation on score progress bar
        setTimeout(() => {
            vulnScoreBarFill.style.width = `${score}%`;
        }, 100);

        // Render detailed vulnerability findings
        vulnList.innerHTML = "";
        item.vulnerabilities.findings.forEach(finding => {
            const vulnCard = document.createElement("div");
            vulnCard.className = `vuln-card vuln-${finding.category.toLowerCase()}`;
            
            const badgeClass = finding.severity.toLowerCase() === "high" ? "badge-high" : (finding.severity.toLowerCase() === "medium" ? "badge-medium" : "badge-low");
            
            vulnCard.innerHTML = `
                <div class="vuln-card-header">
                    <span class="vuln-cat" style="color:${getCategoryColor(finding.category)}">${finding.category}</span>
                    <span class="badge ${badgeClass}">${finding.severity} Severity</span>
                </div>
                <p><strong>Weakness:</strong> ${finding.reasoning}</p>
                <div class="vuln-question">"Investor Test: ${finding.attack_question}"</div>
                <p style="margin-top:0.5rem; font-size:0.8rem; color:var(--success-color)"><strong>Suggested Fix:</strong> ${finding.suggested_mitigation}</p>
            `;
            vulnList.appendChild(vulnCard);
        });

        // Display detail pane and scroll into view
        startupDetailsPane.style.display = "block";
        startupDetailsPane.scrollIntoView({ behavior: "smooth" });
    }

    /** Helper function mapping category names to signature theme colors. */
    function getCategoryColor(cat) {
        if (cat.toLowerCase() === "market") return "#3b82f6";
        if (cat.toLowerCase() === "business") return "#10b981";
        return "#f59e0b";
    }

    // ==========================================
    // UI NAVIGATION & BUTTON LOADING HELPERS
    // ==========================================

    /**
     * Transitions active stage view and updates header step progress indicators.
     */
    function transitionToStage(stageNum) {
        stages.forEach(s => s.classList.remove("active"));
        indicators.forEach(i => {
            i.classList.remove("active");
            i.classList.remove("completed");
        });
        lines.forEach(l => l.classList.remove("active"));

        stages[stageNum - 1].classList.add("active");
        
        for (let i = 1; i <= stageNum; i++) {
            indicators[i - 1].classList.add("active");
            if (i < stageNum) {
                indicators[i - 1].classList.add("completed");
                if (lines[i - 1]) lines[i - 1].classList.add("active");
            }
        }
        window.scrollTo({ top: 0, behavior: "smooth" });
    }

    /** Toggles button disabled state and displays loading spinner during API calls. */
    function setButtonLoading(btn, isLoading) {
        const textSpan = btn.querySelector(".btn-text");
        const spinner = btn.querySelector(".btn-spinner");
        if (isLoading) {
            btn.disabled = true;
            textSpan.style.opacity = "0.2";
            spinner.style.display = "block";
        } else {
            btn.disabled = false;
            textSpan.style.opacity = "1";
            spinner.style.display = "none";
        }
    }

    // ==========================================
    // STAGE 2: EXECUTE REFINEMENT (MODULE 4)
    // ==========================================

    refineBtn.addEventListener("click", async () => {
        if (!selectedStartupKey) return;
        setButtonLoading(refineBtn, true);

        try {
            const res = await fetch("/api/refine", {
                method: "POST",
                headers: getHeaders(),
                body: JSON.stringify({ startup_key: selectedStartupKey })
            });

            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.detail || "Refinement call failed.");
            }

            refinedStartupData = await res.json();
            renderRefinementResults();
            transitionToStage(2);
        } catch (error) {
            alert(`Refinement Error: ${error.message}`);
        } finally {
            setButtonLoading(refineBtn, false);
        }
    });

    /**
     * Renders side-by-side comparison of original pitch vs AI-refined pitch in Stage 2.
     */
    function renderRefinementResults() {
        document.getElementById("refinement-rationale").textContent = refinedStartupData.change_rationale;
        
        const compList = document.getElementById("comparison-list");
        compList.innerHTML = "";
        
        const fields = ["problem", "solution", "target_customer", "business_model", "technology"];
        
        fields.forEach(field => {
            const origVal = selectedStartupData.profile[field];
            const refinedVal = refinedStartupData[field];
            
            // Extract AI change reasoning logs for this specific field
            const changesForField = refinedStartupData.changes.filter(c => c.field.toLowerCase() === field.toLowerCase());
            const fieldTitle = field.replace("_", " ");
            
            const item = document.createElement("div");
            item.className = "comparison-item";
            
            let explanationHtml = "";
            if (changesForField.length > 0) {
                explanationHtml = `
                    <div class="change-reasoning-val mt-2">
                        <strong>AI Refinement Rationale:</strong> ${changesForField.map(c => c.explanation).join("<br/>")}
                    </div>
                `;
            }

            item.innerHTML = `
                <h4>${fieldTitle}</h4>
                <div class="comparison-row">
                    <div class="comparison-side">
                        <div class="side-header side-header-original">Original Pitch</div>
                        <div>${origVal}</div>
                    </div>
                    <div class="comparison-side" style="border-color: rgba(168, 85, 247, 0.25); background: rgba(168, 85, 247, 0.02)">
                        <div class="side-header side-header-refined">Refined Version</div>
                        <div>${refinedVal}</div>
                    </div>
                </div>
                ${explanationHtml}
            `;
            compList.appendChild(item);
        });
    }

    // ==========================================
    // STAGE 3: CONCERNS & CLARITY QUESTIONS (MODULE 5)
    // ==========================================

    generateQuestionsBtn.addEventListener("click", async () => {
        const concerns = founderConcernsTextarea.value.trim();
        if (!concerns) {
            alert("Please state at least one concern, doubt, or operational constraint to proceed.");
            return;
        }
        
        setButtonLoading(generateQuestionsBtn, true);
        
        try {
            const res = await fetch("/api/generate-questions", {
                method: "POST",
                headers: getHeaders(),
                body: JSON.stringify({
                    refined: refinedStartupData,
                    vulnerabilities: selectedStartupData.vulnerabilities,
                    concerns: concerns
                })
            });

            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.detail || "Generating questions failed.");
            }

            clarityQuestions = await res.json();
            renderClarityQuestions();
            transitionToStage(3);
        } catch (error) {
            alert(`Question Generation Error: ${error.message}`);
        } finally {
            setButtonLoading(generateQuestionsBtn, false);
        }
    });

    /**
     * Renders generated clarity questions and textareas for founder defensive responses in Stage 3.
     */
    function renderClarityQuestions() {
        const qList = document.getElementById("questions-list");
        qList.innerHTML = "";
        
        clarityQuestions.forEach((q, idx) => {
            const qCard = document.createElement("div");
            qCard.className = "question-card";
            qCard.dataset.qid = q.id;
            qCard.dataset.qtext = q.question;
            
            qCard.innerHTML = `
                <div class="question-card-header">
                    <div class="q-badge">${idx + 1}</div>
                    <div>
                        <h4>${q.question}</h4>
                        <div class="q-context"><strong>Prompt context:</strong> ${q.context}</div>
                    </div>
                </div>
                <div class="form-group">
                    <label>Provide your defensive answer:</label>
                    <textarea class="founder-response-input" rows="4" placeholder="Type your detailed, structured answer here..."></textarea>
                </div>
            `;
            qList.appendChild(qCard);
        });
    }

    // ==========================================
    // STAGE 4: EVALUATE CLARITY & REPORT (MODULE 6)
    // ==========================================

    evaluateClarityBtn.addEventListener("click", async () => {
        // Collect founder responses from input textareas
        const questionCards = document.querySelectorAll(".question-card");
        const responses = [];
        let unanswered = false;
        
        questionCards.forEach(card => {
            const qid = card.dataset.qid;
            const qtext = card.dataset.qtext;
            const answer = card.querySelector(".founder-response-input").value.trim();
            
            if (!answer) {
                unanswered = true;
            }
            
            responses.push({
                question_id: qid,
                question_text: qtext,
                answer: answer
            });
        });

        if (unanswered) {
            alert("Please answer all questions before submitting for evaluation.");
            return;
        }

        setButtonLoading(evaluateClarityBtn, true);

        try {
            const res = await fetch("/api/evaluate-clarity", {
                method: "POST",
                headers: getHeaders(),
                body: JSON.stringify({
                    refined: refinedStartupData,
                    responses: responses
                })
            });

            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.detail || "Clarity evaluation failed.");
            }

            const evaluation = await res.json();
            renderClarityEvaluation(evaluation);
            transitionToStage(4);
        } catch (error) {
            alert(`Clarity Evaluation Error: ${error.message}`);
        } finally {
            setButtonLoading(evaluateClarityBtn, false);
        }
    });

    /**
     * Renders final evaluation report in Stage 4 (Score Circle, metric bars, weak areas).
     */
    function renderClarityEvaluation(report) {
        // Animate circular progress ring based on overall clarity score
        const score = report.clarity_score;
        document.getElementById("final-clarity-score").textContent = score;
        
        const circleOuter = document.querySelector(".score-circle-outer");
        circleOuter.style.background = `conic-gradient(var(--primary-color) 0%, var(--accent-color) ${score}%, rgba(255,255,255,0.05) ${score}%, rgba(255,255,255,0.05) 100%)`;
        
        // Render dimensional scores
        document.getElementById("score-specificity").textContent = `${report.specificity_score}%`;
        document.getElementById("fill-specificity").style.width = `${report.specificity_score}%`;
        
        document.getElementById("score-consistency").textContent = `${report.consistency_score}%`;
        document.getElementById("fill-consistency").style.width = `${report.consistency_score}%`;
        
        document.getElementById("score-grounded").textContent = `${report.grounded_score}%`;
        document.getElementById("fill-grounded").style.width = `${report.grounded_score}%`;
        
        // Qualitative analysis text
        document.getElementById("evaluation-analysis-text").textContent = report.detailed_analysis;
        
        // Render weak areas list
        const waList = document.getElementById("weak-areas-list");
        waList.innerHTML = "";
        
        if (!report.weak_areas || report.weak_areas.length === 0) {
            waList.innerHTML = `
                <div class="glass-card" style="border-color:var(--success-color); background:rgba(16,185,129,0.02)">
                    <p style="color:var(--success-color); font-weight:600; margin:0">Excellent understanding! No critical weak areas were detected in your defensive responses.</p>
                </div>
            `;
        } else {
            report.weak_areas.forEach(wa => {
                const waCard = document.createElement("div");
                waCard.className = "weak-area-card";
                
                waCard.innerHTML = `
                    <div class="weak-area-header">
                        <h5>${wa.weakness}</h5>
                        <span class="badge badge-high">${wa.category}</span>
                    </div>
                    <p><strong>Evaluation Deficiency:</strong> ${wa.details}</p>
                    <div class="weak-remedy">
                        <strong>Actionable Remedy:</strong> ${wa.remedy}
                    </div>
                `;
                waList.appendChild(waCard);
            });
        }
    }

    // Reset button handler to restart workflow
    restartBtn.addEventListener("click", () => {
        founderConcernsTextarea.value = "";
        selectedStartupKey = null;
        selectedStartupData = null;
        refinedStartupData = null;
        clarityQuestions = [];
        
        document.querySelectorAll(".startup-select-card").forEach(c => c.classList.remove("selected"));
        startupDetailsPane.style.display = "none";
        
        transitionToStage(1);
    });

    // Boot application by loading startups catalog
    loadStartups();
});

