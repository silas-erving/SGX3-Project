from flask import Flask, jsonify, request
import pandas as pd
import os
import io
import sys

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

    # ✅ These lines must NOT be indented under the "if" above!
    unique_vals = traffic_df[column_name].dropna().unique().tolist()
    num_unique = len(unique_vals)

    return jsonify({
        "column": column_name,
        "unique_values": unique_vals,
        "count": num_unique
    })

if __name__ == "__main__":
    load_traffic_data()
    app.run(debug=True, host="0.0.0.0", port=8030)

