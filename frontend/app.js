const API = "http://127.0.0.1:5000";


/* =========================
   Glacier configuration
   ========================= */

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
    }
};


/* =========================
   Elements
   ========================= */

const glacierSelect = document.getElementById("glacier");

const yearSelect = document.getElementById("year");
const secondYearSelect = document.getElementById("secondYear");

const yearSlider = document.getElementById("yearSlider");
const sliderYear = document.getElementById("sliderYear");

const viewButton = document.getElementById("view");
const viewSecondYearButton =
    document.getElementById("viewSecondYear");

const status = document.getElementById("status");
const warning = document.getElementById("warning");

const resultsSection =
    document.getElementById("resultsSection");

const firstResultYear =
    document.getElementById("firstResultYear");

const firstArea =
    document.getElementById("firstArea");

const firstReference =
    document.getElementById("firstReference");

const firstThreshold =
    document.getElementById("firstThreshold");

const secondResultCard =
    document.getElementById("secondResultCard");

const secondResultYear =
    document.getElementById("secondResultYear");

const secondArea =
    document.getElementById("secondArea");

const secondReference =
    document.getElementById("secondReference");

const secondThreshold =
    document.getElementById("secondThreshold");

const firstMapLabel =
    document.getElementById("first-map-label");

const secondMapLabel =
    document.getElementById("second-map-label");

const secondMapContainer =
    document.getElementById("second-map-container");


/* =========================
   Populate year selectors
   ========================= */

for (let year = 2017; year <= 2024; year++) {

    const option = document.createElement("option");

    option.value = year;
    option.textContent = year;

    yearSelect.appendChild(option);


    const secondOption =
        document.createElement("option");

    secondOption.value = year;
    secondOption.textContent = year;

    secondYearSelect.appendChild(secondOption);
}

yearSelect.value = "2019";
secondYearSelect.value = "2024";


/* =========================
   Main map
   ========================= */

const map = L.map("map").setView(
    glaciers["rob-roy"].centre,
    glaciers["rob-roy"].zoom
);


/* =========================
   Base layers
   ========================= */

const satelliteLayer = L.tileLayer(
    "https://server.arcgisonline.com/ArcGIS/rest/services/" +
    "World_Imagery/MapServer/tile/{z}/{y}/{x}",
    {
        maxZoom: 19,
        attribution:
            "Tiles © Esri"
    }
);

const osmLayer = L.tileLayer(
    "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    {
        maxZoom: 19,
        attribution:
            "© OpenStreetMap contributors"
    }
);

satelliteLayer.addTo(map);

L.control.layers(
    {
        "Satellite": satelliteLayer,
        "OpenStreetMap": osmLayer
    }
).addTo(map);


/* =========================
   Geoman drawing controls
   ========================= */

map.pm.addControls({
    position: "topleft",

    drawMarker: false,
    drawCircleMarker: false,
    drawPolyline: false,
    drawCircle: false,

    drawRectangle: true,
    drawPolygon: true,

    editMode: true,
    dragMode: false,
    cutPolygon: false,
    removalMode: true
});


/* =========================
   Map layers
   ========================= */

let firstOverlay = null;
let secondOverlay = null;

let secondMap = null;
let secondSatelliteLayer = null;


/* =========================
   Experimental analysis
   ========================= */

let selectedStudyArea = null;
let dynamicOverlay = null;


/* =========================
   Get glacier
   ========================= */

function getSelectedGlacier() {

    return glacierSelect.value;
}


/* =========================
   Move map to glacier
   ========================= */

function moveToSelectedGlacier() {

    const glacierId =
        getSelectedGlacier();

    const glacier =
        glaciers[glacierId];

    map.setView(
        glacier.centre,
        glacier.zoom
    );

    if (secondMap) {

        secondMap.setView(
            glacier.centre,
            glacier.zoom
        );
    }
}


/* =========================
   Get glacier data
   ========================= */

async function getGlacierData(year) {

    const glacierId =
        getSelectedGlacier();

    const response = await fetch(
        `${API}/api/glacier/${year}?glacier=${glacierId}`
    );

    const data =
        await response.json();

    if (!response.ok || data.error) {

        throw new Error(
            data.error ||
            "Glacier analysis failed."
        );
    }

    return data;
}


/* =========================
   Load first year
   ========================= */

async function loadYear(year, updateMap = true) {

    status.className = "";

    status.textContent =
        `Loading ${year} glacier analysis…`;

    viewButton.disabled = true;

    try {

        const data =
            await getGlacierData(year);


        /* Remove old first-year overlay */

        if (firstOverlay) {

            map.removeLayer(
                firstOverlay
            );

            firstOverlay = null;
        }


        /* Add new first-year overlay */

        if (
            data.tileUrl &&
            Number(data.area) > 0
        ) {

            firstOverlay =
                L.tileLayer(
                    data.tileUrl,
                    {
                        opacity: 0.7,
                        maxZoom: 19
                    }
                );

            firstOverlay.addTo(map);
        }


        /* Update results */

        resultsSection.hidden = false;

        firstResultYear.textContent =
            data.year;

        firstArea.textContent =
            `${Number(data.area).toFixed(2)} km²`;

        firstReference.textContent =
            data.referenceYear;

        firstThreshold.textContent =
            Number(data.threshold).toFixed(2);

        firstMapLabel.textContent =
            data.year;


        /* Warning */

        if (data.warning) {

            warning.hidden = false;
            warning.textContent =
                data.warning;

        } else {

            warning.hidden = true;
            warning.textContent = "";
        }


        /* Status */

        if (Number(data.area) === 0) {

            status.textContent =
                `No glacier-like area was detected for ${year}.`;

        } else {

            status.textContent =
                `${data.glacier || "Glacier"} — ${year}: ` +
                `${Number(data.area).toFixed(2)} km² ` +
                `glacier-like area detected.`;
        }


        /* Move map if requested */

        if (updateMap) {

            moveToSelectedGlacier();
        }


        return data;

    } catch (error) {

        console.error(error);

        status.className = "error";

        status.textContent =
            `Unable to load ${year}: ${error.message}`;

        return null;

    } finally {

        viewButton.disabled = false;
    }
}


/* =========================
   Create second map
   ========================= */

function createSecondMap() {

    if (secondMap) {
        return;
    }

    const glacier =
        glaciers[getSelectedGlacier()];

    secondMap = L.map(
        "secondMap",
        {
            zoomControl: true
        }
    ).setView(
        glacier.centre,
        map.getZoom()
    );


    secondSatelliteLayer =
        L.tileLayer(
            "https://server.arcgisonline.com/ArcGIS/rest/services/" +
            "World_Imagery/MapServer/tile/{z}/{y}/{x}",
            {
                maxZoom: 19,
                attribution:
                    "Tiles © Esri"
            }
        );

    secondSatelliteLayer.addTo(
        secondMap
    );


    /* Keep maps synchronised */

    map.on("move", function () {

        if (!secondMap) {
            return;
        }

        const centre =
            map.getCenter();

        const zoom =
            map.getZoom();

        if (
            secondMap.getZoom() !== zoom ||
            !secondMap
                .getCenter()
                .equals(centre)
        ) {

            secondMap.setView(
                centre,
                zoom,
                {
                    animate: false
                }
            );
        }
    });


    secondMap.on(
        "move",
        function () {

            const centre =
                secondMap.getCenter();

            const zoom =
                secondMap.getZoom();

            if (
                map.getZoom() !== zoom ||
                !map
                    .getCenter()
                    .equals(centre)
            ) {

                map.setView(
                    centre,
                    zoom,
                    {
                        animate: false
                    }
                );
            }
        }
    );
}


/* =========================
   Load second year
   ========================= */

async function loadSecondYear(year) {

    status.className = "";

    status.textContent =
        `Loading second year ${year}…`;

    viewSecondYearButton.disabled =
        true;

    try {

        const data =
            await getGlacierData(year);


        /* Show second map */

        secondMapContainer.hidden =
            false;

        createSecondMap();


        /* Leaflet needs resize */

        setTimeout(() => {

            map.invalidateSize();

            secondMap.invalidateSize();

        }, 100);


        /* Remove previous overlay */

        if (secondOverlay) {

            secondMap.removeLayer(
                secondOverlay
            );

            secondOverlay = null;
        }


        /* Add second overlay */

        if (
            data.tileUrl &&
            Number(data.area) > 0
        ) {

            secondOverlay =
                L.tileLayer(
                    data.tileUrl,
                    {
                        opacity: 0.7,
                        maxZoom: 19
                    }
                );

            secondOverlay.addTo(
                secondMap
            );
        }


        /* Results */

        resultsSection.hidden = false;
        secondResultCard.hidden = false;

        secondResultYear.textContent =
            data.year;

        secondArea.textContent =
            `${Number(data.area).toFixed(2)} km²`;

        secondReference.textContent =
            data.referenceYear;

        secondThreshold.textContent =
            Number(data.threshold).toFixed(2);

        secondMapLabel.textContent =
            data.year;


        status.textContent =
            `${data.glacier || "Glacier"} — ${year}: ` +
            `${Number(data.area).toFixed(2)} km² ` +
            `glacier-like area detected.`;

    } catch (error) {

        console.error(error);

        status.className = "error";

        status.textContent =
            `Unable to load ${year}: ${error.message}`;

    } finally {

        viewSecondYearButton.disabled =
            false;
    }
}


/* =========================
   Experimental dynamic
   area analysis
   ========================= */

map.on(
    "pm:create",
    async function (event) {

        /*
         * The polygon/rectangle drawn by the user
         * is the STUDY AREA.
         *
         * The backend automatically creates the
         * reference and performs the complete
         * experimental analysis.
         */


        /* Remove previous study area */

        if (
            selectedStudyArea &&
            selectedStudyArea !== event.layer
        ) {

            map.removeLayer(
                selectedStudyArea
            );
        }

        selectedStudyArea =
            event.layer;


        /* Remove previous experimental result */

        if (dynamicOverlay) {

            map.removeLayer(
                dynamicOverlay
            );

            dynamicOverlay = null;
        }


        const geojson =
            selectedStudyArea.toGeoJSON();

        const year =
            Number(yearSelect.value);


        status.className = "";

        status.textContent =
            `Running experimental dynamic analysis for ${year}…`;


        try {

            const response =
                await fetch(
                    `${API}/api/automatic-reference-analysis`,
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body: JSON.stringify({
                            geometry:
                                geojson.geometry,

                            year:
                                year
                        })
                    }
                );


            const data =
                await response.json();


            if (
                !response.ok ||
                data.error
            ) {

                throw new Error(
                    data.error ||
                    "Dynamic analysis failed."
                );
            }


            /*
             * This tile is the FINAL
             * automatic-reference analysis.
             *
             * It is NOT the intermediate
             * reference candidate layer.
             */

            if (
                data.tileUrl &&
                Number(data.area) > 0
            ) {

                dynamicOverlay =
                    L.tileLayer(
                        data.tileUrl,
                        {
                            opacity: 0.75,
                            maxZoom: 19
                        }
                    );

                dynamicOverlay.addTo(
                    map
                );
            }


            if (Number(data.area) === 0) {

                status.textContent =
                    `Experimental analysis — ${year}: ` +
                    `no glacier-like area was detected ` +
                    `inside the selected study area.`;

            } else {

                status.textContent =
                    `Experimental analysis — ${year}: ` +
                    `${Number(data.area).toFixed(2)} km² ` +
                    `glacier-like area detected inside ` +
                    `the selected study area.`;
            }


            console.log(
                "Experimental dynamic analysis:",
                data
            );

        } catch (error) {

            console.error(error);

            status.className =
                "error";

            status.textContent =
                `Dynamic analysis failed: ${error.message}`;
        }
    }
);


/* =========================
   Main controls
   ========================= */

viewButton.addEventListener(
    "click",
    function () {

        const year =
            Number(yearSelect.value);

        yearSlider.value =
            year;

        sliderYear.textContent =
            year;

        loadYear(
            year,
            false
        );
    }
);


viewSecondYearButton.addEventListener(
    "click",
    function () {

        loadSecondYear(
            Number(secondYearSelect.value)
        );
    }
);


/* =========================
   Timeline slider
   ========================= */

yearSlider.addEventListener(
    "input",
    function () {

        sliderYear.textContent =
            yearSlider.value;

        yearSelect.value =
            yearSlider.value;
    }
);


yearSlider.addEventListener(
    "change",
    function () {

        // Return to single-map Explorer view
        secondMapContainer.hidden = true;
        secondResultCard.hidden = true;

        if (
            secondOverlay &&
            secondMap
        ) {
            secondMap.removeLayer(
                secondOverlay
            );

            secondOverlay = null;
        }

        setTimeout(() => {
            map.invalidateSize();
        }, 100);

        loadYear(
            Number(yearSlider.value),
            false
        );
    }
);


/* =========================
   Year select
   ========================= */

yearSelect.addEventListener(
    "change",
    function () {

        yearSlider.value =
            yearSelect.value;

        sliderYear.textContent =
            yearSelect.value;
    }
);


/* =========================
   Glacier selection
   ========================= */

glacierSelect.addEventListener(
    "change",
    async function () {

        /* Remove existing overlays */

        if (firstOverlay) {

            map.removeLayer(
                firstOverlay
            );

            firstOverlay = null;
        }


        if (
            secondOverlay &&
            secondMap
        ) {

            secondMap.removeLayer(
                secondOverlay
            );

            secondOverlay = null;
        }


        if (dynamicOverlay) {

            map.removeLayer(
                dynamicOverlay
            );

            dynamicOverlay = null;
        }


        if (selectedStudyArea) {

            map.removeLayer(
                selectedStudyArea
            );

            selectedStudyArea = null;
        }


        /* Hide second comparison */

        secondMapContainer.hidden =
            true;

        secondResultCard.hidden =
            true;


        /* Move to glacier */

        moveToSelectedGlacier();


        /* Reload selected year */

        await loadYear(
            Number(yearSelect.value),
            false
        );


        setTimeout(() => {

            map.invalidateSize();

        }, 100);
    }
);


/* =========================
   Initial page load
   ========================= */

sliderYear.textContent =
    yearSelect.value;

firstMapLabel.textContent =
    yearSelect.value;

loadYear(
    Number(yearSelect.value),
    false
);