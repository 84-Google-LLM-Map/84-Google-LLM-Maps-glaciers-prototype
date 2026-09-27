# Edge Case Testing Report

**Tester:** Cameron Nguyen
**Date:** 27 September 2026
**Application:** Rob Roy Glacier Change Explorer
**Environment:** Local Windows setup, Flask backend on port 5000 and frontend on port 8000
**Testing method:** Manual testing, including temporary code changes to simulate failures and zero detections.

## Test 1 — Normal loading

**Steps:**

1. Start the backend and frontend.
2. Select 2019.
3. Click View Year.

**Expected result:** The detected glacier-like area and map overlay load successfully.

**Actual result:** The application displayed an area value of 10.71 and a turquoise overlay. The unit appeared incorrectly as `kmÂ²`.

**Status:** Pass for loading results. Unit display bug recorded separately.

**Evidence:** Screenshot of the successful 2019 result.

## Test 2 — Backend unavailable

**Steps:**

1. Load the 2019 result successfully.
2. Stop the backend using Ctrl + C.
3. Select 2018 and click View Year.

**Expected result:** A clear error appears, loading stops, and the previous result is cleared or clearly labelled as outdated.

**Actual result:** The application displayed “Could not load glacier data”. However, the previous overlay remained visible while 2018 was selected.

**Status:** Pass for the error message. Fail for handling the previous overlay.

**Note:** This tested a frontend-to-backend connection failure, not a Google Earth Engine outage.

**Evidence:** Screenshot showing the error and the remaining overlay.

## Test 3 — Recovery after backend restart

**Steps:**

1. Restart the backend after Test 2.
2. Select 2018 and click View Year again.

**Expected result:** The application loads a successful result and replaces the error message.

**Actual result:** The error was replaced with an area value of 10.04, and a turquoise overlay was displayed.

**Status:** Pass for loading after restart. Recovery without refreshing the page was not separately confirmed.

**Evidence:** Screenshot of the successful 2018 result.

## Test 4 — Simulated Google Earth Engine exception

**Steps:**

1. Temporarily add the following line at the start of `calculate_glacier(year)`:
   `raise ee.EEException("TEST ONLY: Google Earth Engine data could not be retrieved")`
2. Save the file and allow the backend to reload.
3. Select 2022 and click View Year.
4. Check the website and backend terminal.

**Expected result:** The backend catches the exception, returns an error response, and the website displays an error message.

**Actual result:** The website displayed “Could not load glacier data”. The backend terminal recorded the TEST ONLY exception and HTTP 500 responses during testing.

**Status:** Pass for simulated exception handling.

**Note:** This was a deliberately injected exception, not a real Earth Engine service outage. After the temporary line was removed, the terminal showed a successful HTTP 200 response for a 2019 request.

**Evidence:** Website error screenshot and backend terminal screenshot.

## Test 5 — Simulated zero detections

**Steps:**

1. Temporarily add the following line immediately after the glacier mask is created:
   `glacier_mask = glacier_mask.multiply(0)  # TEST ONLY: force no detections`
2. Save the file and allow the backend to reload.
3. Select 2018 and click View Year.

**Expected result:** The application displays zero area, no glacier-like overlay, and a message explaining that no glacier-like area was detected.

**Actual result:** The application displayed `0.00 kmÂ²` with no turquoise overlay. No explanatory no-detection message appeared.

**Status:** Pass for displaying zero area and no overlay. Fail for the required no-detection message.

**Note:** This test forced an empty detection mask. It does not demonstrate that Rob Roy Glacier was absent or test the accuracy of analysis at a real glacier-free location.

**Evidence:** Screenshot showing the zero-area result.

## Outstanding tests

| Test                                        | Status                                | Reason / next step                                                                                                                                                                                       |
| ------------------------------------------- | ------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Selected area is too large                  | Blocked through the current interface | The application uses a fixed 5 km buffer around Rob Roy Glacier and has no area-selection control or explicit size-validation rule. Confirm the maximum permitted area and arrange a test configuration. |
| Analysis of an actual glacier-free location | Not tested                            | A separate test location and suitable configuration are needed. Moving the current study area also affects how the reference data is extracted.                                                          |

## Bugs found

| ID     | Issue                                                                                            | Expected behaviour                                                                              |
| ------ | ------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------- |
| BUG-01 | Previous overlay remains visible after a failed request, even when a different year is selected. | Clear the previous overlay or label it with its original year and indicate that it is outdated. |
| BUG-02 | Area units display as `kmÂ²` instead of `km²`.                                                   | Display the square-kilometre unit correctly.                                                    |
| BUG-03 | Zero detections display only a zero-area value without an explanatory message.                   | Display “No glacier-like area detected for the selected year” alongside the zero result.        |

## Handover

The completed tests cover normal loading, backend connection failure, recovery after restart, a simulated Earth Engine exception and simulated zero detections.
