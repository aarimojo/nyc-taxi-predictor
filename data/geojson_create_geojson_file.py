import json
import pandas as pd

def parse_polygon_coords(geom_str):
    # Remove POLYGON or MULTIPOLYGON wrapper and clean up the coordinates
    if geom_str.startswith('MULTIPOLYGON'):
        # Handle MULTIPOLYGON case
        coords_str = geom_str[len('MULTIPOLYGON(('):-2]
        polygons = coords_str.split(')),((')
        all_coords = []
        for polygon in polygons:
            coords = []
            pairs = polygon.split(',')
            for pair in pairs:
                clean_pair = pair.strip('() ')
                x, y = map(float, clean_pair.split())
                coords.append([x, y])
            all_coords.append(coords)
        return all_coords, "MultiPolygon"
    else:
        # Handle POLYGON case
        coords_str = geom_str[len('POLYGON(('):-2]
        coords = []
        pairs = coords_str.split(',')
        for pair in pairs:
            clean_pair = pair.strip('() ')
            x, y = map(float, clean_pair.split())
            coords.append([x, y])
        return [coords], "Polygon"

def convert_to_geojson(input_file, output_file, taxi_zones_file):
    # Read the input file and taxi zones CSV
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    taxi_zones_df = pd.read_csv(taxi_zones_file)
    
    # Create the GeoJSON structure
    geojson = {
        "type": "FeatureCollection",
        "features": []
    }
    
    # Convert each neighborhood to a GeoJSON feature
    for neighborhood in data:
        try:
            coords, geom_type = parse_polygon_coords(neighborhood['zone_geom'])
            
            # Find matching taxi zone
            zone_id = neighborhood['zone_id']
            taxi_zone = taxi_zones_df[taxi_zones_df['LocationID'].astype(str) == str(zone_id)]
            service_zone = taxi_zone['service_zone'].iloc[0] if not taxi_zone.empty else "Unknown"
            
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": geom_type,
                    "coordinates": coords
                },
                "properties": {
                    "zone_id": neighborhood['zone_id'],
                    "zone_name": neighborhood['zone_name'],
                    "borough": neighborhood['borough'],
                    "service_zone": service_zone
                }
            }
            
            geojson['features'].append(feature)
        except Exception as e:
            print(f"Error processing neighborhood {neighborhood['zone_name']}: {str(e)}")
            print(f"Geometry string: {neighborhood['zone_geom'][:100]}...")
    
    # Write the output file
    with open(output_file, 'w') as f:
        json.dump(geojson, f, indent=2)

# Run the conversion
convert_to_geojson(
    'nycneighborhoods.geo.json', 
    'nycneighborhoods_converted.geo.json',
    'taxi_zones.csv'
)