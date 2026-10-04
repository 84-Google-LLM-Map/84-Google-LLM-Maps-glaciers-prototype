# Glacier Change Explorer — Rob Roy and Marmolada

An interactive web application for visualising detected glacier-like areas between **2017 and 2024** at:

- **Rob Roy Glacier, New Zealand**
- **Marmolada Glacier, Italy — provisional demo**

The glacier dropdown allows users to switch between both locations.

The prototype uses **Google Satellite Embedding V1** through **Google Earth Engine (GEE)**. Each selected year is compared against a fixed reference created from 2017 embedding data.

Pixels with an embedding similarity of **0.80 or greater** are displayed in cyan.

**Important:** Detected areas represent similarity to the reference embedding. They are not confirmed glacier boundaries or direct measurements of glacier melting.

**Marmolada demo:** Marmolada currently uses an artificial, unverified reference polygon. Its results require Applied Science review and must not be interpreted as validated glacier measurements, collapse predictions or measurements of ice-volume loss.

---

## Project Structure

```text
84-Google-LLM-Maps-glaciers-prototype/
├── backend/
│   ├── app.py
│   ├── glacier_analysis.py
│   └── marmolada_analysis.py
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── style.css
├── docs/
│   ├── glaciers-app-current-architecture.png
│   └── glaciers-app-potential-architecture.png
├── requirements.txt
├── .gitignore
└── README.md
```

### Backend

The backend uses Python, Flask, Flask-CORS and the Google Earth Engine Python API.

It selects the requested glacier analysis, performs the calculations and returns the results through an API.

- `app.py`: API routes, glacier selection and error handling.
- `glacier_analysis.py`: Rob Roy analysis.
- `marmolada_analysis.py`: Provisional Marmolada analysis.

### Frontend

The frontend uses HTML, CSS, JavaScript and Leaflet.

The current toggle version contains its JavaScript and CSS directly in `frontend/index.html`. The older `app.js` and `style.css` files may remain in the repository but are not loaded by this version.

Leaflet displays the satellite basemap and the glacier-like overlay returned by Earth Engine.

---

## How the Application Works

1. The user selects a glacier and year.
2. The frontend sends the selection to the Flask API.
3. The backend selects the corresponding analysis script.
4. Earth Engine compares the selected year's embeddings against the fixed 2017 reference.
5. Pixels meeting the similarity threshold are used to calculate matching area.
6. The API returns the area and an Earth Engine map tile URL.
7. The frontend displays the results and cyan overlay at the selected location.

The analysis uses:

- **Reference year:** 2017
- **Embedding bands:** 64
- **Similarity threshold:** 0.80
- **Analysis scale:** 10 metres
- **Study radius:** 5 kilometres around each configured centre

The calculated area includes all matching pixels within the study area, including matches outside the glacier.

---

## Project Setup

### 1. Clone the Repository

```bash
git clone https://github.com/84-Google-LLM-Map/84-Google-LLM-Maps-glaciers-prototype.git
cd 84-Google-LLM-Maps-glaciers-prototype
```

These instructions assume the glacier-toggle changes have been merged into the branch you are using.

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

Each person running the backend needs an authenticated Google account with access to the configured Earth Engine project.

With the virtual environment active:

```bash
python -c "import ee; ee.Authenticate(auth_mode='localhost', force=True)"
```

Follow the browser authentication instructions using the Google account with project access.

The current project ID is:

```text
studied-market-509102-a7
```

Authentication alone does not grant access to the project. If access is denied, contact the team's project administrator.

Do not commit authentication credentials or tokens.

---

## Running the Application

Two local servers are required:

| Component | Port | Address |
|-----------|------|---------|
| Backend | 5000 | http://127.0.0.1:5000 |
| Frontend | 8000 | http://localhost:8000 |

Start both servers from the **same updated project folder**.

### 1. Start the Backend

Open a terminal in the project root.

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

Keep this terminal open.

The backend runs at:

```text
http://127.0.0.1:5000
```

To test the API directly, open:

```text
http://127.0.0.1:5000/api/glacier/2019?glacier=rob-roy
```

A successful request returns JSON containing the analysis results.

The backend root address is not the application interface. Use the frontend address below to view the map.

### 2. Start the Frontend

Open a second terminal in the project root.

**Windows PowerShell:**

```powershell
python -m http.server 8000 --directory frontend
```

**macOS/Linux:**

```bash
python3 -m http.server 8000 --directory frontend
```

Keep this terminal open, then visit:

```text
http://localhost:8000
```

If your terminal is already inside the `frontend` folder, omit `--directory frontend`.

### 3. Stop the Application

Press `Ctrl+C` in each server terminal.

These commands run the application locally for development and demonstration.

---

## Using the Application

1. Open **http://localhost:8000**.
2. Use the **Glacier** dropdown to select:
   - **Rob Roy — New Zealand**
   - **Marmolada — Italy**
3. Changing the glacier automatically runs analysis for the currently selected year and moves the map to that glacier.
4. To analyse another year, select a year between **2017 and 2024**, then click **View Year**.
5. Wait for the status message confirming that the analysis and overlay have loaded.
6. View the cyan overlay and matching area in **km²**.

The controls are temporarily disabled while analysis runs.

When Marmolada is selected, the application displays a warning explaining that its reference polygon and outputs are unverified.

**Basemap note:** Changing the analysis year changes the calculated overlay. It does not change the satellite basemap to imagery from that year.

### Observed Local Test Results

Both glacier selections successfully loaded during local testing for 2019:

| Glacier | Displayed matching area | Map overlay |
|---------|-------------------------|-------------|
| Rob Roy | 10.71 km² | Loaded at Rob Roy |
| Marmolada | 11.79 km² | Loaded at Marmolada |

Switching back to Rob Roy also removed the Marmolada demo warning.

These checks demonstrate application functionality in the tested local environment. They do not scientifically validate the calculated areas or confirm every supported year has been tested.

---

## API Reference

### Endpoint

```text
GET /api/glacier/<year>?glacier=<glacier-id>
```

### Parameters

| Parameter | Accepted values | Behaviour |
|-----------|-----------------|-----------|
| `year` | 2017–2024 | Required in the URL path |
| `glacier` | `rob-roy`, `marmolada` | Defaults to `rob-roy` when omitted |

### Rob Roy Example

```text
http://127.0.0.1:5000/api/glacier/2019?glacier=rob-roy
```

Example response:

```json
{
  "area": 10.71036953559871,
  "areaUnit": "km2",
  "glacier": "Rob Roy",
  "glacierId": "rob-roy",
  "referenceYear": 2017,
  "studyCentre": [168.741, -44.455],
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

- [ ] Start both servers from the same updated project folder.
- [ ] Confirm the Glacier dropdown is visible.
- [ ] Select Rob Roy and analyse 2019.
- [ ] Confirm the map moves to New Zealand and loads the overlay and area.
- [ ] Switch to Marmolada.
- [ ] Confirm the map moves to Italy and loads the overlay and area.
- [ ] Confirm the Marmolada demo warning appears.
- [ ] Switch back to Rob Roy and confirm the Marmolada warning disappears.
- [ ] Change the year and click View Year.
- [ ] Confirm the status and results show the selected glacier and year.
- [ ] Test `/api/glacier/2016` and confirm an HTTP 400 response.
- [ ] Test `/api/glacier/2019?glacier=invalid` and confirm an HTTP 400 response.
- [ ] Stop the backend and request another analysis to confirm the frontend displays an error.
- [ ] Restart the backend and confirm analysis works again.

Record the glacier, year, result and any error message when reporting an issue.

---

## Troubleshooting

### The Glacier Dropdown Is Missing

You may be serving an older copy of the frontend.

Stop the frontend server with `Ctrl+C`, then run this from the updated project root:

```bash
python -m http.server 8000 --directory frontend
```

Open **http://localhost:8000** and press **Ctrl+F5** to refresh.

### Marmolada Returns Rob Roy Results or a Wrong-Glacier Error

The backend may still be running an older version of `app.py`.

Stop the backend with `Ctrl+C`, then restart it from the updated project root:

```bash
python backend/app.py
```

Confirm these files are present:

```text
backend/app.py
backend/glacier_analysis.py
backend/marmolada_analysis.py
frontend/index.html
```

If multiple copies of the project exist on your computer, check the folder used by each terminal.

### The Frontend Returns 404

Check the folder where you started the frontend server.

From the project root:

```bash
python -m http.server 8000 --directory frontend
```

From inside the frontend folder:

```bash
python -m http.server 8000
```

On macOS/Linux, use `python3` if `python` is unavailable.

### Analysis Fails

Check both the frontend error message and the backend terminal.

Confirm that:

- The backend is running on port 5000.
- The required Python dependencies are installed.
- Earth Engine authentication has completed.
- Your Google account has access to the configured project.
- The selected year is between 2017 and 2024.

If the same code works on another computer, compare the project version, Python environment, authentication and project access.

### Windows Virtual Environment Activation Is Blocked

You can run the virtual environment's Python directly without activating it:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe backend/app.py
```

### The Area Loads but the Overlay Fails

Try **View Year** again to request fresh map tiles.

Check your internet connection and the browser's developer console for failed tile requests.

---

## Current Prototype Limitations

- Rob Roy uses the team's existing 2017 reference polygons.
- Marmolada uses an artificial, unverified reference polygon requiring Applied Science review or replacement.
- The reference, threshold and study area require scientific validation.
- The calculation includes all matching pixels within a 5 km study radius.
- Matching pixels may occur outside the glacier.
- The results do not independently identify confirmed glacier boundaries.
- Changes in matching area do not establish the physical cause of a change.
- Outputs are not measurements of glacier melting or ice-volume loss.
- Annual embeddings cannot isolate short-term precursors to a collapse.
- Marmolada's 2022 annual embedding includes the event year and must not be treated as a pre-collapse prediction.
- The satellite basemap does not change with the selected analysis year.

Results are therefore described as **detected glacier-like area** or **matching area**, rather than confirmed glacier extent or glacier melt.

---

## Technologies

- Google Earth Engine
- Google Satellite Embedding V1
- Python
- Flask
- Flask-CORS
- JavaScript
- Leaflet
- HTML
- CSS
