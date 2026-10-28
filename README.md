# Glacier Change Explorer

An interactive web application for visualising detected glacier-like areas between **2017 and 2024** at:

- **Rob Roy Glacier, New Zealand**
- **Franz Josef Glacier, New Zealand**
- **Aletsch Glacier, Switzerland**
- **Rhône Glacier, Switzerland**
- **Mendenhall Glacier, Alaska, USA**
- **Gangotri Glacier, India**
- **Marmolada Glacier, Italy — provisional demo**

The glacier dropdown allows users to switch between these locations.

The prototype uses **Google Satellite Embedding V1** through **Google Earth Engine (GEE)**. Each selected year is compared against a fixed reference created from 2017 embedding data.

Pixels with an embedding similarity of **0.80 or greater** are displayed in red.

The application has two pages:

- **Home / Explorer:** the standard analysis, using each glacier's hand-picked 2017 reference polygons.
- **Experimental Explorer:** users draw their own study area and the reference is selected automatically. This feature is experimental (see [Current Prototype Limitations](#current-prototype-limitations)).

**Important:** Detected areas represent similarity to the reference embedding. They are not confirmed glacier boundaries or direct measurements of glacier melting.

**Marmolada demo:** Marmolada currently uses an artificial, unverified reference polygon. Its results require Applied Science review and must not be interpreted as validated glacier measurements, collapse predictions or measurements of ice-volume loss.

---

## Project Structure

```text
84-Google-LLM-Maps-glaciers-prototype/
├── backend/
│   ├── app.py
│   ├── ee_auth.py
│   ├── glaciers.py
│   ├── glacier_analysis.py
│   └── marmolada_analysis.py
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── style.css
├── docs/
│   ├── glaciers-app-current-architecture.png
│   └── glaciers-app-potential-architecture.png
├── secrets/            (local only, git-ignored)
├── requirements.txt
├── .gitignore
└── README.md
```

### Backend

The backend uses Python, Flask, Flask-CORS and the Google Earth Engine Python API.

It selects the requested glacier analysis, performs the calculations and returns the results through an API. It also serves the frontend files.

- `app.py`: API routes, glacier selection and error handling.
- `ee_auth.py`: Earth Engine authentication (service account, with a fallback to a personal login for local development).
- `glaciers.py`: Configuration for each glacier: centre, study radius and 2017 reference polygons.
- `glacier_analysis.py`: Standard analysis for all configured glaciers, plus the experimental automatic-reference analysis.
- `marmolada_analysis.py`: Provisional Marmolada analysis.

### Frontend

The frontend uses HTML, CSS and JavaScript, with no build step.

- **Leaflet** displays the satellite basemap and the glacier-like overlay returned by Earth Engine.
- **Leaflet-Geoman** provides the drawing tools on the Experimental Explorer page.
- **Chart.js** draws the 2017–2024 area graph shown on both pages.

---

## How the Application Works

1. The user selects a glacier and year.
2. The frontend sends the selection to the Flask API.
3. The backend selects the corresponding analysis script.
4. Earth Engine compares the selected year's embeddings against the fixed 2017 reference.
5. Pixels meeting the similarity threshold are used to calculate matching area.
6. The API returns the area and an Earth Engine map tile URL.
7. The frontend displays the results and red overlay at the selected location, and fills in the area graph as the other years load.

The analysis uses:

- **Reference year:** 2017
- **Embedding bands:** 64
- **Similarity threshold:** 0.80
- **Analysis scale:** 10 metres
- **Study radius:** 5–20 kilometres around each configured centre, depending on the glacier's size

The calculated area includes all matching pixels within the study area, including matches outside the glacier.

### Experimental Analysis

On the Experimental Explorer page, the user draws a rectangle or shape on the map. Instead of using hand-picked polygons, the backend selects 2017 reference pixels inside the drawn area automatically. To be selected, a pixel must be:

- in the top 25% of mean **Dynamic World** snow/ice probability during the local summer
- in the top 30% of **SRTM** elevation
- on a slope facing away from the sun

The summer dates and slope direction are chosen from the area's hemisphere. The rest of the analysis is the same as above, and the result is shown in yellow.

---

## Project Setup

### 1. Clone the Repository

```bash
git clone https://github.com/84-Google-LLM-Map/84-Google-LLM-Maps-glaciers-prototype.git
cd 84-Google-LLM-Maps-glaciers-prototype
```

### 2. Create and Activate a Python Virtual Environment

Run these commands from the project root.

**Windows PowerShell:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS/Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

The terminal should now show `(.venv)`.

Do not commit the virtual environment.

### 3. Install Dependencies

With the virtual environment active:

```bash
python -m pip install -r requirements.txt
```

### 4. Authenticate Google Earth Engine

The backend authenticates with Earth Engine using a Google Cloud **service account**, so users of the website do not need an Earth Engine account or login.

The current project ID is:

```text
studied-market-509102-a7
```

**Option A: service-account key (recommended, same as deployment)**

1. Obtain the service-account JSON key from the team's project administrator through a secure channel. If the JSON key cannot be obtained, another JSON key can be generated from the Google project account.
2. Save it in the `secrets/` folder in the project root. This folder is git-ignored.
3. Load it into an environment variable before starting the backend:

**macOS/Linux:**

```bash
export EE_SERVICE_ACCOUNT_KEY="$(cat secrets/<key-file>.json)"
```

**Windows PowerShell:**

```powershell
$env:EE_SERVICE_ACCOUNT_KEY = Get-Content secrets\<key-file>.json -Raw
```

**Option B: personal login (local development only)**

If `EE_SERVICE_ACCOUNT_KEY` is not set, the backend falls back to a personal Earth Engine login. Your Google account must have access to the project:

```bash
python -c "import ee; ee.Authenticate(auth_mode='localhost', force=True)"
```

Authentication alone does not grant access to the project. If access is denied, contact the team's project administrator.

Never commit the service-account key, authentication credentials or tokens. If the key is exposed, delete it in the Google Cloud Console and create a new one.

---

## Running the Application

The Flask backend serves both the API and the frontend, so only one server is required.

### 1. Start the Application

Open a terminal in the project root, then activate the virtual environment and set the key as described in [Authenticate Google Earth Engine](#4-authenticate-google-earth-engine).

**Windows PowerShell:**

```powershell
.\.venv\Scripts\Activate.ps1
python backend/app.py
```

**macOS/Linux:**

```bash
source .venv/bin/activate
python backend/app.py
```

Keep this terminal open, then visit:

```text
http://127.0.0.1:5000
```

To test the API directly, open:

```text
http://127.0.0.1:5000/api/glacier/2019?glacier=rob-roy
```

A successful request returns JSON containing the analysis results.

### 2. Stop the Application

Press `Ctrl+C` in the server terminal.

These commands run the application locally for development and demonstration.

### Deployment

The frontend and backend are deployed together on **Vercel**. Set these environment variables in the Vercel project settings, then redeploy:

| Variable                 | Value                                             |
| ------------------------ | ------------------------------------------------- |
| `EE_SERVICE_ACCOUNT_KEY` | The full contents of the service-account JSON key |
| `EE_PROJECT_ID`          | `studied-market-509102-a7`                        |

The frontend must call the API on the same site (`const API = ""` in `frontend/app.js`), never `localhost:5000`.

---

## Using the Application

1. Open **http://127.0.0.1:5000**, or the deployed site.
2. Use the **Select glacier** dropdown to choose a glacier. The map moves to it and the selected year is analysed.
3. Choose a year between **2017 and 2024** using the year slider or **Select Year**, then click **View Year**.
4. Optionally, choose a **Second Year** and click **View Second Year** to compare the two years side by side.
5. **Analyse Glacier** runs the first year, and the second year if one is selected, together.
6. View the red overlay, the matching area in **km²** and the 2017–2024 area graph in **Results**.

On the **Experimental Explorer** page, use the drawing tools on the right of the map to draw a rectangle or shape. The experimental analysis runs automatically for the selected year.

When Marmolada is selected, the application displays a warning explaining that its reference polygon and outputs are unverified.

**Basemap note:** Changing the analysis year changes the calculated overlay. It does not change the satellite basemap to imagery from that year.

### Observed Local Test Results

Both glacier selections successfully loaded during local testing for 2019:

| Glacier   | Displayed matching area | Map overlay         |
| --------- | ----------------------- | ------------------- |
| Rob Roy   | 10.71 km²               | Loaded at Rob Roy   |
| Marmolada | 11.79 km²               | Loaded at Marmolada |

Switching back to Rob Roy also removed the Marmolada demo warning.

These checks demonstrate application functionality in the tested local environment. They do not scientifically validate the calculated areas or confirm every supported year has been tested.

---

## API Reference

### Endpoints

```text
GET  /api/glacier/<year>?glacier=<glacier-id>
POST /api/automatic-reference-analysis
GET  /health
```

### Parameters

| Parameter | Accepted values                                                                     | Behaviour                          |
| --------- | ----------------------------------------------------------------------------------- | ---------------------------------- |
| `year`    | 2017–2024                                                                           | Required in the URL path           |
| `glacier` | `rob-roy`, `franz-josef`, `aletsch`, `rhone`, `mendenhall`, `gangotri`, `marmolada` | Defaults to `rob-roy` when omitted |

### Rob Roy Example

```text
http://127.0.0.1:5000/api/glacier/2019?glacier=rob-roy
```

Example response:

```json
{
  "area": 10.71036953559871,
  "areaUnit": "km2",
  "glacier": "Rob Roy Glacier",
  "glacierId": "rob-roy",
  "referenceYear": 2017,
  "studyCentre": [168.741, -44.455],
  "studyRadiusM": 5000,
  "threshold": 0.8,
  "tileUrl": "Earth Engine map tile URL",
  "year": 2019
}
```

`studyCentre` coordinates are returned in **longitude, latitude** order.

### Marmolada Example

```text
http://127.0.0.1:5000/api/glacier/2019?glacier=marmolada
```

Marmolada returns the same core fields, plus demonstration metadata including:

- `demoOnly`
- `referenceStatus`
- `warning`
- `interpretation`
- `studyRadiusM`
- `collapseDate`

### Experimental Analysis

```text
POST /api/automatic-reference-analysis
```

Request body:

```json
{
  "geometry": { "type": "Polygon", "coordinates": [[[168.73, -44.46], "..."]] },
  "year": 2019,
  "glacier": "rob-roy"
}
```

`geometry` is the drawn area as GeoJSON. `glacier` is optional and selects the manual reference used for comparison.

The response includes `area`, `tileUrl`, `referenceYear` and `threshold`, plus diagnostics such as:

- `candidateArea`
- `manualAutomaticReferenceSimilarity`
- `hemisphere`
- the thresholds used

### Default Glacier

The existing URL remains supported and defaults to Rob Roy:

```text
http://127.0.0.1:5000/api/glacier/2019
```

### Error Responses

- **HTTP 400:** Out-of-range integer year or unsupported glacier selection.
- **HTTP 500:** Analysis or Earth Engine failure.

Error responses include an `error` message. Invalid URL formats may return Flask's standard HTTP 404 response.

---

## Manual Testing Checklist

Run these checks before a demonstration or after updating the application:

- [ ] Start the backend from the updated project folder and open http://127.0.0.1:5000.
- [ ] Confirm the Glacier dropdown is visible.
- [ ] Select Rob Roy and analyse 2019.
- [ ] Confirm the map moves to New Zealand and loads the overlay, area and graph.
- [ ] Switch to Marmolada.
- [ ] Confirm the map moves to Italy and loads the overlay and area.
- [ ] Confirm the Marmolada demo warning appears.
- [ ] Switch back to Rob Roy and confirm the Marmolada warning disappears.
- [ ] Change the year and click View Year.
- [ ] Confirm the status and results show the selected glacier and year.
- [ ] Select a second year and confirm the side-by-side map and second result card appear.
- [ ] Open Experimental Explorer, draw a rectangle over Rob Roy and confirm a yellow result appears.
- [ ] Test `/api/glacier/2016` and confirm an HTTP 400 response.
- [ ] Test `/api/glacier/2019?glacier=invalid` and confirm an HTTP 400 response.
- [ ] Stop the backend and request another analysis to confirm the frontend displays an error.
- [ ] Restart the backend and confirm analysis works again.

Record the glacier, year, result and any error message when reporting an issue.

---

## Troubleshooting

### The Page Shows an Old Version

You may be viewing a cached copy of the frontend.

Restart the backend from the updated project root, then open **http://127.0.0.1:5000** and press **Ctrl+F5** (**Cmd+Shift+R** on macOS) to refresh.

### Marmolada Returns Rob Roy Results or a Wrong-Glacier Error

The backend may still be running an older version of `app.py`.

Stop the backend with `Ctrl+C`, then restart it from the updated project root:

```bash
python backend/app.py
```

Confirm these files are present:

```text
backend/app.py
backend/ee_auth.py
backend/glaciers.py
backend/glacier_analysis.py
backend/marmolada_analysis.py
frontend/index.html
```

If multiple copies of the project exist on your computer, check the folder used by the terminal.

### API Requests Return 404 or Connection Refused

- **Locally:** open the app through Flask at **http://127.0.0.1:5000**. A static server such as `python -m http.server` cannot run the `/api/...` routes.
- **On the deployed site:** check that `const API` in `frontend/app.js` is `""` and not `http://localhost:5000`.

### Analysis Fails

Check both the frontend error message and the backend terminal.

Confirm that:

- The backend is running on port 5000.
- The required Python dependencies are installed.
- `EE_SERVICE_ACCOUNT_KEY` is set in the same terminal, or a personal Earth Engine login has completed.
- The service account or your Google account has access to the configured project.
- The selected year is between 2017 and 2024.

If the same code works on another computer, compare the project version, Python environment, authentication and project access.

### Windows Virtual Environment Activation Is Blocked

You can run the virtual environment's Python directly without activating it:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe backend/app.py
```

### The Area Loads but the Overlay Fails

Try **View Year** again to request fresh map tiles. Earth Engine tile URLs expire after a few hours.

Check your internet connection and the browser's developer console for failed tile requests.

---

## Current Prototype Limitations

- Each glacier uses hand-picked 2017 reference polygons from `glaciers.py`.
- Marmolada uses an artificial, unverified reference polygon requiring Applied Science review or replacement.
- The reference, threshold and study area require scientific validation.
- The calculation includes all matching pixels within each glacier's study radius.
- Matching pixels may occur outside the glacier.
- The results do not independently identify confirmed glacier boundaries.
- Changes in matching area do not establish the physical cause of a change.
- Outputs are not measurements of glacier melting or ice-volume loss.
- Annual embeddings cannot isolate short-term precursors to a collapse.
- Marmolada's 2022 annual embedding includes the event year and must not be treated as a pre-collapse prediction.
- The satellite basemap does not change with the selected analysis year.
- The experimental automatic reference was developed on Rob Roy and is not reliable for every glacier, especially in the northern hemisphere. Its thresholds are relative to the drawn area, so results depend on how the area is drawn.
- Very large drawn areas can exceed Earth Engine's pixel limit, and large glaciers load more slowly.

Results are therefore described as **detected glacier-like area** or **matching area**, rather than confirmed glacier extent or glacier melt.

---

## Technologies

- Google Earth Engine
- Google Satellite Embedding V1
- Google Dynamic World and SRTM elevation (experimental analysis)
- Google Cloud service account authentication
- Python
- Flask
- Flask-CORS
- JavaScript
- Leaflet
- Leaflet-Geoman
- Chart.js
- HTML
- CSS
- Vercel
