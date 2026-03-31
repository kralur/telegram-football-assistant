const state = {
    screen: "today",
    leagueId: null,
    selectedMatchId: null,
    detailTab: "events",
    favoriteUserId: window.localStorage.getItem("miniapp.favoriteUserId") || "",
};

const elements = {
    statusBadge: document.getElementById("status-badge"),
    tabButtons: Array.from(document.querySelectorAll(".tab-button")),
    panelTitle: document.getElementById("panel-title"),
    panelCount: document.getElementById("panel-count"),
    screenError: document.getElementById("screen-error"),
    screenLoading: document.getElementById("screen-loading"),
    screenContent: document.getElementById("screen-content"),
    screenEmpty: document.getElementById("screen-empty"),
    leagueFilters: document.getElementById("league-filters"),
    favoritesControls: document.getElementById("favorites-controls"),
    favoritesUserId: document.getElementById("favorites-user-id"),
    detailsPlaceholder: document.getElementById("details-placeholder"),
    detailsShell: document.getElementById("details-shell"),
    matchSummary: document.getElementById("match-summary"),
    detailsError: document.getElementById("details-error"),
    detailsLoading: document.getElementById("details-loading"),
    detailsContent: document.getElementById("details-content"),
    closeDetails: document.getElementById("close-details"),
    detailTabs: Array.from(document.querySelectorAll(".detail-tab")),
};

const telegramApp = window.Telegram?.WebApp;
if (telegramApp) {
    telegramApp.ready();
    telegramApp.expand();
    const telegramUserId = telegramApp.initDataUnsafe?.user?.id;
    if (telegramUserId && !state.favoriteUserId) {
        state.favoriteUserId = String(telegramUserId);
        window.localStorage.setItem("miniapp.favoriteUserId", state.favoriteUserId);
    }
}

elements.favoritesUserId.value = state.favoriteUserId;

elements.tabButtons.forEach((button) => {
    button.addEventListener("click", () => switchScreen(button.dataset.screen));
});

elements.favoritesControls.addEventListener("submit", (event) => {
    event.preventDefault();
    state.favoriteUserId = elements.favoritesUserId.value.trim();
    window.localStorage.setItem("miniapp.favoriteUserId", state.favoriteUserId);
    loadCurrentScreen();
});

elements.closeDetails.addEventListener("click", () => {
    state.selectedMatchId = null;
    elements.detailsShell.classList.add("is-hidden");
    elements.closeDetails.classList.add("is-hidden");
    elements.detailsPlaceholder.classList.remove("is-hidden");
    elements.detailsError.classList.add("is-hidden");
});

elements.detailTabs.forEach((button) => {
    button.addEventListener("click", () => {
        state.detailTab = button.dataset.detail;
        updateDetailTabs();
        if (state.selectedMatchId) {
            renderMatchDetails(state.selectedMatchId);
        }
    });
});

async function apiGet(path) {
    const response = await fetch(path);
    const payload = await response.json();

    if (!response.ok) {
        throw new Error(payload.error || payload.detail || "Failed to load football data.");
    }

    return payload;
}

function setLoading(target, visible, message = "") {
    target.textContent = message || target.textContent;
    target.classList.toggle("is-hidden", !visible);
}

function setError(target, message = "") {
    target.textContent = message;
    target.classList.toggle("is-hidden", !message);
}

function setEmpty(visible, message = "No data yet. Try another league or refresh later.") {
    elements.screenEmpty.textContent = message;
    elements.screenEmpty.classList.toggle("is-hidden", !visible);
}

function switchScreen(screen) {
    state.screen = screen;
    state.leagueId = screen === "today" ? state.leagueId : null;

    elements.tabButtons.forEach((button) => {
        button.classList.toggle("is-active", button.dataset.screen === screen);
    });

    loadCurrentScreen();
}

function updateToolbar() {
    const showLeagueFilters = state.screen === "today";
    const showFavoritesControls = state.screen === "favorites";
    elements.leagueFilters.classList.toggle("is-hidden", !showLeagueFilters);
    elements.favoritesControls.classList.toggle("is-hidden", !showFavoritesControls);
}

function updateDetailTabs() {
    elements.detailTabs.forEach((button) => {
        button.classList.toggle("is-active", button.dataset.detail === state.detailTab);
    });
}

function formatKickoff(dateValue) {
    if (!dateValue) {
        return "Kickoff TBD";
    }

    const formatter = new Intl.DateTimeFormat(undefined, {
        dateStyle: "medium",
        timeStyle: "short",
    });

    return formatter.format(new Date(dateValue));
}

function statusLabel(match) {
    if (match.is_live) {
        return match.status_long || "Live";
    }
    if (match.is_finished) {
        return match.status_long || "Finished";
    }
    return match.status_long || "Scheduled";
}

function renderLeagues(leagues) {
    elements.leagueFilters.innerHTML = "";
    const options = [{ id: null, name: "All leagues" }, ...leagues];

    options.forEach((league) => {
        const button = document.createElement("button");
        button.className = "chip-button";
        button.textContent = league.name;
        button.classList.toggle("is-active", state.leagueId === league.id);
        button.addEventListener("click", () => {
            state.leagueId = league.id;
            loadToday();
        });
        elements.leagueFilters.appendChild(button);
    });
}

function createMatchCard(match) {
    const card = document.createElement("article");
    card.className = "match-card";

    const statusClass = match.is_live ? "status-pill is-live" : "status-pill";

    card.innerHTML = `
        <div class="match-header">
            <div>
                <h3 class="match-title">${match.home} vs ${match.away}</h3>
                <p class="match-meta">${match.country} • ${match.league}</p>
            </div>
            <span class="${statusClass}">${statusLabel(match)}</span>
        </div>
        <p class="scoreline">${match.score}</p>
        <p class="match-subline">${formatKickoff(match.date)}</p>
        <div class="card-actions">
            <button class="match-action">Open details</button>
            <button class="match-action secondary">Copy match ID</button>
        </div>
    `;

    const [openButton, copyButton] = card.querySelectorAll("button");
    openButton.addEventListener("click", () => openMatch(match.id));
    copyButton.addEventListener("click", async () => {
        await navigator.clipboard.writeText(String(match.id));
        elements.statusBadge.textContent = `Match #${match.id} copied`;
    });

    return card;
}

function createFavoriteCard(favorite) {
    const card = document.createElement("article");
    card.className = "favorite-card";

    const nextMatchText = favorite.next_match
        ? `${favorite.next_match.home} vs ${favorite.next_match.away} • ${formatKickoff(favorite.next_match.date)}`
        : "No upcoming match available";
    const lastMatchText = favorite.last_match
        ? `${favorite.last_match.home} ${favorite.last_match.score} ${favorite.last_match.away}`
        : "No last result available";

    card.innerHTML = `
        <div class="favorite-header">
            <div>
                <h3 class="favorite-title">${favorite.team_name}</h3>
                <p class="favorite-meta">Next: ${nextMatchText}</p>
                <p class="favorite-meta">Last: ${lastMatchText}</p>
            </div>
        </div>
        <div class="favorite-actions">
            <button class="favorite-action">Open next match</button>
        </div>
    `;

    const button = card.querySelector("button");
    button.disabled = !favorite.next_match;
    button.addEventListener("click", () => {
        if (favorite.next_match) {
            openMatch(favorite.next_match.id);
        }
    });

    return card;
}

async function openMatch(matchId) {
    state.selectedMatchId = matchId;
    state.detailTab = state.detailTab || "events";
    updateDetailTabs();
    elements.closeDetails.classList.remove("is-hidden");
    elements.detailsPlaceholder.classList.add("is-hidden");
    elements.detailsShell.classList.remove("is-hidden");
    await renderMatchDetails(matchId);
}

function renderSummary(match) {
    elements.matchSummary.innerHTML = `
        <h3 class="summary-title">${match.home} vs ${match.away}</h3>
        <div class="summary-grid">
            <div><strong>League:</strong> ${match.country} • ${match.league}</div>
            <div><strong>Score:</strong> ${match.score}</div>
            <div><strong>Status:</strong> ${statusLabel(match)}</div>
            <div><strong>Kickoff:</strong> ${formatKickoff(match.date)}</div>
        </div>
    `;
}

function renderEvents(events) {
    if (!events.length) {
        return `<div class="empty-state">No events available for this match yet.</div>`;
    }

    return `
        <div class="detail-section">
            ${events.map((event) => `
                <div class="detail-card">
                    <div class="event-line">
                        <strong>${event.minute ?? "-"}'</strong>
                        <span>${event.team}</span>
                    </div>
                    <div>${event.type} • ${event.detail}</div>
                    <div>${event.player}${event.assist ? ` (assist: ${event.assist})` : ""}</div>
                </div>
            `).join("")}
        </div>
    `;
}

function renderStatistics(statistics) {
    if (!statistics.length) {
        return `<div class="empty-state">No statistics available.</div>`;
    }

    return `
        <div class="detail-section">
            ${statistics.map((block) => `
                <div class="detail-card">
                    <h3>${block.team}</h3>
                    ${block.entries.map((entry) => `
                        <div class="stat-line">
                            <span>${entry.type}</span>
                            <strong>${entry.value}</strong>
                        </div>
                    `).join("")}
                </div>
            `).join("")}
        </div>
    `;
}

function renderLineups(lineups) {
    if (!lineups.length) {
        return `<div class="empty-state">Lineups are not available yet.</div>`;
    }

    return `
        <div class="detail-section">
            ${lineups.map((lineup) => `
                <div class="detail-card">
                    <h3>${lineup.team}</h3>
                    <p>Formation: ${lineup.formation} • Coach: ${lineup.coach}</p>
                    <div>
                        <strong>Starting XI</strong>
                        ${lineup.start_xi.map((player) => `
                            <div class="lineup-player">
                                <span>${player.number ?? "-"} • ${player.name}</span>
                                <span>${player.pos ?? "N/A"}</span>
                            </div>
                        `).join("")}
                    </div>
                </div>
            `).join("")}
        </div>
    `;
}

function renderPlayers(players) {
    if (!players.length) {
        return `<div class="empty-state">Player stats are not available.</div>`;
    }

    return `
        <div class="detail-section">
            ${players.slice(0, 14).map((player) => `
                <div class="detail-card">
                    <div class="player-line">
                        <strong>${player.name}</strong>
                        <span>${player.team}</span>
                    </div>
                    <div class="player-line">
                        <span>${player.position}</span>
                        <span>Rating: ${player.rating || "N/A"}</span>
                    </div>
                    <div class="player-line">
                        <span>Goals ${player.goals}</span>
                        <span>Assists ${player.assists}</span>
                    </div>
                    <div class="player-line">
                        <span>Minutes ${player.minutes ?? 0}</span>
                        <span>Passes ${player.passes}</span>
                    </div>
                </div>
            `).join("")}
        </div>
    `;
}

async function renderMatchDetails(matchId) {
    setError(elements.detailsError, "");
    setLoading(elements.detailsLoading, true, "Loading match details...");
    elements.detailsContent.innerHTML = "";

    try {
        const [summaryPayload, sectionPayload] = await Promise.all([
            apiGet(`/api/match/${matchId}`),
            apiGet(`/api/match/${matchId}/${state.detailTab}`),
        ]);

        renderSummary(summaryPayload.match);

        if (state.detailTab === "events") {
            elements.detailsContent.innerHTML = renderEvents(sectionPayload.events);
        } else if (state.detailTab === "statistics") {
            elements.detailsContent.innerHTML = renderStatistics(sectionPayload.statistics);
        } else if (state.detailTab === "lineups") {
            elements.detailsContent.innerHTML = renderLineups(sectionPayload.lineups);
        } else {
            elements.detailsContent.innerHTML = renderPlayers(sectionPayload.players);
        }
    } catch (error) {
        setError(elements.detailsError, error.message);
    } finally {
        setLoading(elements.detailsLoading, false);
    }
}

async function loadToday() {
    updateToolbar();
    elements.panelTitle.textContent = state.leagueId ? "Today filtered" : "Today";
    setError(elements.screenError, "");
    setLoading(elements.screenLoading, true, "Loading today's matches...");
    setEmpty(false);
    elements.screenContent.innerHTML = "";

    try {
        const [leaguesPayload, todayPayload] = await Promise.all([
            apiGet("/api/leagues"),
            apiGet(`/api/today${state.leagueId ? `?league_id=${state.leagueId}` : ""}`),
        ]);

        renderLeagues(leaguesPayload.leagues);
        elements.panelCount.textContent = `${todayPayload.matches.length} matches`;

        if (!todayPayload.matches.length) {
            setEmpty(true, "No matches for this filter right now.");
            return;
        }

        todayPayload.matches.slice(0, 12).forEach((match) => {
            elements.screenContent.appendChild(createMatchCard(match));
        });
    } catch (error) {
        setError(elements.screenError, error.message);
    } finally {
        setLoading(elements.screenLoading, false);
    }
}

async function loadLive() {
    updateToolbar();
    elements.panelTitle.textContent = "Live";
    elements.panelCount.textContent = "";
    setError(elements.screenError, "");
    setLoading(elements.screenLoading, true, "Loading live matches...");
    setEmpty(false);
    elements.screenContent.innerHTML = "";

    try {
        const payload = await apiGet("/api/live");
        elements.panelCount.textContent = `${payload.matches.length} matches`;

        if (!payload.matches.length) {
            setEmpty(true, "No live matches at the moment.");
            return;
        }

        payload.matches.forEach((match) => {
            elements.screenContent.appendChild(createMatchCard(match));
        });
    } catch (error) {
        setError(elements.screenError, error.message);
    } finally {
        setLoading(elements.screenLoading, false);
    }
}

async function loadFavorites() {
    updateToolbar();
    elements.panelTitle.textContent = "Favorites";
    elements.panelCount.textContent = state.favoriteUserId ? `User ${state.favoriteUserId}` : "";
    setError(elements.screenError, "");
    setLoading(elements.screenLoading, true, "Loading favorite teams...");
    setEmpty(false);
    elements.screenContent.innerHTML = "";

    if (!state.favoriteUserId) {
        setLoading(elements.screenLoading, false);
        setEmpty(true, "Enter a Telegram user ID to load favorites.");
        return;
    }

    try {
        const payload = await apiGet(`/api/favorites/${state.favoriteUserId}`);
        elements.panelCount.textContent = `${payload.favorites.length} teams`;

        if (!payload.favorites.length) {
            setEmpty(true, "This user has no favorite teams yet.");
            return;
        }

        payload.favorites.forEach((favorite) => {
            elements.screenContent.appendChild(createFavoriteCard(favorite));
        });
    } catch (error) {
        setError(elements.screenError, error.message);
    } finally {
        setLoading(elements.screenLoading, false);
    }
}

async function loadCurrentScreen() {
    elements.statusBadge.textContent = "Syncing";
    if (state.screen === "today") {
        await loadToday();
    } else if (state.screen === "live") {
        await loadLive();
    } else {
        await loadFavorites();
    }
    elements.statusBadge.textContent = "Ready";
}

loadCurrentScreen();
