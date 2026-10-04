# Marmolada Analysis Testing Report

**Tester:** Saanvi Telukoti  
**Application:** Glacier Change Explorer  
**Testing method:** Manual testing of the Marmolada analysis script and Flask API.

## Test 1 — Run Marmolada Analysis

**Steps:**

1. Run `python backend/marmolada_analysis.py 2021`.
2. Check the returned result.

**Expected result:** The analysis completes and returns the detected area and map tile.

**Actual result:** The analysis completed successfully and returned JSON data containing the area and tile URL.

**Status:** Pass

## Test 2 — Test Different Years

**Steps:**

1. Run the analysis for multiple years between 2017 and 2024.
2. Check that each year returns a result.

**Expected result:** Each supported year can be analysed successfully.

**Actual result:** The tested years successfully returned glacier-like area results.

**Status:** Pass

## Test 3 — Invalid Year

**Steps:**

1. Run the analysis using a year outside 2017–2024.

**Expected result:** The program rejects the invalid year.

**Actual result:** The invalid year was rejected with an appropriate error message.

**Status:** Pass

## Test 4 — Flask API

**Steps:**

1. Start the Flask backend.
2. Request a Marmolada year through the API.

**Expected result:** The API returns the Marmolada analysis as JSON.

**Actual result:** The API successfully returned the analysis result.

**Status:** Pass

## Test 5 — Map Display

**Steps:**

1. Open the web application.
2. Change the map centre from the Rob Roy Glacier coordinates in New Zealand to the Marmolada coordinates in Italy.
3. Select different years.
4. Check the map overlay and area result.

**Expected result:** The map displays Marmolada and shows the selected year's glacier-like overlay and area.

**Actual result:** The map initially remained centred on Rob Roy because the frontend used the Rob Roy coordinates. After changing the map centre to Marmolada, the area and turquoise overlay displayed successfully for the tested years.

**Status:** Pass

**Note:** The frontend map centre currently needs to be changed when switching from Rob Roy to Marmolada.

## Limitation

The Marmolada reference polygon is currently an **unverified artificial reference area**. These tests confirm that the software works, but they do not validate the scientific accuracy of the detected glacier-like areas.
