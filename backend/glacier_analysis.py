import ee

# Replace with your actual Google Cloud / Earth Engine project ID
PROJECT_ID = "studied-market-509102-a7"

ee.Initialize(project=PROJECT_ID)

# ---------------------------------------------------------
# SETTINGS
# ---------------------------------------------------------

REFERENCE_YEAR = 2017
SIMILARITY_THRESHOLD = 0.80
GLACIER_SIMILARITY_THRESHOLD = 0.80
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

# ---------------------------------------------------------
# DYNAMIC REFERENCE CANDIDATES - VERSION 1
# ---------------------------------------------------------

def get_dynamic_reference_candidates(study_area):

    # Rob Roy summer following the 2017 reference year
    start = "2017-12-01"
    end = "2018-03-01"

    # Dynamic World is derived from Sentinel-2 and provides
    # a probability for the snow_and_ice class.
    dynamic_world = (
        ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
        .filterBounds(study_area)
        .filterDate(start, end)
        .select("snow_and_ice")
    )

    # For every Dynamic World observation:
    # 1 = high-confidence snow/ice
    # 0 = not high-confidence snow/ice
    high_confidence_snow = dynamic_world.map(
        lambda image: image.gte(0.70)
    )

    # Calculate the proportion of observations in which
    # each pixel was high-confidence snow/ice.
    snow_persistence = (
        high_confidence_snow
        .mean()
        .clip(study_area)
    )

    # -----------------------------------------------------
    # DYNAMIC WORLD DIAGNOSTICS FOR MANUAL REFERENCE
    # -----------------------------------------------------

    # Mean snow/ice probability across the summer period.
    mean_snow_probability = (
        dynamic_world
        .mean()
        .clip(study_area)
    )

    # -----------------------------------------------------
    # LOCAL MEAN-SUMMER SNOW PROBABILITY THRESHOLD
    # -----------------------------------------------------

    # Calculate the 75th percentile of mean summer snow/ice
    # probability within the user's study area.
    snow_probability_stats = mean_snow_probability.reduceRegion(
        reducer=ee.Reducer.percentile([75]),
        geometry=study_area,
        scale=10,
        maxPixels=1e9,
        tileScale=4
    )

    snow_probability_threshold = ee.Number(
        snow_probability_stats.get("snow_and_ice")
    )

    # Keep pixels in the upper 25% of local mean summer
    # snow/ice probability.
    mean_snow_candidate_mask = (
        mean_snow_probability
        .gte(snow_probability_threshold)
    )

    # -----------------------------------------------------
    # MEAN SUMMER SNOW PROBABILITY DISTRIBUTION
    # -----------------------------------------------------

    probability_percentiles = ee.Reducer.percentile([
        10, 25, 50, 75, 90
    ])

    # Distribution inside Jasper's manual reference polygons.
    manual_probability_percentiles = (
        mean_snow_probability.reduceRegion(
            reducer=probability_percentiles,
            geometry=SNOW_REFERENCE,
            scale=10,
            maxPixels=1e9,
            tileScale=4
        )
    )

    # Distribution across the whole user-drawn study area.
    study_area_probability_percentiles = (
        mean_snow_probability.reduceRegion(
            reducer=probability_percentiles,
            geometry=study_area,
            scale=10,
            maxPixels=1e9,
            tileScale=4
        )
    )

    # Check Dynamic World snow probability inside Jasper's
    # manually selected reference polygons.
    manual_snow_probability_stats = (
        mean_snow_probability.reduceRegion(
            reducer=ee.Reducer.mean().combine(
                reducer2=ee.Reducer.max(),
                sharedInputs=True
            ),
            geometry=SNOW_REFERENCE,
            scale=10,
            maxPixels=1e9,
            tileScale=4
        )
    )

    # Check persistence inside Jasper's manually selected
    # reference polygons.
    manual_persistence_stats = (
        snow_persistence.reduceRegion(
            reducer=ee.Reducer.mean().combine(
                reducer2=ee.Reducer.max(),
                sharedInputs=True
            ),
            geometry=SNOW_REFERENCE,
            scale=10,
            maxPixels=1e9,
            tileScale=4
        )
    )

    # Keep pixels that were high-confidence snow/ice
    # in at least 60% of the summer observations.
    persistent_snow_mask = snow_persistence.gte(0.60)

    # Get elevation for the selected study area
    elevation = (
        ee.Image("USGS/SRTMGL1_003")
        .select("elevation")
        .clip(study_area)
    )

    elevation_stats = elevation.reduceRegion(
        reducer=ee.Reducer.percentile([70]),
        geometry=study_area,
        scale=30,
        maxPixels=1e9,
        tileScale=4
    )

    elevation_threshold = ee.Number(
        elevation_stats.get("elevation")
    )

    # Calculate terrain aspect from the elevation data.
    # Aspect is measured clockwise from north:
    # 0 = north, 90 = east, 180 = south, 270 = west.
    aspect = ee.Terrain.aspect(elevation)

    # For the Rob Roy test, prefer south-facing terrain.
    # 135-225 degrees = southeast through south to southwest.
    south_facing = (
        aspect
        .gte(135)
        .And(aspect.lte(225))
    )

    # Candidate mask after persistence + elevation,
    # but BEFORE the aspect filter.
    elevation_candidate_mask = (
        mean_snow_candidate_mask
        .And(elevation.gte(elevation_threshold))
    )

    # Candidates must be persistent snow/ice,
    # within the upper 30% of local elevation,
    # AND south-facing.
    candidate_mask = (
        mean_snow_candidate_mask
        .And(elevation.gte(elevation_threshold))
        .And(south_facing)
        .selfMask()
        .rename("reference_candidate")
    )

    persistence_stats = snow_persistence.reduceRegion(
        reducer=ee.Reducer.minMax(),
        geometry=study_area,
        scale=10,
        maxPixels=1e9,
        tileScale=4
    )

    print("Dynamic World images:", dynamic_world.size().getInfo())
    print("Snow persistence stats:", persistence_stats.getInfo())
    print("Elevation stats:", elevation_stats.getInfo())
    print(
        "70th percentile elevation:",
        elevation_threshold.getInfo()
    )

    # Calculate candidate area for testing
    candidate_area_image = (
        ee.Image.pixelArea()
        .divide(1e6)
        .rename("area")
        .updateMask(candidate_mask)
    )

    area_result = candidate_area_image.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=study_area,
        scale=10,
        maxPixels=1e9,
        tileScale=4
    )

    candidate_area = ee.Number(
        ee.Algorithms.If(
            area_result.contains("area"),
            area_result.get("area"),
            0
        )
    )

    # -----------------------------------------------------
    # COMPARE AUTOMATIC CANDIDATES WITH MANUAL REFERENCE
    # -----------------------------------------------------

    # Total area of Jasper's manually selected reference polygons.
    manual_area_image = (
        ee.Image.pixelArea()
        .divide(1e6)
        .rename("area")
    )

    manual_area_result = manual_area_image.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=SNOW_REFERENCE,
        scale=10,
        maxPixels=1e9,
        tileScale=4
    )

    manual_area = ee.Number(
        manual_area_result.get("area")
    )

    # 1. Persistence-only overlap.
    persistence_overlap_result = (
        ee.Image.pixelArea()
        .divide(1e6)
        .rename("area")
        .updateMask(persistent_snow_mask)
        .reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=SNOW_REFERENCE,
            scale=10,
            maxPixels=1e9,
            tileScale=4
        )
    )

    persistence_overlap = ee.Number(
        ee.Algorithms.If(
            persistence_overlap_result.contains("area"),
            persistence_overlap_result.get("area"),
            0
        )
    )

    persistence_overlap_percent = (
        persistence_overlap
        .divide(manual_area)
        .multiply(100)
    )

    # 2. Persistence + elevation overlap.
    elevation_overlap_result = (
        ee.Image.pixelArea()
        .divide(1e6)
        .rename("area")
        .updateMask(elevation_candidate_mask)
        .reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=SNOW_REFERENCE,
            scale=10,
            maxPixels=1e9,
            tileScale=4
        )
    )

    elevation_overlap = ee.Number(
        ee.Algorithms.If(
            elevation_overlap_result.contains("area"),
            elevation_overlap_result.get("area"),
            0
        )
    )

    elevation_overlap_percent = (
        elevation_overlap
        .divide(manual_area)
        .multiply(100)
    )

    # 3. Persistence + elevation + aspect overlap.
    overlap_area_result = (
        ee.Image.pixelArea()
        .divide(1e6)
        .rename("area")
        .updateMask(candidate_mask)
        .reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=SNOW_REFERENCE,
            scale=10,
            maxPixels=1e9,
            tileScale=4
        )
    )

    overlap_area = ee.Number(
        ee.Algorithms.If(
            overlap_area_result.contains("area"),
            overlap_area_result.get("area"),
            0
        )
    )

    manual_overlap_percent = (
        overlap_area
        .divide(manual_area)
        .multiply(100)
    )

    mean_snow_overlap_result = (
        ee.Image.pixelArea()
        .divide(1e6)
        .rename("area")
        .updateMask(mean_snow_candidate_mask)
        .reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=SNOW_REFERENCE,
            scale=10,
            maxPixels=1e9,
            tileScale=4
        )
    )

    mean_snow_overlap = ee.Number(
        ee.Algorithms.If(
            mean_snow_overlap_result.contains("area"),
            mean_snow_overlap_result.get("area"),
            0
        )
    )

    mean_snow_overlap_percent = (
        mean_snow_overlap
        .divide(manual_area)
        .multiply(100)
    )

    print("Manual reference area:", manual_area.getInfo())
    print("Automatic/manual overlap area:", overlap_area.getInfo())
    print(
        "Persistence-only manual overlap:",
        persistence_overlap_percent.getInfo(),
        "%"
    )
    print(
        "Persistence + elevation manual overlap:",
        elevation_overlap_percent.getInfo(),
        "%"
    )
    print(
        "Persistence + elevation + aspect manual overlap:",
        manual_overlap_percent.getInfo(),
        "%"
    )

    print(
        "Manual reference snow probability stats:",
        manual_snow_probability_stats.getInfo()
    )

    print(
        "Manual reference persistence stats:",
        manual_persistence_stats.getInfo()
    )

    print(
        "Manual reference probability percentiles:",
        manual_probability_percentiles.getInfo()
    )

    print(
        "Study area probability percentiles:",
        study_area_probability_percentiles.getInfo()
    )

    print(
        "Local P75 snow filter manual overlap:",
        mean_snow_overlap_percent.getInfo(),
        "%"
    )

    print(
        "Local P75 snow threshold:",
        snow_probability_threshold.getInfo()
    )

    # Yellow so we can distinguish this from:
    # cyan = normal analysis
    # magenta = dynamic study-area analysis
    map_info = candidate_mask.getMapId({
        "min": 1,
        "max": 1,
        "palette": ["FFFF00"]
    })

    return {
        "candidateArea": candidate_area.getInfo(),
        "snowConfidenceThreshold": 0.70,
        "persistenceThreshold": 0.60,
        "elevationPercentile": 70,
        "minimumCandidateElevation": elevation_threshold.getInfo(),
        "aspectMinimum": 135,
        "aspectMaximum": 225,
        "manualReferenceArea": manual_area.getInfo(),
        "manualOverlapArea": overlap_area.getInfo(),
        "manualReferenceCapturedPercent": manual_overlap_percent.getInfo(),
        "persistenceManualOverlapPercent": persistence_overlap_percent.getInfo(),
        "elevationManualOverlapPercent": elevation_overlap_percent.getInfo(),
        "snowProbabilityPercentile": 75,
        "snowProbabilityThreshold": snow_probability_threshold.getInfo(),
        "meanSnowManualOverlapPercent": mean_snow_overlap_percent.getInfo(),
        "startDate": start,
        "endDate": end,
        "tileUrl": map_info["tile_fetcher"].url_format
    }

def calculate_automatic_reference_glacier(year, study_area):
    """
    Experimental dynamic glacier analysis.

    Builds the 2017 Satellite Embedding reference automatically
    from Dynamic World + elevation + aspect candidate pixels,
    rather than Jasper's manual SNOW_REFERENCE polygons.
    """

    # -----------------------------------------------------
    # 1. BUILD AUTOMATIC REFERENCE CANDIDATES
    # -----------------------------------------------------

    start = "2017-12-01"
    end = "2018-03-01"

    dynamic_world = (
        ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
        .filterBounds(study_area)
        .filterDate(start, end)
        .select("snow_and_ice")
    )

    # Mean summer snow/ice probability.
    mean_snow_probability = (
        dynamic_world
        .mean()
        .clip(study_area)
    )

    # Local P75 threshold.
    snow_probability_stats = mean_snow_probability.reduceRegion(
        reducer=ee.Reducer.percentile([75]),
        geometry=study_area,
        scale=10,
        maxPixels=1e9,
        tileScale=4
    )

    snow_probability_threshold = ee.Number(
        snow_probability_stats.get("snow_and_ice")
    )

    mean_snow_candidate_mask = (
        mean_snow_probability
        .gte(snow_probability_threshold)
    )

    # -----------------------------------------------------
    # 2. ELEVATION FILTER
    # -----------------------------------------------------

    elevation = (
        ee.Image("USGS/SRTMGL1_003")
        .select("elevation")
        .clip(study_area)
    )

    elevation_stats = elevation.reduceRegion(
        reducer=ee.Reducer.percentile([70]),
        geometry=study_area,
        scale=30,
        maxPixels=1e9,
        tileScale=4
    )

    elevation_threshold = ee.Number(
        elevation_stats.get("elevation")
    )

    # -----------------------------------------------------
    # 3. ASPECT FILTER
    # -----------------------------------------------------

    aspect = ee.Terrain.aspect(elevation)

    south_facing = (
        aspect
        .gte(135)
        .And(aspect.lte(225))
    )

    candidate_mask = (
        mean_snow_candidate_mask
        .And(elevation.gte(elevation_threshold))
        .And(south_facing)
    )

    # -----------------------------------------------------
    # 4. BUILD AUTOMATIC 2017 EMBEDDING REFERENCE
    # -----------------------------------------------------

    reference_embedding = get_dynamic_embedding(
        REFERENCE_YEAR,
        study_area
    )

    # Only use pixels selected by the automatic method.
    candidate_embedding = reference_embedding.updateMask(
        candidate_mask
    )

    # Mean 64-dimensional embedding across candidate pixels.
    reference_values = candidate_embedding.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=study_area,
        scale=SCALE,
        maxPixels=1e9,
        tileScale=4
    )

    # Convert the 64 mean values back into an image.
    reference_image = ee.Image.constant([
        ee.Number(reference_values.get(band))
        for band in BANDS
    ]).rename(BANDS)

    # Normalise the 64D reference vector.
    reference_magnitude = (
        reference_image
        .pow(2)
        .reduce(ee.Reducer.sum())
        .sqrt()
    )

    normalised_reference = (
        reference_image
        .divide(reference_magnitude)
    )

    # -----------------------------------------------------
    # COMPARE AUTOMATIC REFERENCE WITH MANUAL REFERENCE
    # -----------------------------------------------------

    # Build the existing Jasper/manual 2017 reference.
    manual_reference = create_reference()

    # Compare the two normalised 64-dimensional vectors.
    reference_similarity = (
        normalised_reference
        .multiply(manual_reference)
        .reduce(ee.Reducer.sum())
        .rename("reference_similarity")
    )

    # The reference vectors are constant images, so sample
    # the similarity at any point inside the study area.
    reference_similarity_value = reference_similarity.reduceRegion(
        reducer=ee.Reducer.first(),
        geometry=study_area,
        scale=SCALE,
        maxPixels=1e9
    ).get("reference_similarity")


    print(
        "Manual vs automatic reference similarity:",
        ee.Number(reference_similarity_value).getInfo()
    )

    # -----------------------------------------------------
    # 5. ANALYSE SELECTED YEAR
    # -----------------------------------------------------

    analysis_embedding = get_dynamic_embedding(
        year,
        study_area
    )

    glacier_similarity = (
        analysis_embedding
        .multiply(normalised_reference)
        .reduce(ee.Reducer.sum())
        .rename("glacier_similarity")
    )

    glacier_like_mask = (
        glacier_similarity
        .gte(GLACIER_SIMILARITY_THRESHOLD)
    )

    glacier_like = (
        glacier_like_mask
        .selfMask()
        .rename("glacier_like")
    )

    # -----------------------------------------------------
    # 6. CALCULATE AREA
    # -----------------------------------------------------

    area_image = (
        ee.Image.pixelArea()
        .divide(1e6)
        .rename("area")
        .updateMask(glacier_like_mask)
    )

    area_result = area_image.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=study_area,
        scale=SCALE,
        maxPixels=1e9,
        tileScale=4
    )

    glacier_area = ee.Number(
        ee.Algorithms.If(
            area_result.contains("area"),
            area_result.get("area"),
            0
        )
    )

    # -----------------------------------------------------
    # 7. CANDIDATE AREA
    # -----------------------------------------------------

    candidate_area_result = (
        ee.Image.pixelArea()
        .divide(1e6)
        .rename("area")
        .updateMask(candidate_mask)
        .reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=study_area,
            scale=10,
            maxPixels=1e9,
            tileScale=4
        )
    )

    candidate_area = ee.Number(
        ee.Algorithms.If(
            candidate_area_result.contains("area"),
            candidate_area_result.get("area"),
            0
        )
    )

    # -----------------------------------------------------
    # 8. MAP
    # -----------------------------------------------------

    map_info = glacier_like.getMapId({
        "min": 1,
        "max": 1,
        "palette": ["00FF00"]
    })

    return {
        "year": year,
        "referenceYear": REFERENCE_YEAR,
        "threshold": GLACIER_SIMILARITY_THRESHOLD,

        "area": glacier_area.getInfo(),

        "referenceMethod": "automatic",
        "candidateArea": candidate_area.getInfo(),
        "manualAutomaticReferenceSimilarity": ee.Number(reference_similarity_value).getInfo(),

        "snowProbabilityPercentile": 75,
        "snowProbabilityThreshold":
            snow_probability_threshold.getInfo(),

        "elevationPercentile": 70,
        "minimumCandidateElevation":
            elevation_threshold.getInfo(),

        "aspectMinimum": 135,
        "aspectMaximum": 225,

        "tileUrl": map_info["tile_fetcher"].url_format
    }