// ========================================
// Rob Roy Glacier Change Explorer
// frontend/app.js
// ========================================


// ----------------------------------------
// 1. Create the Leaflet map
// ----------------------------------------
console.log("app.js loaded!");

const map = L.map("map").setView(
  [-44.455, 168.741],
  12
);


// ----------------------------------------
// 2. Base map layers
// ----------------------------------------

const streetMap = L.tileLayer(
  "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
  {
    attribution: "© OpenStreetMap contributors"
  }
);

const satelliteMap = L.tileLayer(
  "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
  {
    attribution: "Tiles © Esri"
  }
);


// Show satellite map by default
satelliteMap.addTo(map);


// Allow switching between maps
L.control.layers({
  Satellite: satelliteMap,
  "Street Map": streetMap
}).addTo(map);


// ----------------------------------------
// 3. Glacier layer
// ----------------------------------------

// This variable stores the current
// Earth Engine glacier-like layer.

let glacierLayer;


// ----------------------------------------
// 4. Load glacier analysis for a year
// ----------------------------------------

async function displayYear(year) {

  const areaElement =
    document.getElementById("area");

  const button =
    document.getElementById("viewYear");


  // Tell the user analysis is running
  areaElement.textContent = "Calculating...";

  button.disabled = true;
  button.textContent = "Loading...";


  try {

    // ------------------------------------
    // Ask Flask backend for glacier data
    // ------------------------------------

    const response = await fetch(
      `http://127.0.0.1:5000/api/glacier/${year}`
    );


    const data = await response.json();


    // If Flask returned an error
    if (!response.ok) {
      throw new Error(
        data.error || "Could not load glacier data"
      );
    }


    console.log(
      "Glacier API response:",
      data
    );


    // ------------------------------------
    // Remove previous glacier layer
    // ------------------------------------

    if (glacierLayer) {
      map.removeLayer(glacierLayer);
    }


    // ------------------------------------
    // Add Earth Engine glacier mask
    // ------------------------------------

    glacierLayer = L.tileLayer(
      data.tileUrl,
      {
        opacity: 0.65
      }
    );


    glacierLayer.addTo(map);


    // ------------------------------------
    // Display glacier-like area
    // ------------------------------------

    areaElement.textContent =
      `${data.area.toFixed(2)} km²`;


    console.log(
      `Year: ${data.year}`
    );

    console.log(
      `Reference year: ${data.referenceYear}`
    );

    console.log(
      `Threshold: ${data.threshold}`
    );

    console.log(
      `Glacier-like area: ${data.area} km²`
    );


  } catch (error) {

    // ------------------------------------
    // Handle errors
    // ------------------------------------

    console.error(
      "Error loading glacier data:",
      error
    );

    areaElement.textContent =
      "Could not load glacier data";


  } finally {

    // Re-enable button
    button.disabled = false;
    button.textContent = "View Year";

  }
}


// ----------------------------------------
// 5. View Year button
// ----------------------------------------

document
  .getElementById("viewYear")
  .addEventListener(
    "click",
    function () {

      const year =
        document.getElementById("year").value;

      displayYear(year);

    }
  );


// ----------------------------------------
// 6. Load default year
// ----------------------------------------

// Load whatever year is currently selected
// when the page first opens.

const defaultYear =
  document.getElementById("year").value;

displayYear(defaultYear);