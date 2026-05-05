import geopandas as gpd
import pandas as pd
from src.connectors import get_snowflake_connection

def _query(sql, fetch='pandas'):
    with get_snowflake_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql)
            if fetch == 'pandas':
                return cursor.fetch_pandas_all()
            elif fetch == 'one':
                return cursor.fetchone()

def compute_competitor_features(gdf_locations, gdf_competitors, radius=1500):
    # EPSG:2180 (Polish coordinate system) uses meters as units, required for buffer(radius) to work in meters, not degrees
    location_projected = gdf_locations.to_crs('EPSG:2180')
    competition_projected = gdf_competitors.to_crs('EPSG:2180')

    # Replace each location point with a circular polygon of given radius.
    buffer = location_projected[['location_id', 'geometry']].copy()
    buffer['geometry'] = buffer['geometry'].buffer(radius)

    # Inner spatial join: find which competitors fall within each location's buffer and count competitors per location.
    in_radius = gpd.sjoin(competition_projected, buffer, predicate='within', how='inner')
    count_df = in_radius.groupby('location_id').size().reset_index(name=f'competitor_count_{radius}m')

    # Left spatial join: find the nearest competitor for each location
    # drop_duplicates handles the edge case where two competitors are equidistant
    nearest_df = gpd.sjoin_nearest(
        location_projected[['location_id', 'geometry']],
        competition_projected,
        how='left',
        distance_col='nearest_competitor_m'
        )[['location_id', 'nearest_competitor_m']].drop_duplicates(subset='location_id')

    competitor_features = (location_projected[['location_id']]
        .merge(count_df, on='location_id', how='left')
        .merge(nearest_df, on='location_id', how='left'))

    # NaN means no competitors found within radius — converted to 0.
    competitor_features[f'competitor_count_{radius}m'] = (
        competitor_features[f'competitor_count_{radius}m'].fillna(0).astype(int))

    return competitor_features


def compute_poi_features(gdf_locations, gdf_poi, radius=1500):
    location_projected = gdf_locations.to_crs('EPSG:2180')
    poi_projected = gdf_poi.to_crs('EPSG:2180')

    buffer = location_projected[['location_id', 'geometry']].copy()
    buffer['geometry'] = buffer['geometry'].buffer(radius)

    in_radius = gpd.sjoin(poi_projected, buffer, predicate='within', how='inner')
    count_df = in_radius.groupby('location_id').size().reset_index(name=f'poi_count_{radius}m')

    nearest_df = gpd.sjoin_nearest(
        location_projected[['location_id', 'geometry']],
        poi_projected,
        how='left',
        distance_col='nearest_poi_m'
    )[['location_id', 'nearest_poi_m']].drop_duplicates(subset='location_id')

    poi_features = (location_projected[['location_id']]
                           .merge(count_df, on='location_id', how='left')
                           .merge(nearest_df, on='location_id', how='left'))

    poi_features[f'poi_count_{radius}m'] = (
        poi_features[f'poi_count_{radius}m'].fillna(0).astype(int))

    # repeating the whole process for each unique category of POI
    for cat in gdf_poi['category'].unique():
        cat_df = (in_radius[in_radius['category'] == cat]
                  .groupby('location_id')
                  .size()
                  .reset_index(name=f'poi_{cat}_count_{radius}m'))
        poi_features = poi_features.merge(cat_df, on='location_id', how='left')
        poi_features[f'poi_{cat}_count_{radius}m'] = (
            poi_features[f'poi_{cat}_count_{radius}m'].fillna(0).astype(int))

        poi_cat_projected = poi_projected[gdf_poi['category'] == cat]

        nearest_cat_df = gpd.sjoin_nearest(
            location_projected[['location_id', 'geometry']],
            poi_cat_projected,
            how='left',
            distance_col=f'nearest_poi_{cat}_m'
        )[['location_id', f'nearest_poi_{cat}_m']].drop_duplicates(subset='location_id')

        poi_features = (poi_features.merge(nearest_cat_df, on='location_id', how='left'))

    return poi_features


def compute_buildings_features(gdf_locations, gdf_buildings, radius=1500):
    # these categories of buildings are considered residential
    RESIDENTIAL_CATEGORIES = [
        'budynkiMieszkalneJednorodzinne',
        'budynkiODwochMieszkaniach',
        'budynkiOTrzechIWiecejMieszkaniach',
        'budynkiZbiorowegoZamieszkania',
    ]

    location_projected = gdf_locations.to_crs('EPSG:2180')
    buildings_projected = gdf_buildings.to_crs('EPSG:2180').copy()
    buildings_projected['is_residential'] = buildings_projected['funogolnabudynku_desc'].isin(RESIDENTIAL_CATEGORIES)

    buffer = location_projected[['location_id', 'geometry']].copy()
    buffer['geometry'] = buffer['geometry'].buffer(radius)

    in_radius = gpd.sjoin(buildings_projected, buffer, predicate='within', how='inner')

    count_df = in_radius.groupby('location_id').size().reset_index(name=f'building_count_{radius}m')

    residential_df = (in_radius[in_radius['is_residential']]
                      .groupby('location_id')
                      .size()
                      .reset_index(name=f'residential_count_{radius}m'))

    building_features = (location_projected[['location_id']]
                         .merge(count_df, on='location_id', how='left')
                         .merge(residential_df, on='location_id', how='left'))

    building_features[f'building_count_{radius}m'] = (
        building_features[f'building_count_{radius}m'].fillna(0).astype(int))
    building_features[f'residential_count_{radius}m'] = (
        building_features[f'residential_count_{radius}m'].fillna(0).astype(int))

    # we compute ratio from to calculated counts
    building_features[f'residential_ratio_{radius}m'] = (
            building_features[f'residential_count_{radius}m'] /
            building_features[f'building_count_{radius}m'].replace(0, float('nan'))
    )

    cols = ['location_id', f'building_count_{radius}m', f'residential_ratio_{radius}m']
    return building_features[cols]


def compute_population_features(gdf_locations, gdf_population, radius=1500):
    location_projected = gdf_locations.to_crs('EPSG:2180')
    population_projected = gdf_population.to_crs('EPSG:2180')

    buffer = location_projected[['location_id', 'geometry']].copy()
    buffer['geometry'] = buffer['geometry'].buffer(radius)

    in_radius = gpd.sjoin(population_projected, buffer, predicate='within', how='inner')
    count_df = in_radius.groupby('location_id')['total'].sum().reset_index(name=f'population_{radius}m')

    population_features = (location_projected[['location_id']].merge(count_df, on='location_id', how='left'))

    population_features[f'population_{radius}m'] = population_features[f'population_{radius}m'].fillna(0).astype(int)

    return population_features


def compute_footfall_features(gdf_locations, base_filter, radius=1500):
    results = []

    # we loop over each location and compute features separately
    for _, row in gdf_locations.iterrows():
        lng, lat = row['geometry'].x, row['geometry'].y

        df = _query(f"""
            SELECT
                COUNT(*) AS signals,
                COUNT(DISTINCT proxi_user_id) AS unique_users
            FROM RECRUITMENT_TRACES
            WHERE {base_filter}
            AND ST_DWITHIN(
                TO_GEOGRAPHY(ST_MAKEPOINT(CAST(longitude AS FLOAT), CAST(latitude AS FLOAT))),
                TO_GEOGRAPHY(ST_MAKEPOINT({lng}, {lat})),
                {radius}
                )
            """, fetch='pandas')

        results.append({
            'location_id': row['location_id'],
            f'signals_{radius}m': df['SIGNALS'].iloc[0],
            f'unique_users_{radius}m': df['UNIQUE_USERS'].iloc[0]
        })

    return pd.DataFrame(results)