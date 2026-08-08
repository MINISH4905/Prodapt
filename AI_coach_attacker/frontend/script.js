const API_BASE = window.location.origin;

const ideaInput = document.getElementById("idea-input");
const attackBtn = document.getElementById("attack-btn");
const errorMsg = document.getElementById("error-msg");
const loadingSection = document.getElementById("loading-section");
const resultsSection = document.getElementById("results-section");
const attackerCards = document.getElementById("attacker-cards");
const severitySections = document.getElementById("severity-sections");
const demoBadge = document.getElementById("demo-badge");
const modalOverlay = document.getElementById("modal-overlay");
const modalContent = document.getElementById("modal-content");
const modalClose = document.getElementById("modal-close");

const ATTACKER_META = {
    market: {
        title: "MARKET ATTACKER",
        persona: "Hostile Market Analyst",
    },
    business: {
        title: "BUSINESS MODEL ATTACKER",
        persona: "Investor Skeptic",
    },
    technology: {
        title: "TECHNOLOGY ATTACKER",
        persona: "Skeptical CTO",
    },
};

let attackData = null;

function showError(message) {
    errorMsg.textContent = message;
    errorMsg.classList.remove("hidden");
}

function hideError() {
    errorMsg.classList.add("hidden");
}

function setStepDone(stepId) {
    const step = document.getElementById(stepId);
    step.classList.add("done");
    step.querySelector(".step-icon").textContent = "[\u2713]";
}

function resetSteps() {
    ["step-market", "step-business", "step-technology", "step-map"].forEach((id) => {
        const step = document.getElementById(id);
        step.classList.remove("done");
        step.querySelector(".step-icon").textContent = "[ ]";
    });
}

function renderVulnCard(vuln, attackerKey) {
    const attackerLabel = vuln.attacker
        ? vuln.attacker.toUpperCase()
        : attackerKey.toUpperCase();

    return `
        <div class="vuln-card">
            <div class="vuln-title">${escapeHtml(vuln.title)}</div>
            <div class="vuln-severity">${escapeHtml(vuln.severity)}</div>
            <div class="vuln-field">
                <div class="vuln-field-label">ATTACKER:</div>
                <div class="vuln-field-value">${escapeHtml(attackerLabel)}</div>
            </div>
            <div class="vuln-field">
                <div class="vuln-field-label">CATEGORY:</div>
                <div class="vuln-field-value">${escapeHtml(vuln.category.toUpperCase())}</div>
            </div>
            <div class="vuln-field">
                <div class="vuln-field-label">WHY IT MATTERS:</div>
                <div class="vuln-field-value">${escapeHtml(vuln.reason)}</div>
            </div>
            <div class="vuln-field">
                <div class="vuln-field-label">ATTACK QUESTION:</div>
                <div class="vuln-field-value attack-question">"${escapeHtml(vuln.attack_question)}"</div>
            </div>
            <div class="vuln-field">
                <div class="vuln-field-label">AREA TO FIX:</div>
                <div class="vuln-field-value">${escapeHtml(vuln.suggested_area_to_fix)}</div>
            </div>
        </div>
    `;
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

function renderAttackerCards(data) {
    attackerCards.innerHTML = "";

    for (const key of ["market", "business", "technology"]) {
        const vulnerabilities = data.attackers[key];
        const meta = ATTACKER_META[key];
        const vulnCount = vulnerabilities.length;

        const card = document.createElement("div");
        card.className = "attacker-card";
        card.innerHTML = `
            <div class="card-title">${meta.title}</div>
            <div class="card-persona">${meta.persona}</div>
            <div class="card-vuln-count">${vulnCount} ${vulnCount === 1 ? "VULNERABILITY" : "VULNERABILITIES"}</div>
            <button class="view-btn" data-attacker="${key}" type="button">VIEW</button>
        `;
        attackerCards.appendChild(card);
    }

    attackerCards.querySelectorAll(".view-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            showAttackerModal(btn.dataset.attacker);
        });
    });
}

function showAttackerModal(attackerKey) {
    const vulnerabilities = attackData.attackers[attackerKey];
    const meta = ATTACKER_META[attackerKey];

    modalContent.innerHTML = `
        <h2 style="font-size:0.85rem;letter-spacing:0.15em;margin-bottom:4px;">${meta.title}</h2>
        <p style="font-size:0.75rem;color:#666;margin-bottom:16px;">${meta.persona}</p>
        ${vulnerabilities.map((vuln) => renderVulnCard(vuln, attackerKey)).join('<hr class="modal-divider">')}
    `;
    modalOverlay.classList.remove("hidden");
}

function renderVulnerabilityMap(data) {
    const map = data.vulnerability_map;
    severitySections.innerHTML = "";

    const severities = [
        { key: "critical", label: "CRITICAL" },
        { key: "high", label: "HIGH" },
        { key: "medium", label: "MEDIUM" },
        { key: "low", label: "LOW" },
    ];

    for (const { key, label } of severities) {
        const items = map[key];
        if (!items || items.length === 0) continue;

        const group = document.createElement("div");
        group.className = "severity-group";
        group.innerHTML = `<h3>${label}</h3>`;
        items.forEach((vuln) => {
            group.innerHTML += renderVulnCard(vuln);
        });
        severitySections.appendChild(group);
    }
}

async function simulateLoadingSteps() {
    const delays = [
        { id: "step-market", ms: 400 },
        { id: "step-business", ms: 400 },
        { id: "step-technology", ms: 400 },
        { id: "step-map", ms: 300 },
    ];

    for (const { id, ms } of delays) {
        await new Promise((resolve) => setTimeout(resolve, ms));
        setStepDone(id);
    }
}

async function checkDemoMode() {
    try {
        const res = await fetch(`${API_BASE}/api/demo-mode`);
        if (res.ok) {
            const data = await res.json();
            if (data.demo_mode) {
                demoBadge.classList.remove("hidden");
            }
        }
    } catch {
        // Backend may not be running yet
    }
}

async function runAttack() {
    hideError();
    const idea = ideaInput.value.trim();

    if (!idea) {
        showError("Please enter a startup idea.");
        return;
    }

    attackBtn.disabled = true;
    loadingSection.classList.remove("hidden");
    resultsSection.classList.add("hidden");
    resetSteps();

    try {
        const fetchPromise = fetch(`${API_BASE}/api/attack`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ idea }),
        });

        await simulateLoadingSteps();

        const response = await fetchPromise;

        if (!response.ok) {
            let message = "Unable to complete attack analysis.";
            try {
                const err = await response.json();
                if (err.detail) message = err.detail;
            } catch {
                // use default message
            }
            showError(message);
            loadingSection.classList.add("hidden");
            attackBtn.disabled = false;
            return;
        }

        attackData = await response.json();

        renderAttackerCards(attackData);
        renderVulnerabilityMap(attackData);

        loadingSection.classList.add("hidden");
        resultsSection.classList.remove("hidden");
    } catch {
        showError("Unable to complete attack analysis.");
        loadingSection.classList.add("hidden");
    }

    attackBtn.disabled = false;
}

attackBtn.addEventListener("click", runAttack);

modalClose.addEventListener("click", () => {
    modalOverlay.classList.add("hidden");
});

modalOverlay.addEventListener("click", (e) => {
    if (e.target === modalOverlay) {
        modalOverlay.classList.add("hidden");
    }
});

checkDemoMode();
