from flask import Flask, request, jsonify
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, mean, stddev, expr, count, lit
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import numpy as np

app = Flask(__name__)

# Create a Spark session pointing to an external Spark cluster (replace with your Spark master node URL)
spark = SparkSession.builder \
    .appName("PlateDataAnalyzer") \
    .master("spark://spark-master:7077") \
    .set("spark.cores.max", "8") \
    .set("spark.executor.memory", "4g")\
    .getOrCreate()

bucket = "sparka"
org = "RemostoTeam"
token = "n6HCiO-f5dz1vRGzeT64eid9As5FvY_Wn0sR_bB9bXbPd1ZEeiC4pwJ4FyexRQD9QqT-NS3Bz7ItppVg0nks0Q=="
url = "http://localhost:8086"

client = InfluxDBClient(url=url, token=token, org=org)
write_api = client.write_api(write_options=SYNCHRONOUS)
query_api = client.query_api()

# List of fields to include in the analysis
fields_to_analyze = [
    "plate_position_x",
    "plate_position_y",
    "vehicle_position_x",
    "vehicle_position_y"
]

@app.route('/analyze_data', methods=['POST'])
def analyze_data():
    data = request.json
    measurement = data.get('measurement')
    start_time = data.get('start', '-1h')  # Default to last hour
    stop_time = data.get('stop', 'now()')
    n_bins = data.get('n_bins', 10)  # Number of bins for clustering

    if not measurement:
        return jsonify({"error": "Measurement parameter is required"}), 400

    try:
        # Step 1: Query Data from InfluxDB
        fields_to_analyze_flux = '["' + '", "'.join(fields_to_analyze) + '"]'

        query = f'''
        from(bucket: "{bucket}")
          |> range(start: {start_time}, stop: {stop_time})
          |> filter(fn: (r) => r["_measurement"] == "{measurement}")
          |> filter(fn: (r) => contains(value: r["_field"], set: {fields_to_analyze_flux}))
        '''

        print("Executing Query:\n", query)  # Debugging: Print the query

        result = query_api.query(org=org, query=query)
        data = []

        for table in result:
            for record in table.records:
                data.append({
                    "time": record.get_time(),
                    "measurement": record.get_measurement(),
                    "field": record.get_field(),
                    "value": record.get_value(),
                    "tags": record.values
                })

        # Step 2: Create a PySpark DataFrame from the data
        if not data:
            return jsonify({"error": "No data found"}), 404

        import pandas as pd
        pd_df = pd.DataFrame(data)
        spark_df = spark.createDataFrame(pd_df)

        # Step 3: Explicitly Select Fields for Analysis
        spark_df = spark_df.filter(col("field").isin(fields_to_analyze))

        # Step 4: Perform Central Tendency and Spread Analysis
        summary_stats = spark_df.groupBy("field").agg(
            mean("value").alias("mean"),
            expr("percentile_approx(value, 0.5)").alias("median"),
            stddev("value").alias("stddev"),
            count("value").alias("count")
        ).collect()

        summary_results = {}
        for row in summary_stats:
            summary_results[row['field']] = {
                "mean": row['mean'],
                "median": row['median'],
                "stddev": row['stddev'],
                "count": row['count']
            }

        # Step 5: Perform Bins Clustering
        bins = np.linspace(spark_df.agg({"value": "min"}).first()["min(value)"],
                           spark_df.agg({"value": "max"}).first()["max(value)"], n_bins + 1)

        binning_expr = f'FLOOR((value - {bins[0]}) / {(bins[-1] - bins[0]) / n_bins})'
        spark_df = spark_df.withColumn("bin", expr(binning_expr).cast("integer"))

        bin_counts = spark_df.groupBy("field", "bin").agg(
            count(lit(1)).alias("count")
        ).collect()

        bins_results = {}
        for row in bin_counts:
            field = row['field']
            if field not in bins_results:
                bins_results[field] = {}
            bins_results[field][int(row['bin'])] = row['count']

        # Step 6: Return the Analysis Results as JSON
        response = {
            "summary_statistics": summary_results,
            "bins_clustering": bins_results
        }

        return jsonify(response), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5004)
