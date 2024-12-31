from pyspark.sql import SparkSession

def check_connection_to_spark_master(master_url):
    try:
        # Create the Spark session
        print(f"Attempting to connect to master at {master_url}...")
        spark = SparkSession.builder \
            .appName("PlateDataAnalyzer") \
            .master(master_url) \
            .getOrCreate()
        
        print("spark connected:", spark)

        # Test Spark context by performing a simple operation
        arr = [i for i in range(100000000)]
        rdd = spark.sparkContext.parallelize(arr)
        result = rdd.reduce(lambda a, b: a + b)
        print(f"Successfully connected to Spark master! Sample result: {result}")

        spark.stop()

        return True
    except Exception as e:
        print(f"Error connecting to Spark master: {e}")
        return False

if __name__ == "__main__":
    master_url = "spark://spark-master:7077" 
    if check_connection_to_spark_master(master_url):
        print("Connection successful!")
    else:
        print("Failed to connect to Spark master.")
