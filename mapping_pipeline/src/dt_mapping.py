from pyspark.sql.functions import col, lit, format_string
from pyspark.sql.column import Column

from r2r import Mapping

POTATO_NS = "http://example.com/potato-factory"


def component_iri(component_id_column_name) -> Column:
    return format_string(f"{POTATO_NS}/component-%s", component_id_column_name)


def type_iri(type_name) -> Column:
    return lit(f"{POTATO_NS}/type/{type_name}")


def predicate_iri(predicate_name) -> str:
    return f"{POTATO_NS}/pred/{predicate_name}"


mappings = {
    spark.conf.get("triple_table"): Mapping(
        source=spark.conf.get("bronze_table"),
        subject_map=component_iri("component_id"),
        rdf_type=type_iri("component"),
        predicate_object_maps={
            predicate_iri("oil_temperature"): col("oil_temperature"),
            predicate_iri("water_temperature"): col("water_temperature"),
            predicate_iri("belt_speed"): col("belt_speed"),
            predicate_iri("freezer_temperature"): col("freezer_temperature"),
            predicate_iri("moisture_content"): col("moisture_content"),
            predicate_iri("product_weight"): col("product_weight"),
            predicate_iri("component_yield_output"): col("component_yield_output"),
            predicate_iri("damaged_component"): col("damaged_component").cast("string"),
            predicate_iri("abnormal_sensor"): col("abnormal_sensor"),
        },
        metadata_columns={
            "timestamp": col("timestamp").cast("timestamp"),
        },
    ),
}

for name, mapping in mappings.items():
    mapping.to_dp(spark, name)
