"""
Delta Live Tables pipeline for clinical data medallion architecture.
Implements data quality expectations and schema enforcement.
"""
import dlt
from pyspark.sql.functions import col, when, current_timestamp, regexp_replace

# Bronze: Raw FHIR events from Event Hubs
@dlt.table(
    name="bronze_clinical_events",
    comment="Raw clinical events ingested from FHIR APIs and Event Hubs",
    table_properties={"quality": "bronze", "pipelines.autoOptimize.managed": "true"}
)
def bronze_clinical_events():
    return (
        spark.readStream
        .format("eventhubs")
        .option("eventhubs.connectionString", dbutils.secrets.get("scope", "eh-connection"))
        .load()
        .selectExpr("cast(body as string) as json_payload")
        .selectExpr("from_json(json_payload, 'resourceType STRING, resourceId STRING, timestamp TIMESTAMP, payload STRING') as data")
        .select("data.*")
    )

# Silver: Validated and cleaned clinical data
@dlt.table(
    name="silver_patient_data",
    comment="Validated patient data with PII handling and quality checks",
    table_properties={"quality": "silver"}
)
@dlt.expect_or_drop("valid_patient_id", "patient_id IS NOT NULL")
@dlt.expect_or_drop("valid_timestamp", "event_timestamp IS NOT NULL")
@dlt.expect("valid_age_range", "age BETWEEN 0 AND 120")
def silver_patient_data():
    bronze_df = dlt.read("bronze_clinical_events")
    
    return (
        bronze_df
        .filter(col("resourceType") == "Patient")
        .select(
            col("resourceId").alias("patient_id"),
            col("payload.name[0].given[0]").alias("first_name"),
            col("payload.name[0].family").alias("last_name"),
            regexp_replace(col("payload.telecom[0].value"), ".{4}$", "****").alias("masked_phone"),
            col("payload.birthDate").alias("birth_date"),
            when(col("payload.gender") == "male", "M")
            .when(col("payload.gender") == "female", "F")
            .otherwise("U").alias("gender"),
            current_timestamp().alias("ingestion_timestamp"),
            col("timestamp").alias("event_timestamp")
        )
        .withColumn("age", (current_timestamp().cast("date").cast("int") - col("birth_date").cast("int")) / 365)
    )

# Gold: Aggregated patient metrics for analytics and ML
@dlt.table(
    name="gold_patient_risk_metrics",
    comment="Aggregated patient risk scores and clinical metrics for ML and BI",
    table_properties={"quality": "gold"}
)
def gold_patient_risk_metrics():
    silver_df = dlt.read("silver_patient_data")
    obs_df = dlt.read("silver_observations")
    
    return (
        silver_df
        .join(
            obs_df.groupBy("patient_id").agg(
                {"value": "avg", "timestamp": "max"}
            ),
            "patient_id",
            "left"
        )
        .select(
            "patient_id",
            "age",
            "gender",
            "avg(value)".alias("avg_observation_value"),
            "max(timestamp)".alias("last_observation_time"),
            when(col("age") > 65, "high_risk")
            .when(col("age") > 45, "medium_risk")
            .otherwise("low_risk").alias("risk_stratification")
        )
    )
