import ee

# Replace with your actual Google Cloud / Earth Engine project ID
PROJECT_ID = "studied-market-509102-a7"

ee.Initialize(project=PROJECT_ID)

# ---------------------------------------------------------
# SETTINGS
# ---------------------------------------------------------

REFERENCE_YEAR = 2017
SIMILARITY_THRESHOLD = 0.80
SCALE = 10

# Rob Roy Glacier
ROB_ROY = ee.Geometry.Point([168.741, -44.455])
STUDY_AREA = ROB_ROY.buffer(5000)

# Satellite Embedding V1
EMBEDDINGS = ee.ImageCollection(
    "GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL"
)

BANDS = [f"A{i:02d}" for i in range(64)]


# ---------------------------------------------------------
# 2017 REFERENCE POLYGONS
# Taken from the Rob Roy master analysis
# ---------------------------------------------------------

SNOW_REFERENCE = ee.Geometry.MultiPolygon([
    [[
        [168.7194032476306, -44.459435712814326],
        [168.71476839045286, -44.460048323135716],
        [168.7171716497302, -44.4616410798897],
        [168.7194032476306, -44.459435712814326]
    ]],
    [[
        [168.73459290302867, -44.46069721090555],
        [168.73399208820933, -44.461922398648404],
        [168.73510788715953, -44.46140169699924],
        [168.73459290302867, -44.46069721090555]
    ]],
    [[
        [168.74407719410533, -44.452671595459066],
        [168.74369095600719, -44.453437446064676],
        [168.74497841633433, -44.452886034641004],
        [168.74407719410533, -44.452671595459066]
    ]]
])


# ---------------------------------------------------------
# GET EMBEDDING FOR ONE YEAR
# ---------------------------------------------------------

def get_embedding(year):
    start = ee.Date.fromYMD(year, 1, 1)
    end = start.advance(1, "year")

    return (
        EMBEDDINGS
        .filterDate(start, end)
        .filterBounds(STUDY_AREA)
        .mosaic()
        .select(BANDS)
        .clip(STUDY_AREA)
    )

# ---------------------------------------------------------
# GET EMBEDDING FOR A DYNAMIC STUDY AREA
# ---------------------------------------------------------

def get_dynamic_embedding(year, study_area):
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

def create_reference():

    embedding_2017 = get_embedding(REFERENCE_YEAR)

    reference_values = embedding_2017.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=SNOW_REFERENCE,
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

    # Normalise the reference vector
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

def calculate_glacier(year):

    reference = create_reference()

    embedding = get_embedding(year)

    # Similarity with fixed 2017 glacier reference
    similarity = (
        embedding
        .multiply(reference)
        .reduce(ee.Reducer.sum())
        .rename("glacier_similarity")
    )

    # >= 0.80 = glacier-like
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
        geometry=STUDY_AREA,
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

    return {
        "year": year,
        "referenceYear": REFERENCE_YEAR,
        "threshold": SIMILARITY_THRESHOLD,
        "area": area.getInfo(),
        "tileUrl": map_info["tile_fetcher"].url_format
    }

# ---------------------------------------------------------
# RUN DYNAMIC GLACIER ANALYSIS
# ---------------------------------------------------------

def calculate_dynamic_glacier(year, study_area):

    # Keep the existing manually selected
    # Rob Roy 2017 glacier reference
    reference = create_reference()

    # Use the user's drawn polygon as the study area
    embedding = get_dynamic_embedding(
        year,
        study_area
    )

    # Similarity with fixed 2017 glacier reference
    similarity = (
        embedding
        .multiply(reference)
        .reduce(ee.Reducer.sum())
        .rename("glacier_similarity")
    )

    # >= 0.80 = glacier-like
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
        "palette": ["FF00FF"]
    })

    return {
        "year": year,
        "referenceYear": REFERENCE_YEAR,
        "threshold": SIMILARITY_THRESHOLD,
        "area": area.getInfo(),
        "tileUrl": map_info["tile_fetcher"].url_format
    }