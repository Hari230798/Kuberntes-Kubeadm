// Same-origin: nginx proxies /api/ to the backend service.
const API_BASE = "/api";
const TOKEN_KEY = "dp_admin_token";

// ---------------------------------------------------------------------------
// Engineer registration page
// ---------------------------------------------------------------------------
const engineerForm = document.getElementById("engineerForm");
if (engineerForm) {
    engineerForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        const msg = document.getElementById("message");
        const payload = {
            name: document.getElementById("name").value.trim(),
            experience: document.getElementById("experience").value.trim(),
            contact: document.getElementById("contact").value.trim(),
            qualification: document.getElementById("qualification").value.trim(),
        };
        try {
            const res = await fetch(`${API_BASE}/engineers`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });
            const data = await res.json();
            if (res.ok) {
                msg.textContent = data.message || "Submitted successfully.";
                msg.className = "message success";
                engineerForm.reset();
            } else {
                msg.textContent = data.error || "Submission failed.";
                msg.className = "message error";
            }
        } catch (err) {
            msg.textContent = "Network error: " + err.message;
            msg.className = "message error";
        }
    });
}

// ---------------------------------------------------------------------------
// Admin login + dashboard page
// ---------------------------------------------------------------------------
const loginForm = document.getElementById("loginForm");
if (loginForm) {
    const loginCard = document.getElementById("loginCard");
    const dashboardCard = document.getElementById("dashboardCard");
    const loginMessage = document.getElementById("loginMessage");
    const dashboardMessage = document.getElementById("dashboardMessage");
    const tbody = document.querySelector("#engineersTable tbody");

    function getToken() { return localStorage.getItem(TOKEN_KEY); }

    function showDashboard() {
        loginCard.classList.add("hidden");
        dashboardCard.classList.remove("hidden");
        loadEngineers();
    }

    function showLogin() {
        dashboardCard.classList.add("hidden");
        loginCard.classList.remove("hidden");
    }

    async function loadEngineers() {
        dashboardMessage.textContent = "";
        try {
            const res = await fetch(`${API_BASE}/engineers`, {
                headers: { "Authorization": "Bearer " + getToken() },
            });
            if (res.status === 401) {
                localStorage.removeItem(TOKEN_KEY);
                showLogin();
                return;
            }
            const rows = await res.json();
            tbody.innerHTML = "";
            rows.forEach((r) => {
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td>${r.id}</td>
                    <td>${escapeHtml(r.name)}</td>
                    <td>${escapeHtml(r.experience)}</td>
                    <td>${escapeHtml(r.contact)}</td>
                    <td>${escapeHtml(r.qualification)}</td>
                    <td class="status-${r.status}">${r.status}</td>
                    <td>
                        <button class="approve" data-id="${r.id}" data-status="Approved">Approve</button>
                        <button class="reject" data-id="${r.id}" data-status="Rejected">Reject</button>
                    </td>`;
                tbody.appendChild(tr);
            });
        } catch (err) {
            dashboardMessage.textContent = "Failed to load: " + err.message;
            dashboardMessage.className = "message error";
        }
    }

    tbody.addEventListener("click", async (event) => {
        const btn = event.target.closest("button[data-id]");
        if (!btn) return;
        const id = btn.getAttribute("data-id");
        const status = btn.getAttribute("data-status");
        try {
            const res = await fetch(`${API_BASE}/engineers/${id}`, {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": "Bearer " + getToken(),
                },
                body: JSON.stringify({ status }),
            });
            if (res.ok) {
                loadEngineers();
            } else {
                const data = await res.json();
                dashboardMessage.textContent = data.error || "Update failed.";
                dashboardMessage.className = "message error";
            }
        } catch (err) {
            dashboardMessage.textContent = "Network error: " + err.message;
            dashboardMessage.className = "message error";
        }
    });

    document.getElementById("logoutBtn").addEventListener("click", () => {
        localStorage.removeItem(TOKEN_KEY);
        showLogin();
    });

    loginForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        const payload = {
            username: document.getElementById("username").value.trim(),
            password: document.getElementById("password").value,
        };
        try {
            const res = await fetch(`${API_BASE}/admin/login`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });
            const data = await res.json();
            if (res.ok) {
                localStorage.setItem(TOKEN_KEY, data.token);
                loginMessage.textContent = "";
                showDashboard();
            } else {
                loginMessage.textContent = data.error || "Login failed.";
                loginMessage.className = "message error";
            }
        } catch (err) {
            loginMessage.textContent = "Network error: " + err.message;
            loginMessage.className = "message error";
        }
    });

    function escapeHtml(str) {
        return String(str)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;");
    }

    // Auto-resume session if a token already exists.
    if (getToken()) { showDashboard(); }
}
