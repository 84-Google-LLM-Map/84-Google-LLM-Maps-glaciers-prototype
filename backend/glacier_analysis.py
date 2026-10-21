import ee

from glaciers import (
    get_glacier,
    get_study_area,
    get_reference_geometry,
)


# ---------------------------------------------------------
# EARTH ENGINE
# ---------------------------------------------------------

from ee_auth import PROJECT_ID, init_earth_engine

init_earth_engine()


# ---------------------------------------------------------
# SETTINGS
# ---------------------------------------------------------

REFERENCE_YEAR = 2017
SIMILARITY_THRESHOLD = 0.80
GLACIER_SIMILARITY_THRESHOLD = 0.80
SCALE = 10

# Glacier whose manual polygons are used when no glacier
# is specified (keeps the original Rob Roy behaviour).
DEFAULT_GLACIER_ID = "rob-roy"

EMBEDDINGS = ee.ImageCollection(
    "GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL"
)

BANDS = [f"A{i:02d}" for i in range(64)]


# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------

def sum_area_km2(mask, geometry, scale=SCALE):
    """
    Sum the area (km²) of the pixels in `mask` inside `geometry`.
    Returns an ee.Number (0 if no pixels).
    """

    result = (
        ee.Image.pixelArea()
        .divide(1e6)
        .rename("area")
        .updateMask(mask)
        .reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=geometry,
            scale=scale,
            maxPixels=1e9,
            tileScale=4
        )
    )

    return ee.Number(
        ee.Algorithms.If(
            result.contains("area"),
            result.get("area"),
            0
        )
    )


def normalise(reference_image):
    """
    Scale a 64-band constant image to unit length so that a
    dot product with an embedding gives cosine similarity.
    """

    magnitude = (
        reference_image
        .pow(2)
        .reduce(ee.Reducer.sum())
        .sqrt()
    )

    return reference_image.divide(magnitude)


# ---------------------------------------------------------
# LOCATION-DEPENDENT SETTINGS (HEMISPHERE)
# ---------------------------------------------------------
#
# Glacier ice is easiest to separate from seasonal snow at the
# end of the local summer, and survives best on slopes facing
# away from the sun (poleward):
#
#   Southern hemisphere: Dec–Feb, south-facing (135–225°)
#   Northern hemisphere: Jul–Sep, north-facing (315–45°)
#
# The southern values are the original Rob Roy settings,
# so Rob Roy / Franz Josef results do not change.

HEMISPHERE_SETTINGS = {
    "south": {
        "start": "2017-12-01",
        "end": "2018-03-01",
        "aspectMinimum": 135,
        "aspectMaximum": 225,
    },
    "north": {
        "start": "2017-07-01",
        "end": "2017-10-01",
        "aspectMinimum": 315,
        "aspectMaximum": 45,
    },
}


def get_location_settings(study_area):
    """
    Pick the season and shaded aspect for a study area from
    the latitude of its centre.
    """

    latitude = ee.Number(
        study_area.centroid(maxError=1).coordinates().get(1)
    ).getInfo()

    hemisphere = "north" if latitude >= 0 else "south"

    return {
        "hemisphere": hemisphere,
        "latitude": latitude,
        **HEMISPHERE_SETTINGS[hemisphere],
    }


def shaded_aspect_mask(aspect, settings):
    """
    1 where the slope faces poleward (away from the sun).
    Aspect: 0 = north, 90 = east, 180 = south, 270 = west.
    """

    low = settings["aspectMinimum"]
    high = settings["aspectMaximum"]

    if low <= high:
        return aspect.gte(low).And(aspect.lte(high))

    # Range wraps through 0° (north), e.g. 315–45
    return aspect.gte(low).Or(aspect.lte(high))


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


# The dynamic version used to be a copy of get_embedding.
# Kept as an alias so existing calls still work.
get_dynamic_embedding = get_embedding


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

    return normalise(reference_image)


def create_manual_reference(glacier_id=DEFAULT_GLACIER_ID):
    """
    Build the manual (hand-drawn polygon) 2017 reference for a
    glacier from its configuration in glaciers.py.
    """

    return create_reference(
        get_study_area(glacier_id),
        get_reference_geometry(glacier_id)
    )


# ---------------------------------------------------------
# RUN GLACIER ANALYSIS
# ---------------------------------------------------------

def calculate_glacier(glacier_id, year):

    glacier = get_glacier(glacier_id)

    study_area = get_study_area(glacier_id)
    snow_reference = get_reference_geometry(glacier_id)

    # Fixed 2017 reference
    reference = create_reference(
        study_area,
        snow_reference
    )

    # Selected year
    embedding = get_embedding(
        year,
        study_area
    )

    # Similarity
    similarity = (
        embedding
        .multiply(reference)
        .reduce(ee.Reducer.sum())
        .rename("glacier_similarity")
    )

    # Glacier-like mask
    glacier_mask = similarity.gte(
        SIMILARITY_THRESHOLD
    )

    glacier_like = (
        glacier_mask
        .selfMask()
        .rename("glacier_like")
    )

    # Area
    area = sum_area_km2(glacier_mask, study_area)

    # Map tile
    map_info = glacier_like.getMapId({
        "min": 1,
        "max": 1,
        "palette": ["D9443A"]
    })

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


# ---------------------------------------------------------
# RUN DYNAMIC GLACIER ANALYSIS
# (user-drawn study area, manual reference)
# ---------------------------------------------------------

def calculate_dynamic_glacier(
    year,
    study_area,
    glacier_id=DEFAULT_GLACIER_ID
):

    # Manual 2017 reference from the selected glacier's polygons
    reference = create_manual_reference(glacier_id)

    # Use the user's drawn polygon as the study area
    embedding = get_embedding(
        year,
        study_area
    )

    similarity = (
        embedding
        .multiply(reference)
        .reduce(ee.Reducer.sum())
        .rename("glacier_similarity")
    )

    glacier_mask = similarity.gte(
        SIMILARITY_THRESHOLD
    )

    glacier_like = (
        glacier_mask
        .selfMask()
        .rename("glacier_like")
    )

    area = sum_area_km2(glacier_mask, study_area)

    map_info = glacier_like.getMapId({
        "min": 1,
        "max": 1,
        "palette": ["FF00FF"]
    })

    return {
        "glacierId": glacier_id,
        "year": year,
        "referenceYear": REFERENCE_YEAR,
        "threshold": SIMILARITY_THRESHOLD,
        "area": area.getInfo(),
        "tileUrl": map_info["tile_fetcher"].url_format
    }


# ---------------------------------------------------------
# DYNAMIC REFERENCE CANDIDATES - VERSION 1
# (diagnostic: compares automatic candidates against the
#  manual reference polygons of the selected glacier)
# ---------------------------------------------------------

def get_dynamic_reference_candidates(
    study_area,
    glacier_id=DEFAULT_GLACIER_ID
):

    # Manual reference polygons for the selected glacier
    # (previously the undefined global SNOW_REFERENCE).
    snow_reference = get_reference_geometry(glacier_id)

    # End of local summer for the 2017 reference year
    settings = get_location_settings(study_area)
    start = settings["start"]
    end = settings["end"]

    # Dynamic World is derived from Sentinel-2 and provides
    # a probability for the snow_and_ice class.
    dynamic_world = (
        ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
        .filterBounds(study_area)
        .filterDate(start, end)
        .select("snow_and_ice")
    )

    # 1 = high-confidence snow/ice, 0 = not
    high_confidence_snow = dynamic_world.map(
        lambda image: image.gte(0.70)
    )

    # Proportion of observations in which each pixel was
    # high-confidence snow/ice.
    snow_persistence = (
        high_confidence_snow
        .mean()
        .clip(study_area)
    )

    # Mean snow/ice probability across the summer period.
    mean_snow_probability = (
        dynamic_world
        .mean()
        .clip(study_area)
    )

    # Local P75 of mean summer snow/ice probability.
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

    # Probability distributions
    probability_percentiles = ee.Reducer.percentile([
        10, 25, 50, 75, 90
    ])

    manual_probability_percentiles = (
        mean_snow_probability.reduceRegion(
            reducer=probability_percentiles,
            geometry=snow_reference,
            scale=10,
            maxPixels=1e9,
            tileScale=4
        )
    )

    study_area_probability_percentiles = (
        mean_snow_probability.reduceRegion(
            reducer=probability_percentiles,
            geometry=study_area,
            scale=10,
            maxPixels=1e9,
            tileScale=4
        )
    )

    mean_max = ee.Reducer.mean().combine(
        reducer2=ee.Reducer.max(),
        sharedInputs=True
    )

    manual_snow_probability_stats = (
        mean_snow_probability.reduceRegion(
            reducer=mean_max,
            geometry=snow_reference,
            scale=10,
            maxPixels=1e9,
            tileScale=4
        )
    )

    manual_persistence_stats = (
        snow_persistence.reduceRegion(
            reducer=mean_max,
            geometry=snow_reference,
            scale=10,
            maxPixels=1e9,
            tileScale=4
        )
    )

    # High-confidence snow/ice in at least 60% of observations
    persistent_snow_mask = snow_persistence.gte(0.60)

    # Elevation
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

    # Aspect: 0 = north, 90 = east, 180 = south, 270 = west.
    # Keep poleward (shaded) slopes for this hemisphere.
    aspect = ee.Terrain.aspect(elevation)

    shaded_facing = shaded_aspect_mask(aspect, settings)

    # Persistence + elevation, before aspect
    elevation_candidate_mask = (
        mean_snow_candidate_mask
        .And(elevation.gte(elevation_threshold))
    )

    # Persistence + elevation + aspect
    candidate_mask = (
        elevation_candidate_mask
        .And(shaded_facing)
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

    # Areas
    candidate_area = sum_area_km2(candidate_mask, study_area)

    manual_area = ee.Number(
        ee.Image.pixelArea()
        .divide(1e6)
        .rename("area")
        .reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=snow_reference,
            scale=10,
            maxPixels=1e9,
            tileScale=4
        )
        .get("area")
    )

    def percent_of_manual(mask):
        return (
            sum_area_km2(mask, snow_reference)
            .divide(manual_area)
            .multiply(100)
        )

    overlap_area = sum_area_km2(candidate_mask, snow_reference)

    persistence_overlap_percent = percent_of_manual(persistent_snow_mask)
    elevation_overlap_percent = percent_of_manual(elevation_candidate_mask)
    manual_overlap_percent = percent_of_manual(candidate_mask)
    mean_snow_overlap_percent = percent_of_manual(mean_snow_candidate_mask)

    # One round trip to Earth Engine instead of ~20
    stats = ee.Dictionary({
        "dynamicWorldImages": dynamic_world.size(),
        "persistenceStats": persistence_stats,
        "elevationStats": elevation_stats,
        "manualSnowProbabilityStats": manual_snow_probability_stats,
        "manualPersistenceStats": manual_persistence_stats,
        "manualProbabilityPercentiles": manual_probability_percentiles,
        "studyAreaProbabilityPercentiles": study_area_probability_percentiles,

        "candidateArea": candidate_area,
        "minimumCandidateElevation": elevation_threshold,
        "manualReferenceArea": manual_area,
        "manualOverlapArea": overlap_area,
        "manualReferenceCapturedPercent": manual_overlap_percent,
        "persistenceManualOverlapPercent": persistence_overlap_percent,
        "elevationManualOverlapPercent": elevation_overlap_percent,
        "snowProbabilityThreshold": snow_probability_threshold,
        "meanSnowManualOverlapPercent": mean_snow_overlap_percent,
    }).getInfo()

    print("Dynamic reference candidate diagnostics:", stats)

    # Yellow, to distinguish from:
    # cyan = normal analysis, magenta = dynamic study-area analysis
    map_info = candidate_mask.getMapId({
        "min": 1,
        "max": 1,
        "palette": ["FFFF00"]
    })

    return {
        "glacierId": glacier_id,
        "candidateArea": stats["candidateArea"],
        "snowConfidenceThreshold": 0.70,
        "persistenceThreshold": 0.60,
        "elevationPercentile": 70,
        "minimumCandidateElevation": stats["minimumCandidateElevation"],
        "hemisphere": settings["hemisphere"],
        "aspectMinimum": settings["aspectMinimum"],
        "aspectMaximum": settings["aspectMaximum"],
        "manualReferenceArea": stats["manualReferenceArea"],
        "manualOverlapArea": stats["manualOverlapArea"],
        "manualReferenceCapturedPercent": stats["manualReferenceCapturedPercent"],
        "persistenceManualOverlapPercent": stats["persistenceManualOverlapPercent"],
        "elevationManualOverlapPercent": stats["elevationManualOverlapPercent"],
        "snowProbabilityPercentile": 75,
        "snowProbabilityThreshold": stats["snowProbabilityThreshold"],
        "meanSnowManualOverlapPercent": stats["meanSnowManualOverlapPercent"],
        "startDate": start,
        "endDate": end,
        "tileUrl": map_info["tile_fetcher"].url_format
    }


# ---------------------------------------------------------
# AUTOMATIC REFERENCE GLACIER ANALYSIS (EXPERIMENTAL)
# ---------------------------------------------------------

def calculate_automatic_reference_glacier(
    year,
    study_area,
    glacier_id=DEFAULT_GLACIER_ID
):
    """
    Experimental dynamic glacier analysis.

    Builds the 2017 Satellite Embedding reference automatically
    from Dynamic World + elevation + aspect candidate pixels
    inside the user's drawn study area, instead of the manual
    reference polygons.

    The manual reference of `glacier_id` is only used for a
    diagnostic similarity score between the two references.
    """

    # -----------------------------------------------------
    # 1. AUTOMATIC REFERENCE CANDIDATES
    # -----------------------------------------------------

    # End of local summer for the 2017 reference year
    settings = get_location_settings(study_area)
    start = settings["start"]
    end = settings["end"]

    dynamic_world = (
        ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
        .filterBounds(study_area)
        .filterDate(start, end)
        .select("snow_and_ice")
    )

    if dynamic_world.size().getInfo() == 0:
        return {
            "error": (
                "No Dynamic World imagery for the selected area "
                f"between {start} and {end}."
            )
        }

    mean_snow_probability = (
        dynamic_world
        .mean()
        .clip(study_area)
    )

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

    shaded_facing = shaded_aspect_mask(aspect, settings)

    candidate_mask = (
        mean_snow_candidate_mask
        .And(elevation.gte(elevation_threshold))
        .And(shaded_facing)
    )

    # Stop early if nothing passes the filters, otherwise the
    # reference vector below is all nulls and Earth Engine errors.
    candidate_area = sum_area_km2(
        candidate_mask.selfMask(),
        study_area
    )

    candidate_area_value = candidate_area.getInfo()

    if candidate_area_value == 0:
        return {
            "error": (
                "No reference candidate pixels found in the selected "
                "area. Try drawing a larger area that includes "
                "high-elevation snow or ice."
            )
        }

    # -----------------------------------------------------
    # 4. AUTOMATIC 2017 EMBEDDING REFERENCE
    # -----------------------------------------------------

    reference_embedding = get_embedding(
        REFERENCE_YEAR,
        study_area
    )

    candidate_embedding = reference_embedding.updateMask(
        candidate_mask
    )

    # Mean 64-dimensional embedding across candidate pixels
    reference_values = candidate_embedding.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=study_area,
        scale=SCALE,
        maxPixels=1e9,
        tileScale=4
    )

    reference_image = ee.Image.constant([
        ee.Number(reference_values.get(band))
        for band in BANDS
    ]).rename(BANDS)

    normalised_reference = normalise(reference_image)

    # -----------------------------------------------------
    # COMPARE AUTOMATIC REFERENCE WITH MANUAL REFERENCE
    # -----------------------------------------------------

    manual_reference = create_manual_reference(glacier_id)

    reference_similarity = (
        normalised_reference
        .multiply(manual_reference)
        .reduce(ee.Reducer.sum())
        .rename("reference_similarity")
    )

    # Both references are constant images, so any pixel
    # in the study area gives the same value.
    reference_similarity_value = reference_similarity.reduceRegion(
        reducer=ee.Reducer.first(),
        geometry=study_area,
        scale=SCALE,
        maxPixels=1e9
    ).get("reference_similarity")

    # -----------------------------------------------------
    # 5. ANALYSE SELECTED YEAR
    # -----------------------------------------------------

    analysis_embedding = get_embedding(
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
    # 6. AREA
    # -----------------------------------------------------

    glacier_area = sum_area_km2(glacier_like_mask, study_area)

    # One round trip for the remaining numbers
    stats = ee.Dictionary({
        "area": glacier_area,
        "manualAutomaticReferenceSimilarity": reference_similarity_value,
        "snowProbabilityThreshold": snow_probability_threshold,
        "minimumCandidateElevation": elevation_threshold,
    }).getInfo()

    print(
        "Manual vs automatic reference similarity:",
        stats["manualAutomaticReferenceSimilarity"]
    )

    # -----------------------------------------------------
    # 7. MAP
    # -----------------------------------------------------

    # Yellow = final experimental dynamic-analysis result
    map_info = glacier_like.getMapId({
        "min": 1,
        "max": 1,
        "palette": ["FFFF00"]
    })

    return {
        "glacierId": glacier_id,
        "year": year,
        "referenceYear": REFERENCE_YEAR,
        "threshold": GLACIER_SIMILARITY_THRESHOLD,

        "area": stats["area"],

        "referenceMethod": "automatic",
        "candidateArea": candidate_area_value,
        "manualAutomaticReferenceSimilarity":
            stats["manualAutomaticReferenceSimilarity"],

        "snowProbabilityPercentile": 75,
        "snowProbabilityThreshold": stats["snowProbabilityThreshold"],

        "elevationPercentile": 70,
        "minimumCandidateElevation": stats["minimumCandidateElevation"],

        "hemisphere": settings["hemisphere"],
        "aspectMinimum": settings["aspectMinimum"],
        "aspectMaximum": settings["aspectMaximum"],

        "tileUrl": map_info["tile_fetcher"].url_format
    }