"""Provisional Marmolada demo adapted from the team's Rob Roy script.

Place in backend/ alongside glacier_analysis.py. To select this analysis in
app.py, use: from marmolada_analysis import calculate_glacier

Run directly from the project root:
    python backend/marmolada_analysis.py 2021
    python backend/marmolada_analysis.py 2023

This version runs real Earth Engine calculations using an ARTIFICIAL reference
rectangle, not a verified snow/ice patch. It requires the existing earthengine-api
dependency and an authenticated account with access to the configured project.
The area and overlay are unvalidated demo outputs, not glacier measurements.

Applied science students must review or replace the 2017 reference polygons,
review the threshold and study area, and validate the outputs. Keep demoOnly
true until that work is complete. Display the returned warning in the app;
returning metadata alone does not change frontend labels or the map centre.

Method retained: fixed 2017 reference, 64 bands, threshold 0.80, 10 m scale.
Area includes all matching pixels within a provisional 5 km study radius.
Annual embeddings cannot isolate short-term precursors; the 2022 annual image
includes the event year. Outputs are not collapse predictions, confirmed glacier
boundaries, or measurements of ice-volume loss.
"""

import argparse
import json
import math
import os
import sys


PROJECT_ID = os.environ.get("EE_PROJECT_ID", "studied-market-509102-a7")
REFERENCE_YEAR = 2017
SIMILARITY_THRESHOLD = 0.80
SCALE = 10
MIN_YEAR, MAX_YEAR = 2017, 2024
COLLAPSE_DATE = "2022-07-03"

# Coordinates are in longitude, latitude order.
MARMOLADA_CENTRE = [11.857975, 46.43522]
STUDY_RADIUS_M = 5000  # Provisional study area, not a glacier boundary.
BANDS = [f"A{i:02d}" for i in range(64)]

DEMO_WARNING = (
    "DEMO ONLY: artificial, unverified reference polygon. "
    "Area and overlay require applied science review and are not "
    "validated glacier measurements or evidence of collapse."
)

# DEMO ONLY: artificial rectangle near the Marmolada centre.
# Not selected from 2017 imagery or verified as snow/ice.
# Replace with reviewed 2017 snow/ice patches inside the study area.
# MultiPolygon nesting: polygons -> rings -> [longitude, latitude] points.
# Do not reuse Rob Roy's reference polygons for Marmolada.
SNOW_REFERENCE_COORDINATES = [
    [
        [
            [11.8575, 46.4350],
            [11.8580, 46.4350],
            [11.8580, 46.4354],
            [11.8575, 46.4354],
            [11.8575, 46.4350],
        ]
    ]
]


def validate_settings(year):
    """Reject unsupported years and missing reference coordinates."""
    if type(year) is not int or not MIN_YEAR <= year <= MAX_YEAR:
        raise ValueError("Year must be an integer between 2017 and 2024.")
    if not SNOW_REFERENCE_COORDINATES:
        raise ValueError(
            "Reference coordinates are missing. Fill SNOW_REFERENCE_COORDINATES "
            "before running analysis. Verified results require reviewed "
            "Marmolada 2017 snow/ice polygons from the applied science team."
        )


def get_embedding(ee, year, study_area):
    """Load the annual embedding within the study area."""
    start = ee.Date.fromYMD(year, 1, 1)
    collection = (
        ee.ImageCollection("GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL")
        .filterDate(start, start.advance(1, "year"))
        .filterBounds(study_area)
    )
    if collection.size().getInfo() == 0:
        raise ValueError(f"No embedding images found for {year} in the study area.")
    return collection.mosaic().select(BANDS).clip(study_area)


def create_reference(ee, study_area, snow_reference):
    """Create a normalised reference vector from the 2017 patches."""
    embedding = get_embedding(ee, REFERENCE_YEAR, study_area)
    reference_values = embedding.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=snow_reference,
        scale=SCALE,
        maxPixels=1e7,
        tileScale=4,
    ).getInfo()
    values = [reference_values.get(band) for band in BANDS]
    if any(v is None or not math.isfinite(v) for v in values):
        raise ValueError("Reference patches lack valid data in one or more bands.")
    if sum(v * v for v in values) <= 0:
        raise ValueError("Reference vector has zero magnitude; review the patches.")
    reference_image = ee.Image.constant(values).rename(BANDS)
    magnitude = reference_image.pow(2).reduce(ee.Reducer.sum()).sqrt()
    return reference_image.divide(magnitude)


def calculate_glacier(year):
    """Return the existing API fields plus explicit demo metadata."""
    validate_settings(year)

    # Earth Engine is imported and initialised here, on the first
    # Marmolada request, rather than when this module is imported.
    # init_earth_engine() does nothing if it has already run.
    import ee
    from ee_auth import init_earth_engine

    init_earth_engine()

    study_area = ee.Geometry.Point(MARMOLADA_CENTRE).buffer(STUDY_RADIUS_M)
    snow_reference = ee.Geometry.MultiPolygon(SNOW_REFERENCE_COORDINATES)
    if not study_area.contains(snow_reference, 1).getInfo():
        raise ValueError("All reference polygons must be inside the study area.")

    reference = create_reference(ee, study_area, snow_reference)
    embedding = get_embedding(ee, year, study_area)
    similarity = (
        embedding.multiply(reference)
        .reduce(ee.Reducer.sum())
        .rename("glacier_similarity")
    )
    glacier_mask = similarity.gte(SIMILARITY_THRESHOLD)
    glacier_like = glacier_mask.selfMask().rename("glacier_like")

    # Missing coverage must not be reported as a genuine zero-area result.
    coverage = embedding.select("A00").reduceRegion(
        reducer=ee.Reducer.count(),
        geometry=study_area,
        scale=SCALE,
        maxPixels=1e9,
        tileScale=4,
    ).getInfo().get("A00")
    if not coverage:
        raise ValueError("No valid embedding pixels in the analysis study area.")

    area_image = (
        ee.Image.pixelArea()
        .divide(1e6)
        .rename("area")
        .updateMask(glacier_mask)
    )
    area_result = area_image.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=study_area,
        scale=SCALE,
        maxPixels=1e9,
        tileScale=4,
    ).getInfo()
    area = area_result.get("area")
    if area is None:
        area = 0.0
    if not math.isfinite(area) or area < 0:
        raise ValueError("Earth Engine returned an invalid area value.")

    map_info = glacier_like.getMapId(
        {"min": 1, "max": 1, "palette": ["00FFFF"]}
    )
    return {
        # Existing Rob Roy API fields are preserved.
        "year": year,
        "referenceYear": REFERENCE_YEAR,
        "threshold": SIMILARITY_THRESHOLD,
        "area": area,
        "tileUrl": map_info["tile_fetcher"].url_format,
        # Additional context for the Marmolada demo.
        "glacier": "Marmolada",
        "areaUnit": "km2",
        "collapseDate": COLLAPSE_DATE,
        "studyCentre": MARMOLADA_CENTRE,
        "studyRadiusM": STUDY_RADIUS_M,
        "demoOnly": True,
        "referenceStatus": "Unverified artificial placeholder",
        "warning": DEMO_WARNING,
        "interpretation": (
            "Area in km2 of pixels similar to an unverified 2017 reference "
            "patch within the study radius; not a validated glacier area, "
            "collapse prediction, or measurement of ice-volume loss."
        ),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("year", type=int, help="Analysis year, 2017-2024")
    args = parser.parse_args()
    # Keep stdout as JSON on success; show the warning separately on stderr.
    print(DEMO_WARNING, file=sys.stderr)
    try:
        result = calculate_glacier(args.year)
        print(json.dumps(result, indent=2, allow_nan=False))
    except Exception as exc:
        parser.exit(1, f"Analysis not completed: {exc}\n")