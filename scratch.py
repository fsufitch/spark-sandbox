import pyspark
import pyspark.sql
import pyspark.sql.types as T
import pyspark.errors

DF_FILE = "/sample_data.parquet"


def path_exists(spark: pyspark.sql.SparkSession, path: str) -> bool:
    try:
        spark.read.parquet(path).limit(1).collect()
        return True
    except pyspark.errors.AnalysisException:
        return False


def create_sample_data(spark: pyspark.sql.SparkSession) -> pyspark.sql.DataFrame:
    return spark.createDataFrame(
        schema=T.StructType(
            [
                T.StructField("id", T.IntegerType(), False),
                T.StructField("name", T.StringType(), False),
                T.StructField("age", T.IntegerType(), True),
                T.StructField("email", T.StringType(), True),
            ]
        ),
        data=[
            (1, "Alice", 30, "alice@example.com"),
            (2, "Bob", None, "bob@example.com"),
            (3, "Cathy", 28, "cathy@example.com"),
            (4, "David", 35, None),
            (5, "Eve", 22, "eve@example.com"),
        ],
    )


def main():
    # Initialize Spark session
    # spark = (
    #     pyspark.sql.SparkSession.builder.appName("Spark Sandbox").config(
    #         "spark.hadoop.fs.defaultFS", "hdfs://localhost:9000"
    #     )
    # ).getOrCreate()

    spark = (
        pyspark.sql.SparkSession.Builder()
        .remote("sc://localhost:15002")
        .appName("Spark Sandbox")
        .getOrCreate()
    )

    if not path_exists(spark, DF_FILE):
        print(f"File {DF_FILE} does not exist in HDFS. Creating it.")
        create_sample_data(spark).write.parquet(DF_FILE)

    print("Reading DataFrame from HDFS...")
    df = spark.read.parquet(DF_FILE)

    # Show the DataFrame
    df.show()

    # Stop the Spark session
    spark.stop()


if __name__ == "__main__":
    main()
