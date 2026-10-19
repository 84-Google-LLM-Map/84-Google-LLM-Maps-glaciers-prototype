const API = "";


// Glacier locations
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


// Page elements
const glacierSelect = document.getElementById("glacier");

const yearSelect = document.getElementById("year");
const secondYearSelect = document.getElementById("secondYear");

const yearSlider = document.getElementById("yearSlider");
const sliderYear = document.getElementById("sliderYear");

const viewButton = document.getElementById("view");
const viewSecondYearButton = document.getElementById("viewSecondYear");

const status = document.getElementById("status");
const warning = document.getElementById("warning");

const resultsSection = document.getElementById("resultsSection");

const firstResultCard = document.getElementById("firstResultCard");
const secondResultCard = document.getElementById("secondResultCard");

const firstResultYear = document.getElementById("firstResultYear");
const firstArea = document.getElementById("firstArea");
const firstReference = document.getElementById("firstReference");
const firstThreshold = document.getElementById("firstThreshold");

const secondResultYear = document.getElementById("secondResultYear");
const secondArea = document.getElementById("secondArea");
const secondReference = document.getElementById("secondReference");
const secondThreshold = document.getElementById("secondThreshold");

const firstMapLabel = document.getElementById("first-map-label");
const secondMapLabel = document.getElementById("second-map-label");
const secondMapContainer = document.getElementById("second-map-container");


// Cache
const glacierCache = {};


// Year options
for (let year = 2017; year <= 2024; year++) {
    yearSelect.add(new Option(year, year));
    secondYearSelect.add(new Option(year, year));
}

// Default year
yearSelect.value = "2019";

secondYearSelect.insertBefore(
    new Option("None", ""),
    secondYearSelect.firstChild
);

secondYearSelect.value = "";

yearSlider.value = "2019";
sliderYear.textContent = "2019";


// Main map
const map = L.map("map").setView(
    glaciers["rob-roy"].centre,
    glaciers["rob-roy"].zoom
);

let secondMap = null;
let secondSatellite = null;

const satellite = L.tileLayer(
    "https://server.arcgisonline.com/ArcGIS/rest/services/" +
    "World_Imagery/MapServer/tile/{z}/{y}/{x}",
    {
        attribution: "Tiles &copy; Esri",
        maxZoom: 19
    }
).addTo(map);

const streets = L.tileLayer(
    "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    {
        attribution: "&copy; OpenStreetMap contributors",
        maxZoom: 19
    }
);

L.control.layers({
    Satellite: satellite,
    Streets: streets
}).addTo(map);

let firstOverlay = null;
let secondOverlay = null;


// Clear results
function clearResult() {

    if (firstOverlay) {
        map.removeLayer(firstOverlay);
        firstOverlay = null;
    }

    if (secondOverlay && secondMap) {
        secondMap.removeLayer(secondOverlay);
        secondOverlay = null;
    }

    resultsSection.hidden = true;

    firstResultCard.hidden = false;
    secondResultCard.hidden = true;

    firstResultYear.textContent = "—";
    firstArea.textContent = "—";
    firstReference.textContent = "—";
    firstThreshold.textContent = "—";

    secondResultYear.textContent = "—";
    secondArea.textContent = "—";
    secondReference.textContent = "—";
    secondThreshold.textContent = "—";

    warning.hidden = true;
    warning.textContent = "";

    status.className = "";
}


// Demo warning
function showDemoWarning() {

    if (glacierSelect.value === "marmolada") {
        warning.textContent =
            "Demo only: Marmolada currently uses an artificial, " +
            "unverified reference polygon. Results require Applied " +
            "Science review and are not validated glacier measurements.";

        warning.hidden = false;
    }
}


// Loading state
function setBusy(busy) {
    glacierSelect.disabled = busy;
    yearSlider.disabled = busy;
}


// Cache glacier timeline
async function preloadGlacier(glacierId) {

    if (glacierCache[glacierId]) {
        return;
    }

    glacierCache[glacierId] = {};

    const years = [
        2017, 2018, 2019, 2020,
        2021, 2022, 2023, 2024
    ];

    const requests = years.map(async (year) => {

        try {

            const response = await fetch(
                `${API}/api/glacier/${year}?glacier=${glacierId}`
            );

            const data = await response.json();

            if (!response.ok || data.error) {
                throw new Error(
                    data.error || `Could not load ${year}`
                );
            }

            glacierCache[glacierId][year] = data;

            console.log(`${glacierId} ${year} cached`);

        } catch (error) {

            console.error(
                `Could not cache ${glacierId} ${year}:`,
                error
            );
        }

    });

    await Promise.all(requests);

    console.log(`${glacierId} timeline cached`);
}


// Load a year
async function loadYear(year, isSecondYear = false) {

    const glacierId = glacierSelect.value;
    const selected = glaciers[glacierId];

    setBusy(true);

    map.setView(
        selected.centre,
        selected.zoom
    );

    status.className = "";
    status.textContent =
        `Loading ${selected.name} for ${year}…`;

    try {

        await preloadGlacier(glacierId);

        const data = glacierCache[glacierId][year];

        if (!data) {
            throw new Error(
                `Could not load ${selected.name} for ${year}`
            );
        }

        // Check glacier
        if (data.glacierId !== glacierId) {
            throw new Error(
                "The backend returned the wrong glacier."
            );
        }

        // Validate data
        if (
            !Number.isFinite(data.area) ||
            data.area < 0 ||
            typeof data.tileUrl !== "string"
        ) {
            throw new Error(
                "The backend returned incomplete analysis data."
            );
        }

        // Backend warning
        if (data.warning) {
            warning.textContent = data.warning;
            warning.hidden = false;
        }

        // Glacier overlay
        const newOverlay = L.tileLayer(data.tileUrl, {
            opacity: 0.75,
            maxZoom: 19
        });


        if (isSecondYear) {

            // Replace second overlay
            if (secondOverlay && secondMap) {
                secondMap.removeLayer(secondOverlay);
                secondOverlay = null;
            }

            secondOverlay = newOverlay;
            secondOverlay.addTo(secondMap);

            // Second-year result
            secondResultCard.hidden = false;

            secondResultYear.textContent = year;
            secondArea.textContent =
                `${data.area.toFixed(2)} km²`;
            secondReference.textContent =
                data.referenceYear;
            secondThreshold.textContent =
                Number(data.threshold).toFixed(2);

        } else {

            // Replace first overlay
            if (firstOverlay) {
                map.removeLayer(firstOverlay);
            }

            firstOverlay = newOverlay;
            firstOverlay.addTo(map);

            // First-year result
            firstResultCard.hidden = false;

            firstResultYear.textContent = year;
            firstArea.textContent =
                `${data.area.toFixed(2)} km²`;
            firstReference.textContent =
                data.referenceYear;
            firstThreshold.textContent =
                Number(data.threshold).toFixed(2);
        }

        resultsSection.hidden = false;

        status.textContent =
            `${selected.name}, ${year}: ` +
            "analysis and overlay loaded.";

        return data;

    } catch (error) {

        console.error(error);

        status.className = "error";
        status.textContent =
            `Could not load glacier data: ${error.message}`;

        return null;

    } finally {

        setBusy(false);
    }
}


// Create second map
function createSecondMap() {

    if (secondMap) {
        return;
    }

    const selected = glaciers[glacierSelect.value];

    secondMap = L.map("secondMap", {
        zoomControl: false,
        attributionControl: false
    }).setView(
        selected.centre,
        selected.zoom
    );

    secondSatellite = L.tileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/" +
        "World_Imagery/MapServer/tile/{z}/{y}/{x}",
        {
            attribution: "Tiles &copy; Esri",
            maxZoom: 19
        }
    ).addTo(secondMap);
}


// Close second map
function closeSecondMap() {

    secondMapContainer.hidden = true;

    if (secondOverlay && secondMap) {
        secondMap.removeLayer(secondOverlay);
        secondOverlay = null;
    }

    secondYearSelect.value = "";
    secondResultCard.hidden = true;

    // Resize main map
    setTimeout(() => {
        map.invalidateSize();
    }, 0);
}


// Change glacier
glacierSelect.addEventListener("change", () => {

    clearResult();
    closeSecondMap();

    const selected = glaciers[glacierSelect.value];

    map.setView(
        selected.centre,
        selected.zoom
    );

    showDemoWarning();

    status.textContent =
        "Select a year and click View Year.";
});


// Change first year
yearSelect.addEventListener("change", () => {

    clearResult();
    showDemoWarning();

    status.textContent =
        "Click View Year to analyse the selected year.";
});


// Timeline
yearSlider.value = yearSelect.value;
sliderYear.textContent = yearSelect.value;

yearSlider.addEventListener("input", () => {

    const year = yearSlider.value;

    sliderYear.textContent = year;
    yearSelect.value = year;
});

yearSlider.addEventListener("change", async () => {

    const year = yearSlider.value;

    clearResult();
    closeSecondMap();

    yearSelect.value = year;
    firstMapLabel.textContent = year;

    showDemoWarning();

    await loadYear(year, false);
});


// View first year
viewButton.addEventListener("click", async () => {

    const year = yearSelect.value;

    firstMapLabel.textContent = year;

    clearResult();
    showDemoWarning();

    await loadYear(year, false);
});


// Second year
secondYearSelect.addEventListener("change", () => {

    if (!secondYearSelect.value) {
        closeSecondMap();
    }
});

viewSecondYearButton.addEventListener("click", async () => {

    const year = secondYearSelect.value;

    if (!year) {
        status.textContent =
            "Select a second year first.";
        return;
    }

    secondMapContainer.hidden = false;
    secondMapLabel.textContent = year;

    createSecondMap();

    setTimeout(() => {
        map.invalidateSize();
        secondMap.invalidateSize();
    }, 0);

    showDemoWarning();

    await loadYear(year, true);
});


// Keep maps aligned
map.on("move", () => {

    if (!secondMap) {
        return;
    }

    secondMap.setView(
        map.getCenter(),
        map.getZoom(),
        { animate: false }
    );
});


// Load initial year
loadYear(yearSelect.value, false);
