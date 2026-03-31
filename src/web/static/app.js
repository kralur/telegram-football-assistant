const state = {
    tab: "matches",
    selectedLeagueId: null,
    selectedMatchId: null,
    selectedMatchSeed: null,
    detailTab: "events",
    telegramUserId: null,
};

const ui = {
    heroStatus: document.getElementById("hero-status"),
    metricMode: document.getElementById("metric-mode"),
    metricFocus: document.getElementById("metric-focus"),
    metricTip: document.getElementById("metric-tip"),
    tabs: Array.from(document.querySelectorAll(".tab-button")),
    leagueBar: document.getElementById("league-bar"),
    panelTitle: document.getElementById("panel-title"),
    panelMeta: document.getElementById("panel-meta"),
    screenError: document.getElementById("screen-error"),
    screenLoading: document.getElementById("screen-loading"),
    cards: document.getElementById("cards"),
    emptyState: document.getElementById("empty-state"),
    detailMeta: document.getElementById("detail-meta"),
    detailPlaceholder: document.getElementById("detail-placeholder"),
    detailShell: document.getElementById("detail-shell"),
    summaryCard: document.getElementById("summary-card"),
    detailTabs: Array.from(document.querySelectorAll(".detail-tab")),
    detailError: document.getElementById("detail-error"),
    detailLoading: document.getElementById("detail-loading"),
    detailContent: document.getElementById("detail-content"),
};

const telegramApp = window.Telegram?.WebApp;
if (telegramApp) {
    telegramApp.ready();
    telegramApp.expand();
    ui.heroStatus.textContent = "Opened in Telegram";
    state.telegramUserId = telegramApp.initDataUnsafe?.user?.id ?? null;
}

ui.tabs.forEach((button) => {
    button.addEventListener("click", () => {
        state.tab = button.dataset.tab;
        ui.tabs.forEach((tabButton) => {
            tabButton.classList.toggle("is-active", tabButton.dataset.tab === state.tab);
        });
        loadCurrentTab();
    });
});

ui.detailTabs.forEach((button) => {
    button.addEventListener("click", () => {
        state.detailTab = button.dataset.detail;
        ui.detailTabs.forEach((tabButton) => {
            tabButton.classList.toggle("is-active", tabButton.dataset.detail === state.detailTab);
        });
        if (state.selectedMatchId) {
            openMatchDetails(state.selectedMatchId, state.selectedMatchSeed);
        }
    });
});

async function apiGet(path) {
    const response = await fetch(path);
    const payload = await response.json();

    if (!response.ok) {
        throw new Error(payload.error || payload.detail || "No data available");
    }

    return payload;
}

function setError(message = "") {
    ui.screenError.textContent = message;
    ui.screenError.classList.toggle("is-hidden", !message);
}

function setLoading(visible, message = "Loading football data...") {
    ui.screenLoading.textContent = message;
    ui.screenLoading.classList.toggle("is-hidden", !visible);
}

function setEmpty(message = "No data available", visible = false) {
    ui.emptyState.textContent = message;
    ui.emptyState.classList.toggle("is-hidden", !visible);
}

function setMetrics(mode, focus, tip) {
    ui.metricMode.textContent = mode;
    ui.metricFocus.textContent = focus;
    ui.metricTip.textContent = tip;
}

function formatKickoff(value) {
    if (!value) {
        return "Kickoff TBD";
    }

    return new Intl.DateTimeFormat(undefined, {
        dateStyle: "medium",
        timeStyle: "short",
    }).format(new Date(value));
}

function badgeClass(match) {
    if (match.is_live) {
        return "status-badge live";
    }
    if (match.is_finished) {
        return "status-badge finished";
    }
    return "status-badge";
}

function badgeLabel(match) {
    return match.status_long || "Unknown";
}

function renderMatchCard(match, accentLabel = "Open details") {
    const card = document.createElement("article");
    card.className = "match-card";
    card.innerHTML = `
        <div class="match-header">
            <div>
                <h3 class="match-title">${match.home} vs ${match.away}</h3>
                <p class="match-league">${match.country} - ${match.league}</p>
            </div>
            <span class="${badgeClass(match)}">${badgeLabel(match)}</span>
        </div>
        <p class="scoreline">${match.score}</p>
        <p class="match-time">${formatKickoff(match.date)}</p>
        <div class="card-actions">
            <button class="primary">${accentLabel}</button>
            <button>Copy ID</button>
        </div>
    `;

    const [openButton, copyButton] = card.querySelectorAll("button");
    openButton.addEventListener("click", () => openMatchDetails(match.id, match));
    copyButton.addEventListener("click", async () => {
        await navigator.clipboard.writeText(String(match.id));
        ui.heroStatus.textContent = `Match #${match.id} copied`;
    });
    return card;
}

function renderFavoriteCard(item) {
    const card = document.createElement("article");
    card.className = "match-card";

    const nextMatch = item.next_match;
    const lastMatch = item.last_match;
    const nextBlock = nextMatch
        ? `
            <p class="match-time">Next match</p>
            <p class="match-title">${nextMatch.home} vs ${nextMatch.away}</p>
            <p class="match-league">${nextMatch.country} - ${nextMatch.league}</p>
            <p class="match-time">${formatKickoff(nextMatch.date)}</p>
        `
        : `<p class="match-time">No upcoming match available.</p>`;
    const lastBlock = lastMatch
        ? `<p class="match-time">Last result: ${lastMatch.home} ${lastMatch.score} ${lastMatch.away}</p>`
        : `<p class="match-time">Last result unavailable.</p>`;

    card.innerHTML = `
        <div class="match-header">
            <div>
                <h3 class="match-title">${item.team_name}</h3>
                <p class="match-league">Favorite team</p>
            </div>
            <span class="status-badge">${item.team_id || "-"}</span>
        </div>
        ${nextBlock}
        ${lastBlock}
        <div class="card-actions">
            <button class="primary"${nextMatch ? "" : " disabled"}>Open next</button>
            <button class="secondary"${nextMatch ? "" : " disabled"}>Next match ID</button>
        </div>
    `;

    const [openButton, copyButton] = card.querySelectorAll("button");
    if (nextMatch) {
        openButton.addEventListener("click", () => openMatchDetails(nextMatch.id, nextMatch));
        copyButton.addEventListener("click", async () => {
            await navigator.clipboard.writeText(String(nextMatch.id));
            ui.heroStatus.textContent = `${item.team_name} next match copied`;
        });
    }
    return card;
}

function renderLeagueBar(leagues, activeId) {
    ui.leagueBar.innerHTML = "";
    ui.leagueBar.classList.remove("is-hidden");

    leagues.forEach((league) => {
        const button = document.createElement("button");
        button.className = "league-chip";
        button.textContent = league.name;
        button.classList.toggle("is-active", league.id === activeId);
        button.addEventListener("click", () => {
            state.selectedLeagueId = league.id;
            loadStandings();
        });
        ui.leagueBar.appendChild(button);
    });
}

function hideLeagueBar() {
    ui.leagueBar.classList.add("is-hidden");
    ui.leagueBar.innerHTML = "";
}

function renderSummary(match) {
    ui.summaryCard.innerHTML = `
        <h3 class="summary-title">${match.home} vs ${match.away}</h3>
        <div class="summary-grid">
            <div><strong>League:</strong> ${match.country} - ${match.league}</div>
            <div><strong>Score:</strong> ${match.score}</div>
            <div><strong>Status:</strong> ${badgeLabel(match)}</div>
            <div><strong>Kickoff:</strong> ${formatKickoff(match.date)}</div>
        </div>
    `;
}

function renderDetailBlock(title, lines) {
    return `
        <article class="detail-card">
            <h3>${title}</h3>
            <div class="detail-lines">
                ${lines}
            </div>
        </article>
    `;
}

function renderEvents(events) {
    if (!events.length) {
        return `<div class="empty-state">No data available</div>`;
    }

    return events.slice(0, 12).map((event) => renderDetailBlock(
        `${event.minute ?? "-"}' - ${event.team}`,
        `
            <div class="detail-row"><span>${event.type}</span><strong>${event.detail || "Event"}</strong></div>
            <div class="detail-row"><span>Player</span><strong>${event.player}</strong></div>
            <div class="detail-row"><span>Assist</span><strong>${event.assist || "-"}</strong></div>
        `,
    )).join("");
}

function renderStatistics(statistics) {
    if (!statistics.length) {
        return `<div class="empty-state">No data available</div>`;
    }

    return statistics.map((block) => renderDetailBlock(
        block.team,
        block.entries.slice(0, 10).map((entry) => `
            <div class="detail-row"><span>${entry.type}</span><strong>${entry.value}</strong></div>
        `).join(""),
    )).join("");
}

function renderLineups(lineups) {
    if (!lineups.length) {
        return `<div class="empty-state">No data available</div>`;
    }

    return lineups.map((lineup) => renderDetailBlock(
        `${lineup.team} - ${lineup.formation}`,
        `
            <div class="detail-row"><span>Coach</span><strong>${lineup.coach}</strong></div>
            ${lineup.start_xi.slice(0, 11).map((player) => `
                <div class="detail-row"><span>${player.number ?? "-"}</span><strong>${player.name} ${player.pos ? `(${player.pos})` : ""}</strong></div>
            `).join("")}
        `,
    )).join("");
}

function renderPlayers(players) {
    if (!players.length) {
        return `<div class="empty-state">No data available</div>`;
    }

    return players.slice(0, 12).map((player) => renderDetailBlock(
        `${player.name} - ${player.team}`,
        `
            <div class="detail-row"><span>Position</span><strong>${player.position}</strong></div>
            <div class="detail-row"><span>Rating</span><strong>${player.rating || "N/A"}</strong></div>
            <div class="detail-row"><span>Goals / Assists</span><strong>${player.goals} / ${player.assists}</strong></div>
            <div class="detail-row"><span>Minutes</span><strong>${player.minutes ?? 0}</strong></div>
        `,
    )).join("");
}

async function openMatchDetails(matchId, seedMatch = null) {
    state.selectedMatchId = matchId;
    state.selectedMatchSeed = seedMatch;
    ui.detailPlaceholder.classList.add("is-hidden");
    ui.detailShell.classList.remove("is-hidden");
    ui.detailMeta.textContent = `Match #${matchId}`;
    ui.detailError.classList.add("is-hidden");
    ui.detailLoading.classList.remove("is-hidden");
    ui.detailContent.innerHTML = "";

    try {
        const [summaryPayload, detailsPayload] = await Promise.all([
            apiGet(`/api/match/${matchId}`),
            apiGet(`/api/match/${matchId}/${state.detailTab}`),
        ]);

        renderSummary(summaryPayload.match);
        if (state.detailTab === "events") {
            ui.detailContent.innerHTML = renderEvents(detailsPayload.events);
        } else if (state.detailTab === "statistics") {
            ui.detailContent.innerHTML = renderStatistics(detailsPayload.statistics);
        } else if (state.detailTab === "lineups") {
            ui.detailContent.innerHTML = renderLineups(detailsPayload.lineups);
        } else {
            ui.detailContent.innerHTML = renderPlayers(detailsPayload.players);
        }
    } catch (_) {
        if (seedMatch) {
            renderSummary(seedMatch);
            ui.detailContent.innerHTML = `<div class="empty-state">Detailed ${state.detailTab} data is unavailable for featured fallback matches.</div>`;
        }
        ui.detailError.textContent = seedMatch
            ? "Showing summary from fallback showcase data."
            : "No data available";
        ui.detailError.classList.remove("is-hidden");
    } finally {
        ui.detailLoading.classList.add("is-hidden");
    }
}

async function loadLive() {
    hideLeagueBar();
    ui.panelTitle.textContent = "Live Matches";
    ui.panelMeta.textContent = "";
    setMetrics("Mini App", "Live window", "Use this tab during ongoing games");
    setError("");
    setLoading(true, "Loading live matches...");
    setEmpty("", false);
    ui.cards.innerHTML = "";

    try {
        const payload = await apiGet("/live");
        const items = payload.items || [];
        ui.panelMeta.textContent = payload.source === "live" ? `${items.length} live right now` : `Showing ${payload.source} matches`;
        if (!items.length) {
            setEmpty("No live matches right now. Switch to Matches for upcoming kickoffs.", true);
            return;
        }
        items.forEach((match) => ui.cards.appendChild(renderMatchCard(match)));
    } catch (_) {
        setError("Football data is temporarily unavailable.");
    } finally {
        setLoading(false);
    }
}

async function loadMatches() {
    hideLeagueBar();
    ui.panelTitle.textContent = "Upcoming Matches";
    ui.panelMeta.textContent = "";
    setMetrics("Mini App", "Best upcoming picks", "Tap a match to open full detail view");
    setError("");
    setLoading(true, "Loading upcoming matches...");
    setEmpty("", false);
    ui.cards.innerHTML = "";

    try {
        const payload = await apiGet("/matches");
        const items = payload.items || [];
        if (payload.source === "today") {
            ui.panelMeta.textContent = `${items.length} scheduled today`;
        } else if (payload.source === "upcoming") {
            ui.panelMeta.textContent = `${items.length} upcoming picks`;
        } else {
            ui.panelMeta.textContent = "Featured showcase";
        }
        if (!items.length) {
            setEmpty("No upcoming matches are available right now.", true);
            return;
        }
        items.forEach((match) => ui.cards.appendChild(renderMatchCard(match, "Open summary")));
    } catch (_) {
        setError("Football data is temporarily unavailable.");
    } finally {
        setLoading(false);
    }
}

async function loadStandings() {
    ui.panelTitle.textContent = "Standings";
    ui.panelMeta.textContent = "";
    setMetrics("Mini App", "League tables", "Choose a league chip to switch the table");
    setError("");
    setLoading(true, "Loading standings...");
    setEmpty("", false);
    ui.cards.innerHTML = "";

    try {
        const [leaguesPayload, standingsPayload] = await Promise.all([
            apiGet("/api/leagues"),
            apiGet(`/standings${state.selectedLeagueId ? `?league_id=${state.selectedLeagueId}` : ""}`),
        ]);

        const leagues = leaguesPayload.leagues || [];
        const league = standingsPayload.league;
        state.selectedLeagueId = league?.id || state.selectedLeagueId || leagues[0]?.id || null;
        renderLeagueBar(leagues, state.selectedLeagueId);
        ui.panelMeta.textContent = standingsPayload.source === "api" ? (league?.name || "") : `${league?.name || ""} - featured table`;

        const items = standingsPayload.items || [];
        if (!items.length) {
            setEmpty("No standings are available for this league right now.", true);
            return;
        }

        items.slice(0, 12).forEach((row) => {
            const card = document.createElement("article");
            card.className = "match-card";
            card.innerHTML = `
                <div class="match-header">
                    <div>
                        <h3 class="match-title">${row.rank}. ${row.team}</h3>
                        <p class="match-league">${league?.name || "League table"}</p>
                    </div>
                    <span class="status-badge">${row.points} pts</span>
                </div>
                <p class="match-time">Played: ${row.played}</p>
            `;
            ui.cards.appendChild(card);
        });
    } catch (_) {
        setError("Football data is temporarily unavailable.");
        hideLeagueBar();
    } finally {
        setLoading(false);
    }
}

async function loadFavorites() {
    hideLeagueBar();
    ui.panelTitle.textContent = "Favorites";
    ui.panelMeta.textContent = "";
    setMetrics("Mini App", "Personal watchlist", "Open inside Telegram to sync your teams");
    setError("");
    setLoading(true, "Loading favorites...");
    setEmpty("", false);
    ui.cards.innerHTML = "";

    try {
        const query = state.telegramUserId ? `?user_id=${state.telegramUserId}` : "";
        const payload = await apiGet(`/favorites${query}`);
        const items = payload.items || [];
        ui.panelMeta.textContent = payload.source === "api" ? `${items.length} favorite teams` : "Telegram profile required";
        if (!items.length) {
            setEmpty(payload.message || "Open Match Center inside Telegram to load favorites.", true);
            return;
        }
        items.forEach((item) => ui.cards.appendChild(renderFavoriteCard(item)));
    } catch (_) {
        setError("Favorites are temporarily unavailable.");
    } finally {
        setLoading(false);
    }
}

async function loadCurrentTab() {
    ui.heroStatus.textContent = telegramApp ? "Opened in Telegram" : "Browser preview";
    if (state.tab === "live") {
        await loadLive();
    } else if (state.tab === "favorites") {
        await loadFavorites();
    } else if (state.tab === "standings") {
        await loadStandings();
    } else {
        await loadMatches();
    }
}

loadCurrentTab();
