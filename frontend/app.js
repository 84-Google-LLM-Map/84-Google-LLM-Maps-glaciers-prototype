const API = "";


/* =========================
   Configuration
   ========================= */

const YEARS = [2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024];

const DEFAULT_YEAR = "2019";

// Chart colours (overlay red matches the backend palette)
const COLOUR_FIRST = "#d9443a";
const COLOUR_SECOND = "#202124";
const COLOUR_OTHER = "#c4c9ce";

const OVERLAY_OPACITY = 0.8;

const glaciers = {

    "rob-roy": {
        name: "Rob Roy",
        centre: [-44.455, 168.741],
        zoom: 13
    },

    "marmolada": {
        name: "Marmolada",
        centre: [46.43522, 11.857975],
        zoom: 13
    },

    "aletsch": {
        name: "Aletsch",
        centre: [46.45424, 8.07374],
        zoom: 10
    },

    "rhone": {
        name: "Rhône",
        centre: [46.62, 8.40],
        zoom: 11
    },

    "mendenhall": {
        name: "Mendenhall",
        centre: [58.49583, -134.53222],
        zoom: 11
    },

    "franz-josef": {
        name: "Franz Josef",
        centre: [-43.475331, 170.199855],
        zoom: 11
    },

    "gangotri": {
        name: "Gangotri",
        centre: [30.82845, 79.17748],
        zoom: 10
    }
};


/* =========================
   Icons (map buttons + legend)
   ========================= */

const STROKE =
    'fill="none" stroke="currentColor" stroke-width="2" ' +
    'stroke-linecap="round" stroke-linejoin="round"';

const ICONS = {

    satellite:
        '<svg viewBox="0 0 24 24" aria-hidden="true">' +
        '<g transform="rotate(-45 12 12)">' +
        // solar panels with cell lines
        '<rect x="0.5" y="8" width="7.5" height="8" fill="currentColor"/>' +
        '<rect x="16" y="8" width="7.5" height="8" fill="currentColor"/>' +
        '<path d="M3 8v8M5.5 8v8M18.5 8v8M21 8v8M0.5 12h7.5M16 12h7.5" ' +
        'stroke="#fff" stroke-width=".7"/>' +
        // arms and body
        '<path d="M8 12h2M14 12h2" stroke="currentColor" stroke-width="1.4"/>' +
        '<rect x="10" y="8.5" width="4" height="7" rx=".8" fill="currentColor"/>' +
        // dish
        '<path d="M9.2 19.5a2.8 2.8 0 0 0 5.6 0Z" fill="currentColor"/>' +
        '<path d="M12 15.5v4" stroke="currentColor" stroke-width="1.2"/>' +
        '</g>' +
        '</svg>',

    hand:
        '<svg viewBox="0 0 24 24" aria-hidden="true" ' + STROKE + '>' +
        '<path d="M18 11V6a2 2 0 0 0-4 0"/>' +
        '<path d="M14 10V4a2 2 0 0 0-4 0v2"/>' +
        '<path d="M10 10.5V6a2 2 0 0 0-4 0v8"/>' +
        '<path d="M18 8a2 2 0 1 1 4 0v6a8 8 0 0 1-8 8h-2c-2.8 0-4.5-.86-6-2.34l-3.6-3.6a2 2 0 0 1 2.83-2.82L7 15"/>' +
        '</svg>',

    line:
        '<svg viewBox="0 0 24 24" aria-hidden="true" ' + STROKE + '>' +
        '<polyline points="3,7 10,17 21,6"/>' +
        '</svg>',

    rectangle:
        '<svg viewBox="0 0 24 24" aria-hidden="true">' +
        '<rect x="4" y="4" width="16" height="16" fill="currentColor"/>' +
        '</svg>',

    polygon:
        '<svg viewBox="0 0 24 24" aria-hidden="true" ' + STROKE + ' stroke-width="1.8">' +
        '<path d="M12 3.5 20.5 9.5 17.5 20h-11L3.5 9.5Z"/>' +
        '</svg>'
};

document.querySelectorAll("[data-icon]").forEach((element) => {
    element.innerHTML = ICONS[element.dataset.icon] || "";
});


/* =========================
   Elements
   ========================= */

const $ = (id) => document.getElementById(id);

const glacierSelect = $("glacier");
const glacierSubtitle = $("glacierSubtitle");

const yearSelect = $("year");
const secondYearSelect = $("secondYear");

const yearSlider = $("yearSlider");
const sliderYear = $("sliderYear");
const sliderEnabled = $("sliderEnabled");

const viewButton = $("view");
const viewSecondYearButton = $("viewSecondYear");
const analyseButton = $("analyse");

const status = $("status");
const warning = $("warning");

const resultGlacierName = $("resultGlacierName");

const firstMapLabel = $("first-map-label");
const secondMapLabel = $("second-map-label");
const secondMapContainer = $("second-map-container");

const coordSearch = $("coordSearch");
const coordInput = $("coordInput");
const experimentalResult = $("experimentalResult");

const a11yButton = $("a11yButton");
const a11yDialog = $("a11yDialog");


/* =========================
   State
   ========================= */

// glacierCache[glacierId][year] = API result
const glacierCache = {};
const pendingRequests = {};

let firstData = null;
let secondData = null;

let areaChart = null;

let firstOverlay = null;
let secondOverlay = null;

let secondMap = null;
let secondSatellite = null;
let secondStreets = null;

let selectedStudyArea = null;
let dynamicOverlay = null;


/* =========================
   Helpers
   ========================= */

function getSelectedGlacier() {
    return glacierSelect.value;
}

function getSelectedGlacierName() {
    return glacierSelect.selectedOptions[0].textContent.trim();
}

function isExperimentalMode() {
    return document.body.dataset.mode === "experimental";
}

function setStatus(message, isError = false) {
    status.className = isError ? "error" : "";
    status.textContent = message;
}

function formatArea(area) {
    return `${Number(area).toFixed(2)} km²`;
}

function setBusy(busy) {
    viewButton.disabled = busy;
    viewSecondYearButton.disabled = busy;
    analyseButton.disabled = busy;
}


/* =========================
   Year controls
   ========================= */

YEARS.forEach((year) => {
    yearSelect.add(new Option(year, year));
    secondYearSelect.add(new Option(year, year));
});

secondYearSelect.insertBefore(
    new Option("None", ""),
    secondYearSelect.firstChild
);

yearSelect.value = DEFAULT_YEAR;
secondYearSelect.value = "";

yearSlider.min = YEARS[0];
yearSlider.max = YEARS[YEARS.length - 1];
yearSlider.value = DEFAULT_YEAR;
sliderYear.textContent = DEFAULT_YEAR;

function setFirstYearControls(year) {
    yearSelect.value = String(year);
    yearSlider.value = String(year);
    sliderYear.textContent = String(year);
}


/* =========================
   Main map
   ========================= */

const satelliteUrl =
    "https://server.arcgisonline.com/ArcGIS/rest/services/" +
    "World_Imagery/MapServer/tile/{z}/{y}/{x}";

const streetsUrl =
    "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";

const map = L.map("map", {
    zoomControl: false
}).setView(
    glaciers["rob-roy"].centre,
    glaciers["rob-roy"].zoom
);

L.control.zoom({ position: "topleft" }).addTo(map);

const satelliteLayer = L.tileLayer(satelliteUrl, {
    maxZoom: 19,
    attribution: "Tiles © Esri"
}).addTo(map);

const streetsLayer = L.tileLayer(streetsUrl, {
    maxZoom: 19,
    attribution: "© OpenStreetMap contributors"
});

// Lines drawn in Experimental Explorer (annotations only)
const drawnLines = L.featureGroup().addTo(map);


/* =========================
   Satellite button
   ========================= */

let satelliteButton = null;

const SatelliteControl = L.Control.extend({

    options: { position: "topleft" },

    onAdd() {

        const bar = L.DomUtil.create("div", "leaflet-bar");
        const button = L.DomUtil.create("button", "map-btn satellite-btn", bar);

        button.type = "button";
        button.title = "Toggle satellite imagery";
        button.setAttribute("aria-label", "Toggle satellite imagery");
        button.setAttribute("aria-pressed", "true");
        button.innerHTML = ICONS.satellite;

        L.DomEvent.disableClickPropagation(bar);
        button.addEventListener("click", toggleBasemap);

        satelliteButton = button;
        return bar;
    }
});

new SatelliteControl().addTo(map);

function toggleBasemap() {

    const showSatellite = !map.hasLayer(satelliteLayer);

    swapBase(map, satelliteLayer, streetsLayer, showSatellite);

    if (secondMap) {
        swapBase(secondMap, secondSatellite, secondStreets, showSatellite);
    }

    satelliteButton.setAttribute("aria-pressed", String(showSatellite));
}

function swapBase(targetMap, satellite, streets, showSatellite) {

    const add = showSatellite ? satellite : streets;
    const remove = showSatellite ? streets : satellite;

    if (targetMap.hasLayer(remove)) {
        targetMap.removeLayer(remove);
    }

    add.addTo(targetMap);
    add.bringToBack();
}


/* =========================
   Drawing toolbar (Experimental Explorer)
   ========================= */

const DRAW_TOOLS = [
    { id: "move", label: "Stop drawing / move map", icon: "hand" },
    { id: "Line", label: "Draw line", icon: "line" },
    { id: "Rectangle", label: "Draw rectangle", icon: "rectangle" },
    { id: "Polygon", label: "Draw shape", icon: "polygon" }
];

const toolButtons = {};

const DrawToolbar = L.Control.extend({

    options: { position: "topright" },

    onAdd() {

        const bar = L.DomUtil.create("div", "leaflet-bar draw-toolbar experimental-only");

        DRAW_TOOLS.forEach((tool) => {

            const button = L.DomUtil.create("button", "map-btn", bar);

            button.type = "button";
            button.title = tool.label;
            button.setAttribute("aria-label", tool.label);
            button.innerHTML = ICONS[tool.icon];

            button.addEventListener("click", () => selectTool(tool.id));

            toolButtons[tool.id] = button;
        });

        L.DomEvent.disableClickPropagation(bar);
        L.DomEvent.disableScrollPropagation(bar);

        return bar;
    }
});

new DrawToolbar().addTo(map);

map.pm.setGlobalOptions({
    pathOptions: {
        color: "#111",
        weight: 2,
        fillColor: "#111",
        fillOpacity: 0.08
    }
});

function selectTool(toolId) {

    if (toolId === "move") {
        map.pm.disableDraw();
        setActiveTool("move");
        return;
    }

    map.pm.enableDraw(toolId);
    setActiveTool(toolId);
}

function setActiveTool(toolId) {

    Object.entries(toolButtons).forEach(([id, button]) => {
        const active = id === toolId;
        button.classList.toggle("is-active", active);
        button.setAttribute("aria-pressed", String(active));
    });
}

map.on("pm:drawstart", (event) => setActiveTool(event.shape));
map.on("pm:drawend", () => setActiveTool("move"));

setActiveTool("move");


/* =========================
   Fetching glacier data
   ========================= */

function fetchYear(glacierId, year) {

    year = Number(year);

    glacierCache[glacierId] = glacierCache[glacierId] || {};

    if (glacierCache[glacierId][year]) {
        return Promise.resolve(glacierCache[glacierId][year]);
    }

    const key = `${glacierId}:${year}`;

    if (!pendingRequests[key]) {

        pendingRequests[key] = fetch(
            `${API}/api/glacier/${year}?glacier=${encodeURIComponent(glacierId)}`
        )
            .then(async (response) => {

                const data = await response.json().catch(() => ({}));

                if (!response.ok || data.error) {
                    throw new Error(
                        data.error || `Request failed (${response.status})`
                    );
                }

                if (
                    !Number.isFinite(Number(data.area)) ||
                    typeof data.tileUrl !== "string"
                ) {
                    throw new Error("The backend returned incomplete analysis data.");
                }

                glacierCache[glacierId][year] = data;

                // Fill in the graph as each year arrives
                if (glacierId === getSelectedGlacier()) {
                    updateAreaChart();
                }

                return data;
            })
            .finally(() => {
                delete pendingRequests[key];
            });
    }

    return pendingRequests[key];
}

// Load the remaining years in the background for the graph
function preloadTimeline(glacierId) {

    YEARS.forEach((year) => {
        fetchYear(glacierId, year).catch((error) => {
            console.warn(`Could not load ${glacierId} ${year}:`, error);
        });
    });
}

function makeOverlay(data) {

    if (!data.tileUrl || Number(data.area) <= 0) {
        return null;
    }

    return L.tileLayer(data.tileUrl, {
        opacity: OVERLAY_OPACITY,
        maxZoom: 19
    });
}


/* =========================
   Results
   ========================= */

function fillCard(prefix, data) {

    $(`${prefix}Area`).textContent = formatArea(data.area);
    $(`${prefix}ResultYear`).textContent = data.year;
    $(`${prefix}Reference`).textContent = data.referenceYear;
    $(`${prefix}Threshold`).textContent = Number(data.threshold).toFixed(2);
}

function resetCard(prefix) {

    ["Area", "ResultYear", "Reference", "Threshold"].forEach((field) => {
        $(`${prefix}${field}`).textContent = "—";
    });
}

function showBackendWarning(data) {

    if (data && data.warning) {
        warning.textContent = data.warning;
        warning.hidden = false;
    } else {
        warning.hidden = true;
        warning.textContent = "";
    }
}


/* =========================
   Load first year
   ========================= */

async function loadYear(year) {

    const glacierId = getSelectedGlacier();
    const glacierName = getSelectedGlacierName();

    setFirstYearControls(year);
    firstMapLabel.textContent = year;

    setStatus(`Loading ${glacierName} for ${year}…`);
    setBusy(true);

    try {

        const data = await fetchYear(glacierId, year);

        // The user switched glacier while this was loading
        if (glacierId !== getSelectedGlacier()) {
            return null;
        }

        if (firstOverlay) {
            map.removeLayer(firstOverlay);
        }

        firstOverlay = makeOverlay(data);

        if (firstOverlay) {
            firstOverlay.addTo(map);
        }

        firstData = data;

        fillCard("first", data);
        showBackendWarning(data);
        updateAreaChart();

        setStatus(
            Number(data.area) === 0
                ? `${glacierName} — ${year}: no glacier-like area detected.`
                : `${glacierName} — ${year}: ${formatArea(data.area)} glacier-like area detected.`
        );

        return data;

    } catch (error) {

        console.error(error);
        setStatus(`Unable to load ${year}: ${error.message}`, true);
        return null;

    } finally {

        setBusy(false);
    }
}


/* =========================
   Second map
   ========================= */

let syncingMaps = false;

function syncMaps(source, target) {

    if (syncingMaps || !target) {
        return;
    }

    syncingMaps = true;

    target.setView(
        source.getCenter(),
        source.getZoom(),
        { animate: false }
    );

    syncingMaps = false;
}

map.on("move", () => syncMaps(map, secondMap));

function createSecondMap() {

    if (secondMap) {
        return;
    }

    secondMap = L.map("secondMap", {
        zoomControl: false
    }).setView(
        map.getCenter(),
        map.getZoom()
    );

    secondSatellite = L.tileLayer(satelliteUrl, {
        maxZoom: 19,
        attribution: "Tiles © Esri"
    });

    secondStreets = L.tileLayer(streetsUrl, {
        maxZoom: 19,
        attribution: "© OpenStreetMap contributors"
    });

    (map.hasLayer(satelliteLayer) ? secondSatellite : secondStreets)
        .addTo(secondMap);

    secondMap.on("move", () => syncMaps(secondMap, map));
}

function resizeMaps() {

    setTimeout(() => {
        map.invalidateSize();
        if (secondMap) {
            secondMap.invalidateSize();
        }
    }, 100);
}

function closeSecondMap() {

    secondMapContainer.hidden = true;

    if (secondOverlay && secondMap) {
        secondMap.removeLayer(secondOverlay);
    }

    secondOverlay = null;
    secondData = null;

    resetCard("second");
    updateAreaChart();
    resizeMaps();
}


/* =========================
   Load second year
   ========================= */

async function loadSecondYear(year) {

    const glacierId = getSelectedGlacier();
    const glacierName = getSelectedGlacierName();

    setStatus(`Loading second year ${year}…`);
    setBusy(true);

    try {

        const data = await fetchYear(glacierId, year);

        if (glacierId !== getSelectedGlacier()) {
            return null;
        }

        secondMapContainer.hidden = false;
        createSecondMap();
        resizeMaps();

        if (secondOverlay) {
            secondMap.removeLayer(secondOverlay);
        }

        secondOverlay = makeOverlay(data);

        if (secondOverlay) {
            secondOverlay.addTo(secondMap);
        }

        secondData = data;

        fillCard("second", data);
        secondMapLabel.textContent = data.year;
        updateAreaChart();

        setStatus(
            `${glacierName} — ${year}: ${formatArea(data.area)} glacier-like area detected.`
        );

        return data;

    } catch (error) {

        console.error(error);
        setStatus(`Unable to load ${year}: ${error.message}`, true);
        return null;

    } finally {

        setBusy(false);
    }
}


/* =========================
   Area chart (2017–2024)
   ========================= */

function updateAreaChart() {

    const canvas = $("areaChart");

    if (!canvas || typeof Chart === "undefined") {
        return;
    }

    const timeline = glacierCache[getSelectedGlacier()] || {};

    const areas = YEARS.map((year) => {
        const data = timeline[year];
        return data ? Number(data.area) : null;
    });

    const firstYear = firstData ? Number(firstData.year) : null;
    const secondYear = secondData ? Number(secondData.year) : null;

    const colours = YEARS.map((year) => {
        if (year === firstYear) return COLOUR_FIRST;
        if (year === secondYear) return COLOUR_SECOND;
        return COLOUR_OTHER;
    });

    if (areaChart) {
        areaChart.data.datasets[0].data = areas;
        areaChart.data.datasets[0].backgroundColor = colours;
        areaChart.update("none");
        return;
    }

    areaChart = new Chart(canvas, {
        type: "bar",

        data: {
            labels: YEARS,
            datasets: [{
                label: "Glacier-like area (km²)",
                data: areas,
                backgroundColor: colours,
                borderRadius: 2,
                maxBarThickness: 34
            }]
        },

        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,

            plugins: {
                legend: { display: false },

                tooltip: {
                    callbacks: {
                        label: (context) => formatArea(context.parsed.y)
                    }
                }
            },

            scales: {
                x: {
                    grid: { display: false },
                    title: { display: true, text: "Year" }
                },

                y: {
                    beginAtZero: true,
                    title: { display: true, text: "Area (km²)" },
                    ticks: { callback: (value) => `${value}` }
                }
            }
        }
    });
}


/* =========================
   Experimental analysis
   ========================= */

function clearExperimental() {

    map.pm.disableDraw();
    setActiveTool("move");

    if (selectedStudyArea) {
        map.removeLayer(selectedStudyArea);
        selectedStudyArea = null;
    }

    if (dynamicOverlay) {
        map.removeLayer(dynamicOverlay);
        dynamicOverlay = null;
    }

    drawnLines.clearLayers();

    experimentalResult.hidden = true;
    experimentalResult.textContent = "";
}

map.on("pm:create", (event) => {

    // Lines are annotations, not study areas
    if (event.shape === "Line") {
        drawnLines.addLayer(event.layer);
        return;
    }

    if (selectedStudyArea && selectedStudyArea !== event.layer) {
        map.removeLayer(selectedStudyArea);
    }

    selectedStudyArea = event.layer;

    runExperimentalAnalysis();
});

async function runExperimentalAnalysis() {

    if (!selectedStudyArea) {
        setStatus(
            "Draw a rectangle or shape on the map first.",
            true
        );
        return;
    }

    if (dynamicOverlay) {
        map.removeLayer(dynamicOverlay);
        dynamicOverlay = null;
    }

    const year = Number(yearSelect.value);

    setStatus(`Running experimental analysis for ${year}…`);
    experimentalResult.hidden = true;
    setBusy(true);

    try {

        const response = await fetch(
            `${API}/api/automatic-reference-analysis`,
            {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    geometry: selectedStudyArea.toGeoJSON().geometry,
                    year: year,
                    glacier: getSelectedGlacier()
                })
            }
        );

        const data = await response.json().catch(() => ({}));

        if (!response.ok || data.error) {
            throw new Error(data.error || "Experimental analysis failed.");
        }

        if (data.tileUrl && Number(data.area) > 0) {
            dynamicOverlay = L.tileLayer(data.tileUrl, {
                opacity: OVERLAY_OPACITY,
                maxZoom: 19
            }).addTo(map);
        }

        const message =
            Number(data.area) === 0
                ? `${year}: no glacier-like area inside the drawn area.`
                : `${year}: ${formatArea(data.area)} glacier-like area inside the drawn area.`;

        experimentalResult.textContent = message;
        experimentalResult.hidden = false;

        setStatus(`Experimental analysis — ${message}`);

        console.log("Experimental analysis:", data);

    } catch (error) {

        console.error(error);
        setStatus(`Experimental analysis failed: ${error.message}`, true);

    } finally {

        setBusy(false);
    }
}


/* =========================
   Coordinate search
   ========================= */

coordSearch.addEventListener("submit", (event) => {

    event.preventDefault();

    const text = coordInput.value.trim();

    // Empty search: zoom to the drawn area
    if (!text) {

        if (selectedStudyArea) {
            map.fitBounds(selectedStudyArea.getBounds(), { padding: [40, 40] });
        } else {
            setStatus(
                "Enter coordinates as latitude, longitude, or draw a shape first.",
                true
            );
        }

        return;
    }

    const match = text.match(
        /^\s*(-?\d+(?:\.\d+)?)\s*[,\s]\s*(-?\d+(?:\.\d+)?)\s*$/
    );

    const lat = match ? Number(match[1]) : NaN;
    const lng = match ? Number(match[2]) : NaN;

    if (
        !Number.isFinite(lat) || !Number.isFinite(lng) ||
        Math.abs(lat) > 90 || Math.abs(lng) > 180
    ) {
        setStatus(
            "Enter coordinates as latitude, longitude — for example -44.455, 168.741.",
            true
        );
        return;
    }

    map.setView([lat, lng], Math.max(map.getZoom(), 12));
    setStatus(`Moved to ${lat.toFixed(4)}, ${lng.toFixed(4)}.`);
});


/* =========================
   Explorer / Experimental mode
   ========================= */

const modeTabs = document.querySelectorAll(".mode-tab");

function getModeFromHash() {
    return location.hash === "#experimental" ? "experimental" : "explorer";
}

function setMode(mode) {

    document.body.dataset.mode = mode;

    modeTabs.forEach((tab) => {
        const active = tab.dataset.mode === mode;
        tab.classList.toggle("is-active", active);

        if (active) {
            tab.setAttribute("aria-current", "page");
        } else {
            tab.removeAttribute("aria-current");
        }
    });

    if (mode === "explorer") {
        clearExperimental();
        setStatus("Select a year and click View Year or Analyse Glacier.");
    } else {
        setStatus("Draw a rectangle or shape on the map to run the experimental analysis.");
    }

    resizeMaps();
}

// The tabs are links; the back button and shared links work too
window.addEventListener("hashchange", () => setMode(getModeFromHash()));


/* =========================
   Main controls
   ========================= */

viewButton.addEventListener("click", () => {
    loadYear(yearSelect.value);
});

viewSecondYearButton.addEventListener("click", () => {

    if (!secondYearSelect.value) {
        setStatus("Select a second year first.", true);
        return;
    }

    loadSecondYear(secondYearSelect.value);
});

secondYearSelect.addEventListener("change", () => {
    if (!secondYearSelect.value) {
        closeSecondMap();
    }
});

analyseButton.addEventListener("click", async () => {

    // Experimental Explorer: re-run on the drawn area
    if (isExperimentalMode() && selectedStudyArea) {
        runExperimentalAnalysis();
        return;
    }

    await loadYear(yearSelect.value);

    if (secondYearSelect.value) {
        await loadSecondYear(secondYearSelect.value);
    } else {
        closeSecondMap();
    }
});

yearSelect.addEventListener("change", () => {
    yearSlider.value = yearSelect.value;
    sliderYear.textContent = yearSelect.value;
});


/* =========================
   Timeline slider
   ========================= */

function applySliderEnabled() {
    yearSlider.disabled = !sliderEnabled.checked;
    yearSlider
        .closest(".timeline-section")
        .classList.toggle("is-disabled", !sliderEnabled.checked);
}

sliderEnabled.addEventListener("change", applySliderEnabled);
applySliderEnabled();

yearSlider.addEventListener("input", () => {
    sliderYear.textContent = yearSlider.value;
    yearSelect.value = yearSlider.value;
});

yearSlider.addEventListener("change", () => {

    // Return to the single-map view while scrubbing
    closeSecondMap();
    secondYearSelect.value = "";

    loadYear(yearSlider.value);
});


/* =========================
   Glacier selection
   ========================= */

glacierSelect.addEventListener("change", async () => {

    const glacierId = getSelectedGlacier();
    const glacier = glaciers[glacierId];
    const glacierName = getSelectedGlacierName();

    if (firstOverlay) {
        map.removeLayer(firstOverlay);
        firstOverlay = null;
    }

    clearExperimental();

    firstData = null;
    resetCard("first");
    closeSecondMap();
    secondYearSelect.value = "";

    glacierSubtitle.textContent = glacierName;
    resultGlacierName.textContent = glacierName;

    map.setView(glacier.centre, glacier.zoom);

    updateAreaChart();

    await loadYear(yearSelect.value);
    preloadTimeline(glacierId);
});


/* =========================
   Accessibility settings
   ========================= */

const A11Y_STORAGE_KEY = "glacier-explorer-a11y";

const A11Y_CLASSES = {
    largeText: "a11y-large-text",
    highContrast: "a11y-high-contrast",
    reduceMotion: "a11y-reduce-motion"
};

function loadA11ySettings() {
    try {
        return JSON.parse(localStorage.getItem(A11Y_STORAGE_KEY)) || {};
    } catch (error) {
        return {};
    }
}

function saveA11ySettings(settings) {
    try {
        localStorage.setItem(A11Y_STORAGE_KEY, JSON.stringify(settings));
    } catch (error) {
        // Storage unavailable (private window etc.) — settings last this visit only
    }
}

function applyA11ySettings(settings) {

    Object.entries(A11Y_CLASSES).forEach(([key, className]) => {
        document.documentElement.classList.toggle(className, Boolean(settings[key]));
    });

    resizeMaps();

    if (areaChart) {
        areaChart.resize();
    }
}

const a11ySettings = loadA11ySettings();

a11yDialog.querySelectorAll("[data-a11y]").forEach((checkbox) => {

    checkbox.checked = Boolean(a11ySettings[checkbox.dataset.a11y]);

    checkbox.addEventListener("change", () => {
        a11ySettings[checkbox.dataset.a11y] = checkbox.checked;
        applyA11ySettings(a11ySettings);
        saveA11ySettings(a11ySettings);
    });
});

applyA11ySettings(a11ySettings);

a11yButton.addEventListener("click", () => {
    a11yDialog.showModal();
});


/* =========================
   Initial page load
   ========================= */

setMode(getModeFromHash());

glacierSubtitle.textContent = getSelectedGlacierName();
resultGlacierName.textContent = getSelectedGlacierName();

loadYear(yearSelect.value).then(() => {
    preloadTimeline(getSelectedGlacier());
});
