# Prototype Architecture

## 1. Overview

The Rob Roy Glacier Change Explorer is a prototype web application
designed to make changes in detected glacier-like areas easier to
visualise across multiple years.

Current architecture:

![glaciers-app-current-architecture](glaciers-app-current-architecture.png)

## 2. Why This Architecture Was Selected

Google Earth Engine was selected for the prototype because the existing
glacier analysis had already been developed by the applied science students and validated within Google Earth Engine.

Using the Google Earth Engine Python API allowed the existing methodology to be transferred to a web application without redesigning the underlying
analysis.

The prototype therefore focuses on demonstrating the user experience
and research concept rather than building a new geospatial processing
platform.

The Python implementation was validated against the original Earth
Engine implementation. For 2019, both implementations produced a
detected glacier-like area of approximately 10.71037 km².

## 3. Frontend

Leaflet is used to provide the interactive map interface.

The user can select a year between 2017 and 2024. The frontend requests
the corresponding analysis from the Flask backend and displays the
returned Earth Engine map tiles.

Leaflet was selected because it provides a lightweight way to display
interactive geospatial layers without requiring a larger frontend
framework. It is also an open-source, free tool to use.

## 4. Backend

Flask provides a small REST API between the frontend and Google Earth
Engine.

Example:

GET /api/glacier/2019

The backend performs the Earth Engine analysis and returns:

- selected year
- reference year
- similarity threshold
- detected glacier-like area
- map tile URL

## 5. Google Earth Engine

Earth Engine currently performs the geospatial processing.

For each selected year, Satellite Embedding V1 data is compared against
a fixed glacier/snow reference derived from 2017.

A similarity threshold of 0.80 is applied to identify glacier-like
pixels, and the resulting area is calculated in square kilometres.

Using Earth Engine avoids downloading and locally processing the
underlying satellite embedding data during the prototype stage.

## 6. Prototype Architecture Limitation

The current architecture depends on Google Earth Engine as the
processing backend.

This is suitable for demonstrating the prototype, but Earth Engine
service access and the Satellite Embedding dataset should be considered
separately when evaluating a future production or commercial system.

## 7. Potential Production Architecture

### Commercial Considerations

Although Earth Engine is suitable for the prototype, the commercial viability of the architecture must also be considered.

Google provides Earth Engine access for eligible noncommercial projects, while commercial usage requires an appropriate commercial Earth Engine configuration. A commercial implementation would therefore need to consider Earth Engine pricing, compute usage, quotas and other infrastructure costs.

Google Earth Engine documentation:

- [Earth Engine access and project configuration](https://developers.google.com/earth-engine/guides/access)
- [Earth Engine commercial transition](https://developers.google.com/earth-engine/guides/transition_to_commercial)

---

### Alternative Architecture Without Earth Engine

Satellite Embedding V1 is not limited to Google Earth Engine.

The underlying **AlphaEarth Foundations Satellite Embedding dataset** is also distributed outside Earth Engine as **Cloud-Optimized GeoTIFFs (COGs)**. The dataset is licensed under **CC BY 4.0**, which permits commercial use subject to the licence's attribution and other requirements.

The external distribution contains annual embedding data that could therefore be accessed and processed directly by the application rather than through Earth Engine.

Relevant documentation:

- [Google AlphaEarth Foundations COG documentation](https://developers.google.com/earth-engine/guides/aef_on_gcs_readme)
- [Source Cooperative AlphaEarth Foundations distribution](https://source.coop/tge-labs/aef)
- [Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/)

### Cloud-Optimized GeoTIFFs

A **Cloud-Optimized GeoTIFF (COG)** is a geospatial raster format designed to allow applications to efficiently access portions of large raster datasets stored remotely.

This means the application would not necessarily need to download an entire embedding dataset to analyse a relatively small area such as Rob Roy Glacier.

The AlphaEarth Foundations COGs contain the **64 Satellite Embedding dimensions (A00–A63)** required by the current glacier similarity algorithm.

A geographic index provided with the dataset can be used to identify which COG intersects the requested study area.

---

### Potential Processing Pipeline

A future implementation could process the officially distributed
Satellite Embedding data outside Google Earth Engine.

Possible architecture:

![glaciers-app-potential-architecture](glaciers-app-potential-architecture.png)

---

**Rasterio** could be used to read the required geographic window and embedding bands from the COG while maintaining the raster's spatial information, including its coordinate reference system, transform and geographic extent.

The raster embedding values could then be represented as numerical arrays and processed using **NumPy**.

NumPy could reproduce the mathematical portion of the current Earth Engine algorithm:

1. Calculate the glacier reference embedding from the 2017 reference area.
2. Normalise the reference embedding.
3. Load the 64-dimensional embedding for the selected year.
4. Calculate similarity between each pixel and the reference embedding.
5. Apply the `>= 0.80` similarity threshold.
6. Produce a binary glacier-like mask.
7. Calculate the detected glacier-like area.

The resulting mask could then be converted into a web-compatible geospatial representation.

For a small prototype, this could be **GeoJSON**, which Leaflet can display directly. For a larger system, the resulting raster products could instead be stored and served as **map tiles or Cloud-Optimized GeoTIFFs**.
