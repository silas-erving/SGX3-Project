from flask import Flask, jsonify, request
import pandas as pd
import os
import io
import sys
import numpy as np



# Define your global DataFrame
traffic_df = None

app = Flask(__name__)

def load_traffic_data():
    global traffic_df
    print("Loading Austin Traffic Data...")
    traffic_df = pd.read_csv("atxtraffic.csv")
    print(f"Loaded {len(traffic_df)} rows into memory.")

@app.route("/")
def index():
    global traffic_df
    sample = traffic_df.head(10).to_dict(orient="records")
    return jsonify(sample)

@app.route("/head")
def top():
    global traffic_df
    num = int(request.args.get('count', 5))
    sample = traffic_df.head(num).to_dict(orient="records")
    return jsonify(sample)

@app.route('/shape', methods=['GET'])
def get_shape():
    rows, cols = traffic_df.shape
    return jsonify({
        'rows': rows,
        'columns': cols
    })

@app.route('/columns', methods=['GET'])
def get_columns():
    columns = traffic_df.columns.tolist()
    return jsonify(columns)

@app.route('/info', methods=['GET'])
def get_info():
    buffer = io.StringIO()
    traffic_df.info(buf=buffer)
    info_str = buffer.getvalue()
    return jsonify({"info": info_str})

@app.route('/describe', methods=['GET'])
def get_describe():
    stats = traffic_df.describe().to_dict()
    return jsonify(stats)

@app.route('/UniqueValues', methods=['GET'])
def get_unique_values():
    global traffic_df

    column_name = request.args.get('ColumnName')

    # Validate input
    if not column_name:
        return jsonify({"error": "Please provide a ColumnName query parameter."}), 400

    if column_name not in traffic_df.columns:
        return jsonify({
            "error": f"Column '{column_name}' not found in dataset."
        }), 400

    
    unique_vals = traffic_df[column_name].dropna().unique().tolist()
    num_unique = len(unique_vals)

    return jsonify({
        "column": column_name,
        "unique_values": unique_vals,
        "count": num_unique
    })

@app.route('/FilterByYear', methods=['GET'])
def filter_by_year():
    global traffic_df

    column_name = request.args.get('ColumnName')
    column_value = request.args.get('ColumnValue')
    year = request.args.get('Year')

    # Validate inputs
    if not column_name or not column_value or not year:
        return jsonify({"error": "Please provide ColumnName, ColumnValue, and Year as query parameters."}), 400

    if column_name not in traffic_df.columns:
        return jsonify({"error": f"Column '{column_name}' not found in dataset."}), 400

    # Ensure 'Year' column exists or extract year from datetime
    if 'Year' not in traffic_df.columns:
        if 'Published Date' in traffic_df.columns:
            traffic_df['Year'] = pd.to_datetime(traffic_df['Published Date'], errors='coerce').dt.year
        else:
            return jsonify({"error": "No 'Year' or valid date column available to extract year."}), 400

    # Filter the DataFrame
    filtered = traffic_df[
        (traffic_df[column_name] == column_value) &
        (traffic_df['Year'] == int(year))
    ]

    results = filtered.to_dict(orient="records")
    return jsonify({
        "column": column_name,
        "value": column_value,
        "year": int(year),
        "count": len(results),
        "matching_records": results
    })

@app.route('/FilterByHourRange', methods=['GET'])
def filter_by_hour_range():
    global traffic_df

    start_hour = request.args.get('StartHour')
    end_hour = request.args.get('EndHour')

    # Validate input
    if not start_hour or not end_hour:
        return jsonify({"error": "Please provide both StartHour and EndHour as query parameters."}), 400

    try:
        start_hour = int(start_hour)
        end_hour = int(end_hour)
    except ValueError:
        return jsonify({"error": "StartHour and EndHour must be integers between 0 and 23."}), 400

    if not (0 <= start_hour <= 23 and 0 <= end_hour <= 23):
        return jsonify({"error": "Hour values must be between 0 and 23."}), 400

    # ensure hour column is available
    if 'Hour' not in traffic_df.columns:
        if 'Published Date' in traffic_df.columns:
            traffic_df['Hour'] = pd.to_datetime(traffic_df['Published Date'], errors='coerce').dt.hour
        else:
            return jsonify({"error": "no 'Published Date' or similar datetime column to extract hour."}), 400

        # Filter rows between start start and end hour (inclusive)
        filtered = traffic_df[
                (traffic_df['Hour'] >= start_hour) & (traffic_df['Hour'] <= end_hour)
                ]

        return jsonify({
            "start_hour": start_hour,
            "end_hour": end_hour,
            "count": len(filtered),
            "records": filtered.to_dict(orient="records")
            })

# Haversine formula to calculate distance in kilometers
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth's radius in km
    lat1_rad = np.radians(lat1)
    lon1_rad = np.radians(lon1)
    lat2_rad = np.radians(lat2)
    lon2_rad = np.radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = np.sin(dlat / 2.0)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2.0)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c


@app.route('/NearbyIncidents', methods=['GET'])
def nearby_incidents():
    global traffic_df

    lat = request.args.get('lat')
    lon = request.args.get('lon')

    # Validate input
    if not lat or not lon:
        return jsonify({"error": "Please provide both lat and lon query parameters."}), 400

    try:
        lat = float(lat)
        lon = float(lon)
    except ValueError:
        return jsonify({"error": "Latitude and longitude must be numeric values."}), 400

    # Check if the necessary columns exist
    if 'Latitude' not in traffic_df.columns or 'Longitude' not in traffic_df.columns:
        return jsonify({"error": "Dataset must contain 'Latitude' and 'Longitude' columns."}), 400

    # Calculate distance using Haversine
    distances = haversine(
        lat, lon,
        traffic_df['Latitude'].astype(float),
        traffic_df['Longitude'].astype(float)
    )

    # Filter records within 1 km
    nearby = traffic_df[distances <= 1.0]

    return jsonify({
        "center_point": {"lat": lat, "lon": lon},
        "radius_km": 1.0,
        "count": len(nearby),
        "records": nearby.to_dict(orient="records")
    })

if __name__ == "__main__":
    load_traffic_data()
    app.run(debug=True, host="0.0.0.0", port=8030)

