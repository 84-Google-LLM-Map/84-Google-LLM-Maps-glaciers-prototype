"""Marmolada case study adapted from the team's Rob Roy Python script.

DRAFT: science-team reference polygons are required before analysis can run.
Place this file in backend/ alongside glacier_analysis.py. It is standalone;
no Flask or frontend changes are required for this case-study task.

After filling SNOW_REFERENCE_COORDINATES with reviewed MultiPolygon coordinates:
    python backend/marmolada_analysis.py 2021
    python backend/marmolada_analysis.py 2023
Use the project's existing earthengine-api dependency and authenticated account.

Method retained: fixed 2017 reference, 64 bands, threshold 0.80, 10 m scale.
The threshold, reference patches and provisional 5 km study radius need science
review. Area includes ALL matching pixels in that radius, not just the failed ice.
Annual embeddings cannot isolate short-term precursors; 2022 includes the event
within its calendar-year summary. Results are glacier-like similarity, not a
collapse probability, confirmed glacier boundary, or measured ice-volume loss.

Location/event source: https://doi.org/10.1029/2025GL121279
Dataset: https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_SATELLITE_EMBEDDING_V1_ANNUAL
"""
import argparse
import json
import math
import os

PROJECT_ID = os.environ.get("EE_PROJECT_ID", "studied-market-509102-a7")
REFERENCE_YEAR = 2017
SIMILARITY_THRESHOLD = 0.80
SCALE = 10
MIN_YEAR, MAX_YEAR = 2017, 2024
COLLAPSE_DATE = "2022-07-03"
# Published location near Punta Rocca, in longitude, latitude order.
MARMOLADA_CENTRE = [11.857975, 46.43522]
STUDY_RADIUS_M = 5000  # Provisional: retained from Rob Roy; not a glacier boundary.
BANDS = [f"A{i:02d}" for i in range(64)]

# SCIENCE TEAM TODO: paste reviewed snow/ice patches for the 2017 reference.
# MultiPolygon nesting: [ [ [ [lon, lat], ..., [first_lon, first_lat] ] ] ]
# Use clean snow/ice in 2017 INSIDE the study area. Do not reuse Rob Roy patches.
SNOW_REFERENCE_COORDINATES = []


def validate_settings(year):
    if type(year) is not int or not MIN_YEAR <= year <= MAX_YEAR:
        raise ValueError("Year must be an integer between 2017 and 2024.")
    if not SNOW_REFERENCE_COORDINATES:
        raise ValueError(
            "Reference polygons pending science-team input. Fill "
            "SNOW_REFERENCE_COORDINATES with reviewed Marmolada 2017 "
            "snow/ice MultiPolygon coordinates before running analysis."
        )


def get_embedding(ee, year, study_area):
    start = ee.Date.fromYMD(year, 1, 1)
    collection = (ee.ImageCollection("GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL")
                  .filterDate(start, start.advance(1, "year"))
                  .filterBounds(study_area))
    if collection.size().getInfo() == 0:
        raise ValueError(f"No embedding images found for {year} in the study area.")
    return collection.mosaic().select(BANDS).clip(study_area)


def create_reference(ee, study_area, snow_reference):
    embedding = get_embedding(ee, REFERENCE_YEAR, study_area)
    reference_values = embedding.reduceRegion(
        reducer=ee.Reducer.mean(), geometry=snow_reference,
        scale=SCALE, maxPixels=1e7, tileScale=4
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
    validate_settings(year)
    # Lazy initialization lets the missing-polygon message appear without login.
    import ee
    ee.Initialize(project=PROJECT_ID)
    study_area = ee.Geometry.Point(MARMOLADA_CENTRE).buffer(STUDY_RADIUS_M)
    snow_reference = ee.Geometry.MultiPolygon(SNOW_REFERENCE_COORDINATES)
    if not study_area.contains(snow_reference, 1).getInfo():
        raise ValueError("All reference polygons must be inside the study area.")
    reference = create_reference(ee, study_area, snow_reference)
    embedding = get_embedding(ee, year, study_area)
    similarity = (embedding.multiply(reference).reduce(ee.Reducer.sum())
                  .rename("glacier_similarity"))
    glacier_mask = similarity.gte(SIMILARITY_THRESHOLD)
    glacier_like = glacier_mask.selfMask().rename("glacier_like")
    # Reject wholly missing analysis coverage rather than report false zero area.
    coverage = embedding.select("A00").reduceRegion(
        reducer=ee.Reducer.count(), geometry=study_area,
        scale=SCALE, maxPixels=1e9, tileScale=4
    ).getInfo().get("A00")
    if not coverage:
        raise ValueError("No valid embedding pixels in the analysis study area.")
    area_image = (ee.Image.pixelArea().divide(1e6).rename("area")
                  .updateMask(glacier_mask))
    area_result = area_image.reduceRegion(
        reducer=ee.Reducer.sum(), geometry=study_area,
        scale=SCALE, maxPixels=1e9, tileScale=4
    ).getInfo()
    area = area_result.get("area")
    if area is None:
        area = 0.0
    map_info = glacier_like.getMapId({"min": 1, "max": 1, "palette": ["00FFFF"]})
    return {
        "glacier": "Marmolada", "year": year,
        "referenceYear": REFERENCE_YEAR, "threshold": SIMILARITY_THRESHOLD,
        "area": area, "tileUrl": map_info["tile_fetcher"].url_format,
        "collapseDate": COLLAPSE_DATE,
        "studyCentre": MARMOLADA_CENTRE, "studyRadiusM": STUDY_RADIUS_M,
        "interpretation": "Detected glacier-like area in km2; not collapse prediction.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("year", type=int, help="Analysis year, 2017-2024")
    args = parser.parse_args()
    try:
        print(json.dumps(calculate_glacier(args.year), indent=2, allow_nan=False))
    except Exception as exc:
        parser.exit(1, f"Analysis not completed: {exc}\n")

