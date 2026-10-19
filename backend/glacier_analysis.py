import ee

from glaciers import get_glacier


# ---------------------------------------------------------
# EARTH ENGINE
# ---------------------------------------------------------

PROJECT_ID = "studied-market-509102-a7"

ee.Initialize(project=PROJECT_ID)


# ---------------------------------------------------------
# SETTINGS
# ---------------------------------------------------------

REFERENCE_YEAR = 2017
SIMILARITY_THRESHOLD = 0.80
SCALE = 10

EMBEDDINGS = ee.ImageCollection(
    "GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL"
)

BANDS = [f"A{i:02d}" for i in range(64)]


# ---------------------------------------------------------
# GET EMBEDDING FOR ONE YEAR
# ---------------------------------------------------------

def get_embedding(year, study_area):

    start = ee.Date.fromYMD(year, 1, 1)
    end = start.advance(1, "year")

    return (
        EMBEDDINGS
        .filterDate(start, end)
        .filterBounds(study_area)
        .mosaic()
        .select(BANDS)
        .clip(study_area)
    )


# ---------------------------------------------------------
# CREATE FIXED 2017 GLACIER REFERENCE
# ---------------------------------------------------------

def create_reference(study_area, snow_reference):

    embedding_2017 = get_embedding(
        REFERENCE_YEAR,
        study_area
    )

    reference_values = embedding_2017.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=snow_reference,
        scale=SCALE,
        maxPixels=1e7,
        tileScale=4
    )

    values = [
        reference_values.get(band)
        for band in BANDS
    ]

    reference_image = (
        ee.Image.constant(values)
        .rename(BANDS)
    )

    # Normalise reference vector
    magnitude = (
        reference_image
        .pow(2)
        .reduce(ee.Reducer.sum())
        .sqrt()
    )

    return reference_image.divide(magnitude)


# ---------------------------------------------------------
# RUN GLACIER ANALYSIS
# ---------------------------------------------------------

def calculate_glacier(glacier_id, year):

    # -----------------------------------------------------
    # GET SELECTED GLACIER
    # -----------------------------------------------------

    glacier = get_glacier(glacier_id)

    centre = ee.Geometry.Point(
        glacier["centre"]
    )

    study_area = centre.buffer(
        glacier["study_radius_m"]
    )

    snow_reference = ee.Geometry.MultiPolygon(
        glacier["reference_polygons"]
    )


    # -----------------------------------------------------
    # CREATE FIXED 2017 REFERENCE
    # -----------------------------------------------------

    reference = create_reference(
        study_area,
        snow_reference
    )


    # -----------------------------------------------------
    # GET SELECTED YEAR
    # -----------------------------------------------------

    embedding = get_embedding(
        year,
        study_area
    )


    # -----------------------------------------------------
    # SIMILARITY
    # -----------------------------------------------------

    similarity = (
        embedding
        .multiply(reference)
        .reduce(ee.Reducer.sum())
        .rename("glacier_similarity")
    )


    # -----------------------------------------------------
    # GLACIER-LIKE MASK
    # -----------------------------------------------------

    glacier_mask = similarity.gte(
        SIMILARITY_THRESHOLD
    )

    glacier_like = (
        glacier_mask
        .selfMask()
        .rename("glacier_like")
    )


    # -----------------------------------------------------
    # CALCULATE AREA
    # -----------------------------------------------------

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
        tileScale=4
    )

    area = ee.Number(
        ee.Algorithms.If(
            area_result.contains("area"),
            area_result.get("area"),
            0
        )
    )


    # -----------------------------------------------------
    # CREATE MAP TILE
    # -----------------------------------------------------

    map_info = glacier_like.getMapId({
        "min": 1,
        "max": 1,
        "palette": ["00FFFF"]
    })


    # -----------------------------------------------------
    # RETURN RESULT
    # -----------------------------------------------------

    return {
        "glacierId": glacier_id,
        "glacier": glacier["name"],
        "year": year,
        "referenceYear": REFERENCE_YEAR,
        "threshold": SIMILARITY_THRESHOLD,
        "area": area.getInfo(),
        "areaUnit": "km2",
        "studyCentre": glacier["centre"],
        "studyRadiusM": glacier["study_radius_m"],
        "tileUrl": map_info["tile_fetcher"].url_format
    }