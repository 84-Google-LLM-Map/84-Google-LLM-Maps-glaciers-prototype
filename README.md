# Rob Roy Glacier Change Explorer

An interactive web application for visualising changes in detected glacier-like areas at **Rob Roy Glacier, New Zealand**, between **2017 and 2024**.

The prototype uses **Google Satellite Embedding V1** through Google Earth Engine (GEE). A fixed glacier/snow reference is created from 2017 embedding data, and each selected year is compared against this reference.

Pixels with an embedding similarity of **0.80 or greater** are displayed as glacier-like areas.

**Note:** The detected areas represent similarity to the 2017 glacier/snow embedding reference. They should not be interpreted as confirmed glacier extent or direct measurements of glacier melting.

---

## Project Structure

```text
84-Google-LLM-Maps-glaciers-prototype/
│
├── backend/
│   ├── app.py
│   └── glacier_analysis.py
│
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── style.css
│
├── docs/
│   ├── glaciers-app-current-architecture.png
│   ├── glaciers-app-potential-architecture.png
│
├── requirements.txt
├── .gitignore
└── README.md

```

### Backend

The backend uses:

- Python
- Flask
- Google Earth Engine Python API
- Flask-CORS

It performs the Satellite Embedding analysis and provides the results to the frontend through an API.

### Frontend

The frontend uses:

- HTML
- CSS
- JavaScript
- Leaflet

Leaflet displays the satellite basemap and the glacier-like area returned by Google Earth Engine.

---

# How the Application Works

![glaciers-app-current-architecture](docs/glaciers-app-current-architecture.png)

For example:

```text
GET /api/glacier/2019
```

returns data similar to:

```json
{
  "area": 10.71036953559871,
  "referenceYear": 2017,
  "threshold": 0.8,
  "tileUrl": "Earth Engine map tile URL",
  "year": 2019
}
```

---

# Project Setup

## 1. Clone the Repository

```bash
git clone https://github.com/84-Google-LLM-Map/84-Google-LLM-Maps-glaciers-prototype.git
cd 84-Google-LLM-Maps-glaciers-prototype
```

---

## 2. Create a Python Virtual Environment

From the project root:

```bash
python3 -m venv .venv
```

Activate it on macOS/Linux:

```bash
source .venv/bin/activate
```

The terminal should now show:

```text
(.venv)
```

Do not commit the virtual environment.

---

## 3. Install Python Dependencies

With the virtual environment active run:

```bash
pip install -r requirements.txt
```

---

# Google Earth Engine Setup

## 4. Authenticate Earth Engine

With the virtual environment active, run:

```bash
python -c "import ee; ee.Authenticate(auth_mode='localhost', force=True)"
```

A Google authentication page should open in the browser.

Sign in using the Google account with access to the Earth Engine project and approve the requested permissions.

After successful authentication, the browser should display a message similar to:

```text
Google Earth Engine authorization successful!
Credentials have been retrieved.
```

---

# Running the Application

Two local servers are required:

```text
Frontend → port 8000
Backend  → port 5000
```

## 1. Start the Backend

From the project root:

```bash
source .venv/bin/activate
python backend/app.py
```

The Flask server should start at:

```text
http://127.0.0.1:5000
```

You can test the glacier API directly using:

```text
http://127.0.0.1:5000/api/glacier/2019
```

A successful request should return JSON containing:

- selected year
- reference year
- similarity threshold
- detected glacier-like area
- Earth Engine map tile URL

---

## 2. Start the Frontend

Open a second terminal.

From the project root:

```bash
cd frontend
python3 -m http.server 8000
```

If already inside the `frontend` directory, simply run:

```bash
python3 -m http.server 8000
```

Open the application in a browser:

```text
http://localhost:8000
```

---

# Using the Application

1. Open the Glacier Explorer.
2. Select a year between **2017 and 2024**.
3. Click **View Year**.
4. The frontend sends the selected year to the Flask API.
5. Google Earth Engine performs the embedding analysis.
6. The detected glacier-like area is displayed on the map.
7. The calculated area is displayed in km².

For example, the validated 2019 result is approximately:

```text
10.71 km²
```

---

# Current Prototype Limitations

This application is a prototype designed to demonstrate interactive glacier-change visualisation.

The current method:

- focuses on Rob Roy Glacier;
- uses manually selected 2017 reference polygons;
- uses a fixed similarity threshold of 0.80;
- identifies areas similar to the glacier/snow reference embedding;
- does not independently classify confirmed glacier boundaries;
- does not determine the physical cause of detected changes.

For this reason, results are described as **detected glacier-like area** rather than confirmed glacier extent or glacier melt.

---

# Technologies

- Google Earth Engine
- Google Satellite Embedding V1
- Python
- Flask
- Flask-CORS
- JavaScript
- Leaflet
- HTML
- CSS
