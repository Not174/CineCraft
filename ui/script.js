const state = {
    liveJobs: new Map(),
    currentRoute: "home",
    editor: {
        duration: 0,
        startPercent: 0,
        endPercent: 100,
        activeHandle: "start",
        controlTarget: "selection",
        syncingPreview: false,
    },
};

const routes = {
    home: "/",
    convert: "/convert",
    merge: "/merge",
    extract: "/extract",
    edit: "/edit",
};

const tools = {
    convert: {
        button: "run-convert",
        progress: "progress-convert",
        label: "progress-label-convert",
        artifacts: "artifacts-convert",
        status: "status-convert",
        title: "Ready for conversion",
        copy: "Choose a source clip and export format to start.",
        actionText: "Start Conversion",
        run: runConvert,
    },
    merge: {
        button: "run-merge",
        progress: "progress-merge",
        label: "progress-label-merge",
        artifacts: "artifacts-merge",
        status: "status-merge",
        title: "Build a merged master",
        copy: "Combine matching sources quickly, or export MP4 for broad playback support.",
        actionText: "Merge Files",
        run: runMerge,
    },
    extract: {
        button: "run-extract",
        progress: "progress-extract",
        label: "progress-label-extract",
        artifacts: "artifacts-extract",
        status: "status-extract",
        title: "Prepare isolated assets",
        copy: "Text subtitles and multiple audio tracks are exported separately, with a ZIP bundle when useful.",
        actionText: "Extract Tracks",
        run: runExtract,
    },
    edit: {
        button: "run-edit",
        progress: "progress-edit",
        label: "progress-label-edit",
        artifacts: "artifacts-edit",
        status: "status-edit",
        title: "Shape the final cut",
        copy: "Use the range controls after preview metadata loads, then export a clean MP4.",
        actionText: "Export Edit",
        run: runEdit,
    },
};

const byId = (id) => document.getElementById(id);

// Wait for pywebview API to be ready
async function waitForAPI(timeout = 5000) {
    const start = Date.now();
    while (Date.now() - start < timeout) {
        if (window.pywebview && window.pywebview.api) {
            return true;
        }
        await new Promise(resolve => setTimeout(resolve, 100));
    }
    return false;
}

document.addEventListener("DOMContentLoaded", async () => {
    bindRoutes();
    bindTipsCarousel();
    bindSuggestors();
    bindExtractOptions();
    bindResets();
    bindEditor();
    
    // Wait for API before binding buttons
    await waitForAPI();
    bindBrowseButtons();
    bindActionButtons();
    
    refreshHealth();
    refreshCurrentStatus();
    window.setInterval(pollJobs, 1200);
    window.setInterval(refreshCurrentStatus, 5000);
    byId("refresh-status").addEventListener("click", refreshCurrentStatus);
});


function bindTipsCarousel() {
    const tips = [...document.querySelectorAll("#tips-list .tip")];
    if (tips.length < 2) return;

    let activeIndex = tips.findIndex((tip) => tip.classList.contains("is-active"));
    if (activeIndex < 0) activeIndex = 0;

    window.setInterval(() => {
        const current = tips[activeIndex];
        const nextIndex = (activeIndex + 1) % tips.length;
        const next = tips[nextIndex];

        current.classList.remove("is-active");
        current.classList.add("is-exit");

        next.classList.add("is-enter");

        window.requestAnimationFrame(() => {
            window.requestAnimationFrame(() => {
                next.classList.add("is-active");
                next.classList.remove("is-enter");
            });
        });

        window.setTimeout(() => current.classList.remove("is-exit"), 520);
        activeIndex = nextIndex;
    }, 3000);
}

function bindRoutes() {
    document.querySelectorAll("[data-route]").forEach((button) => {
        button.addEventListener("click", () => goToRoute(button.dataset.route));
    });
    window.addEventListener("popstate", () => applyRoute(window.location.pathname));
    applyRoute(window.location.pathname);
}

function goToRoute(route) {
    const targetPath = routes[route] || routes.home;
    if (window.location.pathname !== targetPath) {
        window.history.pushState({}, "", targetPath);
    }
    applyRoute(targetPath);
}

function applyRoute(pathname) {
    const route = Object.entries(routes).find(([, path]) => path === pathname)?.[0] || "home";
    state.currentRoute = route;
    document.body.dataset.route = route;
    document.querySelectorAll(".tool-tab").forEach((item) => item.classList.toggle("active", item.dataset.route === route));
    byId("hero-panel").style.display = route === "home" ? "grid" : "none";
    byId("tool-home").classList.toggle("active", route === "home");
    document.querySelectorAll(".tool-panel").forEach((panel) => panel.classList.toggle("active", panel.dataset.panel === route));
    document.title = route === "home" ? "CineCraft" : `CineCraft - ${capitalize(route)}`;
}

function bindBrowseButtons() {
    document.querySelectorAll("[data-browse]").forEach((button) => {
        button.addEventListener("click", async () => {
            // Final check before attempting API call
            if (!window.pywebview?.api) {
                showError("Desktop file dialogs are only available inside the CineCraft app window.");
                return;
            }
            try {
                const kind = button.dataset.browse;
                let value = null;
                if (kind === "file") value = await window.pywebview.api.choose_file();
                if (kind === "multiple") value = await window.pywebview.api.choose_multiple();
                if (kind === "folder") value = await window.pywebview.api.choose_folder();
                if (kind === "save") {
                    const fixed = button.dataset.fixedExtension || "";
                    const formatId = button.dataset.format;
                    const extension = fixed || (formatId ? byId(formatId).value : "");
                    value = await window.pywebview.api.choose_save_path(extension);
                }
                if (!value || (Array.isArray(value) && value.length === 0)) return;
                const target = byId(button.dataset.target);
                target.value = Array.isArray(value) ? value.join("; ") : value;
                if (button.dataset.suggest) suggestOutput(button.dataset.target, button.dataset.suggest, button.dataset.format);
                if (button.dataset.target === "edit-input") {
                    if (!byId("edit-output").value) byId("edit-output").value = suggestFileName(target.value, ".mp4", "_edit");
                    await prepareEditor(target.value);
                }
            } catch (error) {
                console.error("Browse button error:", error);
                showError("Failed to open file dialog: " + error.message);
            }
        });
    });
}

function bindSuggestors() {
    document.querySelectorAll("[data-suggest-from]").forEach((element) => {
        element.addEventListener("change", () => suggestOutput(element.dataset.suggestFrom, element.dataset.suggestTarget, element.id));
    });
}

function bindExtractOptions() {
    const type = byId("extract-type");
    const format = byId("extract-subtitle-format");
    if (!type || !format) return;
    type.addEventListener("change", syncExtractOptions);
    syncExtractOptions();
}

function syncExtractOptions() {
    const type = byId("extract-type");
    const format = byId("extract-subtitle-format");
    if (!type || !format) return;
    const isSubtitle = type.value === "subtitle";
    format.disabled = !isSubtitle;
    format.title = isSubtitle ? "Choose the subtitle export format." : "Subtitle format is only used for subtitle extraction.";
}

function bindActionButtons() {
    Object.entries(tools).forEach(([tool, config]) => {
        byId(config.button).addEventListener("click", async () => {
            const jobId = byId(config.button).dataset.jobId;
            if (jobId) {
                try {
                    await api(`/api/jobs/${jobId}/cancel`, { method: "POST" });
                    state.liveJobs.delete(jobId);
                    setActionButton(tool, null);
                    refreshCurrentStatus();
                } catch (error) {
                    showError(error.message);
                }
                return;
            }
            await config.run();
        });
    });
}

function bindResets() {
    document.querySelectorAll("[data-reset]").forEach((button) => {
        button.addEventListener("click", () => resetTool(button.dataset.reset));
    });
}

function bindEditor() {
    const preview = byId("edit-preview");
    const startRange = byId("edit-start-range");
    const endRange = byId("edit-end-range");
    const editMode = byId("edit-mode");

    startRange.addEventListener("input", () => {
        state.editor.controlTarget = "selection";
        state.editor.activeHandle = "start";
        state.editor.startPercent = Math.min(Number(startRange.value), state.editor.endPercent - 0.2);
        syncEditor("start");
    });

    endRange.addEventListener("input", () => {
        state.editor.controlTarget = "selection";
        state.editor.activeHandle = "end";
        state.editor.endPercent = Math.max(Number(endRange.value), state.editor.startPercent + 0.2);
        syncEditor("end");
    });

    startRange.addEventListener("pointerdown", () => {
        state.editor.controlTarget = "selection";
        state.editor.activeHandle = "start";
    });
    startRange.addEventListener("focus", () => {
        state.editor.controlTarget = "selection";
        state.editor.activeHandle = "start";
    });
    endRange.addEventListener("pointerdown", () => {
        state.editor.controlTarget = "selection";
        state.editor.activeHandle = "end";
    });
    endRange.addEventListener("focus", () => {
        state.editor.controlTarget = "selection";
        state.editor.activeHandle = "end";
    });

    editMode.addEventListener("change", () => {
        syncEditor(false);
    });

    preview.addEventListener("timeupdate", () => {
        if (!state.editor.duration) return;
        const { start, end } = getEditorBounds();
        if (preview.currentTime < start) {
            setPreviewCurrentTime(start);
        } else if (preview.currentTime >= end) {
            setPreviewCurrentTime(end);
            preview.pause();
        }
        updateRangePlayhead(preview.currentTime);
    });

    preview.addEventListener("seeking", () => {
        if (!state.editor.duration) return;
        if (!state.editor.syncingPreview) {
            state.editor.controlTarget = "playhead";
        }
        const clampedTime = clampPreviewTime(preview.currentTime);
        if (Math.abs(clampedTime - preview.currentTime) > 0.01) {
            setPreviewCurrentTime(clampedTime);
            return;
        }
        updateRangePlayhead(preview.currentTime);
    });

    preview.addEventListener("seeked", () => {
        state.editor.syncingPreview = false;
        if (!state.editor.duration) return;
        updateRangePlayhead(preview.currentTime);
    });

    preview.addEventListener("play", () => {
        if (!state.editor.duration) return;
        const { start, end } = getEditorBounds();
        state.editor.controlTarget = "playhead";
        if (preview.currentTime < start || preview.currentTime >= end) {
            setPreviewCurrentTime(start);
        }
        updateRangePlayhead(preview.currentTime);
    });

    document.querySelectorAll("[data-seek-ms]").forEach((button) => {
        button.addEventListener("click", () => seekPreviewBy(Number(button.dataset.seekMs || 0)));
    });

    setSeekButtonsEnabled(false);
}

async function refreshHealth() {
    try {
        const payload = await api("/api/health");
        const pill = byId("engine-pill");
        const ok = payload.ffmpeg && payload.ffprobe;
        pill.classList.toggle("online", ok);
        pill.classList.toggle("error", !ok);
        byId("engine-text").textContent = ok ? "FFmpeg and FFprobe ready" : "FFmpeg setup incomplete";
    } catch {
        byId("engine-pill").classList.add("error");
        byId("engine-text").textContent = "Backend unavailable";
    }
}

async function refreshCurrentStatus() {
    try {
        const payload = await api("/api/jobs");
        const items = payload.items || [];
        const active = items.find((item) => isLiveStatus(item.status));
        renderCurrentStatus(active || items[0] || null, !active);
    } catch {
        renderCurrentStatus(null, false);
    }
}

function renderCurrentStatus(job, isHistorical = false) {
    if (!job) {
        byId("current-status-title").textContent = "Idle";
        byId("current-status-message").textContent = "No active processing right now. Launch a tool to begin.";
        byId("current-status-progress").style.width = "0%";
        byId("current-status-percent").textContent = "0%";
        byId("current-status-kind").textContent = "Standby";
        byId("current-status-log").textContent = "Ready for your next render.";
        return;
    }

    const kind = isHistorical ? `Last ${job.status}` : capitalize(job.kind);
    const log = (job.logs && job.logs.length ? job.logs[job.logs.length - 1] : "").trim();
    const progress = clamp(Number(job.progress) || 0, 0, 100);
    byId("current-status-title").textContent = job.title;
    byId("current-status-message").textContent = job.message || "Processing...";
    byId("current-status-progress").style.width = `${progress}%`;
    byId("current-status-percent").textContent = formatProgress(progress);
    byId("current-status-kind").textContent = kind;
    byId("current-status-log").textContent = log || job.command_preview || "Waiting for fresh processing details.";
}

function suggestOutput(sourceId, targetId, formatId) {
    const value = byId(sourceId).value;
    if (!value) return;
    byId(targetId).value = suggestFileName(value, formatId ? byId(formatId).value : ".mp4", "_output");
}

function suggestFileName(rawPath, extension, suffix) {
    const first = rawPath.split("; ")[0];
    const index = first.lastIndexOf(".");
    return index === -1 ? `${first}${suffix}${extension}` : `${first.slice(0, index)}${suffix}${extension}`;
}

async function prepareEditor(path) {
    const preview = byId("edit-preview");
    preview.removeAttribute("src");
    preview.load();
    byId("preview-empty").style.display = "grid";
    setSeekButtonsEnabled(false);
    setStatus("edit", "Analyzing clip...", "Inspecting codecs and preparing preview.", 8);
    try {
        const probe = await api("/api/probe", jsonOptions({ path }));
        state.editor.duration = probe.duration || 0;
        state.editor.startPercent = 0;
        state.editor.endPercent = 100;
        state.editor.activeHandle = "start";
        state.editor.controlTarget = "selection";
        byId("editor-insight").innerHTML = `
            <p class="info-label">Clip insight</p>
            <p class="info-value">${escapeHtml(probe.name)}</p>
            <p class="status-copy">${escapeHtml(probe.duration_label)} · ${escapeHtml(probe.video_codec)} · ${probe.audio_tracks} audio · ${probe.subtitle_tracks} subtitles · ${escapeHtml(probe.size_label)}</p>
        `;
        syncEditor(false);
        if (probe.preview_needed) {
            setStatus("edit", "Building preview proxy...", "This source needs a browser-friendly preview before editing.", 12);
            const job = await api("/api/previews", jsonOptions({ path }));
            registerJob("edit", job.job_id);
        } else {
            loadPreview(probe.media_url);
            setStatus("edit", "Preview ready", "Range controls are ready for trimming or cutting.", 0);
        }
    } catch (error) {
        setSeekButtonsEnabled(false);
        setStatus("edit", "Preview failed", error.message, 0, true);
    }
}

function loadPreview(url) {
    const preview = byId("edit-preview");
    preview.src = url;
    preview.load();
    byId("preview-empty").style.display = "none";
    setSeekButtonsEnabled(true);
    preview.addEventListener("loadedmetadata", () => {
        setPreviewCurrentTime(clampPreviewTime((state.editor.startPercent / 100) * (state.editor.duration || 0)));
        updateRangePlayhead(preview.currentTime);
    }, { once: true });
}

function syncEditor(previewTarget = null) {
    const duration = state.editor.duration || 0;
    const start = (state.editor.startPercent / 100) * duration;
    const end = (state.editor.endPercent / 100) * duration;
    const mode = byId("edit-mode").value;
    const selectionDuration = Math.max(end - start, 0);
    const displayedDuration = mode === "cut" ? Math.max(duration - selectionDuration, 0) : selectionDuration;
    const preview = byId("edit-preview");
    byId("edit-start-range").value = state.editor.startPercent;
    byId("edit-end-range").value = state.editor.endPercent;
    byId("edit-start-label").textContent = formatSeconds(start);
    byId("edit-end-label").textContent = formatSeconds(end);
    byId("edit-length-label").textContent = formatSeconds(displayedDuration);
    byId("range-selection").style.left = `${state.editor.startPercent}%`;
    byId("range-selection").style.width = `${state.editor.endPercent - state.editor.startPercent}%`;
    if (previewTarget && duration) {
        setPreviewCurrentTime(previewTarget === "end" ? end : start);
    } else if (duration) {
        setPreviewCurrentTime(clampPreviewTime(preview.currentTime || 0));
    }
    const currentTime = previewTarget === "end" ? end : previewTarget === "start" ? start : preview.currentTime || 0;
    updateRangePlayhead(currentTime);
}

async function runConvert() {
    try {
        const input_path = byId("conv-input").value;
        const output_path = byId("conv-output").value;
        const mode = byId("conv-mode").value;
        if (!input_path || !output_path) throw new Error("Choose both a source file and an output path.");
        const job = await api("/api/jobs/convert", jsonOptions({ input_path, output_path, mode }));
        registerJob("convert", job.job_id);
        setStatus("convert", "Conversion started", "FFmpeg is processing the export now.", 4);
    } catch (error) {
        setStatus("convert", "Missing inputs", error.message, 0, true);
    }
}

async function runMerge() {
    try {
        const videos = byId("merge-videos").value.split("; ").filter(Boolean);
        const output_path = byId("merge-output").value;
        if (!videos.length || !output_path) throw new Error("Choose at least one clip and an output path.");
        const payload = {
            videos,
            output_path,
            audio: byId("merge-audio").value || null,
            subtitle: byId("merge-subtitle").value || null,
        };
        const job = await api("/api/jobs/merge", jsonOptions(payload));
        registerJob("merge", job.job_id);
        setStatus("merge", "Merge started", "Your media is being stitched together.", 4);
    } catch (error) {
        setStatus("merge", "Missing inputs", error.message, 0, true);
    }
}

async function runExtract() {
    try {
        const input_path = byId("extract-input").value;
        if (!input_path) throw new Error("Choose a source file before extracting tracks.");
        const extract_type = byId("extract-type").value;
        const payload = {
            input_path,
            extract_type,
            output_dir: byId("extract-output").value || null,
            subtitle_format: extract_type === "subtitle" ? byId("extract-subtitle-format").value : null,
        };
        const job = await api("/api/jobs/extract", jsonOptions(payload));
        registerJob("extract", job.job_id);
        setStatus("extract", "Extraction started", "Track isolation is running.", 4);
    } catch (error) {
        setStatus("extract", "Missing input", error.message, 0, true);
    }
}

async function runEdit() {
    try {
        const input_path = byId("edit-input").value;
        const output_path = byId("edit-output").value;
        if (!input_path || !output_path || !state.editor.duration) throw new Error("Load a clip and choose an output path before exporting.");
        const payload = {
            input_path,
            output_path,
            mode: byId("edit-mode").value,
            start: (state.editor.startPercent / 100) * state.editor.duration,
            end: (state.editor.endPercent / 100) * state.editor.duration,
        };
        const job = await api("/api/jobs/edit", jsonOptions(payload));
        registerJob("edit", job.job_id);
        setStatus("edit", "Edit started", "Your clip is being rendered.", 4);
    } catch (error) {
        setStatus("edit", "Missing editor data", error.message, 0, true);
    }
}

function registerJob(tool, jobId) {
    state.liveJobs.set(jobId, tool);
    setActionButton(tool, jobId);
    refreshCurrentStatus();
}

async function pollJobs() {
    const entries = [...state.liveJobs.entries()];
    for (const [jobId, tool] of entries) {
        try {
            const snapshot = await api(`/api/jobs/${jobId}`);
            applySnapshot(tool, snapshot);
            if (["completed", "failed", "cancelled"].includes(snapshot.status)) {
                state.liveJobs.delete(jobId);
                setActionButton(tool, null);
                refreshCurrentStatus();
            }
        } catch {
            state.liveJobs.delete(jobId);
            setActionButton(tool, null);
        }
    }
}

function applySnapshot(tool, job) {
    setStatus(tool, job.title, job.message, job.progress, job.status === "failed" || job.status === "cancelled");
    renderArtifacts(tool, job.artifacts || []);
    renderCurrentStatus(job);
    if (tool === "edit" && job.kind === "preview" && job.status === "completed") {
        const media = (job.artifacts || []).find((item) => item.role === "media");
        if (media) {
            loadPreview(media.url);
            setStatus("edit", "Preview ready", "Proxy preview loaded. Range controls are ready.", 0);
        }
    }
}

function renderArtifacts(tool, artifacts) {
    byId(tools[tool].artifacts).innerHTML = artifacts.filter((item) => item.role === "download").map((item) => `
        <a class="artifact-link" href="${item.url}" target="_blank" rel="noreferrer">
            <span>${escapeHtml(item.label)}</span>
            <span>${escapeHtml(item.size_label)}</span>
        </a>
    `).join("");
}

function setActionButton(tool, jobId) {
    const button = byId(tools[tool].button);
    button.dataset.jobId = jobId || "";
    button.classList.toggle("cancel", Boolean(jobId));
    button.textContent = jobId ? "Cancel Job" : tools[tool].actionText;
}

function setStatus(tool, title, copy, progress, isError = false) {
    const root = byId(tools[tool].status);
    const safeProgress = clamp(Number(progress) || 0, 0, 100);
    root.querySelector(".status-title").textContent = title;
    root.querySelector(".status-copy").textContent = copy;
    byId(tools[tool].progress).style.width = `${safeProgress}%`;
    byId(tools[tool].label).textContent = formatProgress(safeProgress);
    root.dataset.error = isError ? "true" : "false";
}

function resetTool(tool) {
    if (tool === "convert") {
        ["conv-input", "conv-output"].forEach((id) => byId(id).value = "");
        byId("conv-format").selectedIndex = 0;
        byId("conv-mode").selectedIndex = 0;
    }
    if (tool === "merge") {
        ["merge-videos", "merge-audio", "merge-subtitle", "merge-output"].forEach((id) => byId(id).value = "");
        byId("merge-format").selectedIndex = 0;
    }
    if (tool === "extract") {
        ["extract-input", "extract-output"].forEach((id) => byId(id).value = "");
        byId("extract-type").selectedIndex = 0;
        byId("extract-subtitle-format").selectedIndex = 0;
        syncExtractOptions();
    }
    if (tool === "edit") {
        ["edit-input", "edit-output"].forEach((id) => byId(id).value = "");
        byId("edit-mode").selectedIndex = 0;
        byId("edit-preview").removeAttribute("src");
        byId("edit-preview").load();
        byId("preview-empty").style.display = "grid";
        byId("editor-insight").innerHTML = `<p class="info-label">Clip insight</p><p class="info-value">No media selected yet.</p>`;
        state.editor.duration = 0;
        state.editor.startPercent = 0;
        state.editor.endPercent = 100;
        state.editor.activeHandle = "start";
        state.editor.controlTarget = "selection";
        setSeekButtonsEnabled(false);
        syncEditor(false);
    }
    byId(tools[tool].artifacts).innerHTML = "";
    setStatus(tool, tools[tool].title, tools[tool].copy, 0);
    setActionButton(tool, null);
}

async function api(url, options = {}) {
    const response = await fetch(url, options);
    const isJson = (response.headers.get("content-type") || "").includes("application/json");
    const payload = isJson ? await response.json() : null;
    if (!response.ok) throw new Error(payload?.detail || "Something went wrong.");
    return payload;
}

function jsonOptions(payload) {
    return { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) };
}

function formatSeconds(seconds) {
    if (!Number.isFinite(seconds)) return "00:00:00";
    const totalHundredths = Math.max(Math.round(seconds * 100), 0);
    const minutes = Math.floor(totalHundredths / 6000);
    const secs = Math.floor((totalHundredths % 6000) / 100);
    const fraction = totalHundredths % 100;
    return `${String(minutes).padStart(2, "0")}:${String(secs).padStart(2, "0")}:${String(fraction).padStart(2, "0")}`;
}

function formatProgress(progress) {
    const value = clamp(Number(progress) || 0, 0, 100);
    const text = value % 1 === 0 ? String(value) : value.toFixed(1);
    return `${text}%`;
}

function seekPreviewBy(deltaMs) {
    const preview = byId("edit-preview");
    const duration = state.editor.duration || 0;
    if (!duration || !Number.isFinite(deltaMs)) return;
    if (state.editor.controlTarget === "playhead") {
        setPreviewCurrentTime(clampPreviewTime((preview.currentTime || 0) + (deltaMs / 1000)));
        updateRangePlayhead(preview.currentTime);
        return;
    }
    const deltaPercent = (deltaMs / 1000 / duration) * 100;
    if (state.editor.activeHandle === "end") {
        state.editor.endPercent = clamp(Math.max(state.editor.endPercent + deltaPercent, state.editor.startPercent + 0.2), 0.2, 100);
        syncEditor("end");
        return;
    }
    state.editor.startPercent = clamp(Math.min(state.editor.startPercent + deltaPercent, state.editor.endPercent - 0.2), 0, 99.8);
    syncEditor("start");
}

function updateRangePlayhead(currentTime) {
    const duration = state.editor.duration || 0;
    const percent = duration ? (clamp(currentTime, 0, duration) / duration) * 100 : 0;
    byId("range-playhead").style.left = `${percent}%`;
}

function setPreviewCurrentTime(time) {
    const preview = byId("edit-preview");
    if (!Number.isFinite(time)) return;
    if (Math.abs((preview.currentTime || 0) - time) <= 0.01) return;
    state.editor.syncingPreview = true;
    preview.currentTime = time;
}

function getEditorBounds() {
    const duration = state.editor.duration || 0;
    return {
        start: (state.editor.startPercent / 100) * duration,
        end: (state.editor.endPercent / 100) * duration,
    };
}

function clampPreviewTime(time) {
    const { start, end } = getEditorBounds();
    return clamp(time, start, end);
}

function setSeekButtonsEnabled(enabled) {
    document.querySelectorAll("[data-seek-ms]").forEach((button) => {
        button.disabled = !enabled;
    });
}

function clamp(value, min, max) {
    return Math.min(Math.max(value, min), max);
}

function isLiveStatus(status) {
    return ["queued", "running", "cancelling"].includes(status);
}

function capitalize(value) {
    const text = String(value || "");
    return text ? text.charAt(0).toUpperCase() + text.slice(1) : "Status";
}

function escapeHtml(value) {
    return String(value || "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
}

function showError(message) {
    if (state.currentRoute !== "home" && tools[state.currentRoute]) {
        setStatus(state.currentRoute, "Request failed", message, 0, true);
    }
    byId("current-status-title").textContent = "Request failed";
    byId("current-status-message").textContent = message;
    byId("current-status-progress").style.width = "0%";
    byId("current-status-percent").textContent = "0%";
    byId("current-status-kind").textContent = "Error";
    byId("current-status-log").textContent = "Fix the issue and try again.";
}
