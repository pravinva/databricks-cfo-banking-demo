# Databricks notebook source
# MAGIC %md
# MAGIC # DLT Pipeline: Loan Origination → GL Posting
# MAGIC
# MAGIC **Purpose**: Real-time streaming pipeline to process loan originations and post GL entries
# MAGIC
# MAGIC **Pipeline Flow**:
# MAGIC 1. **Bronze**: Ingest loan origination events from streaming source
# MAGIC 2. **Silver**: Parse events, validate data, enrich with accounting logic
# MAGIC 3. **Gold**: Post GL entries (double-entry bookkeeping) and update subledgers
# MAGIC
# MAGIC **Key Features**:
# MAGIC - Streaming ingestion with Auto Loader
# MAGIC - Data quality checks at each layer
# MAGIC - Double-entry GL posting automation
# MAGIC - Real-time regulatory impact calculations

# COMMAND ----------

import dlt
from pyspark.sql.functions import *
from pyspark.sql.types import *
from datetime import datetime

# COMMAND ----------

# MAGIC %md
# MAGIC ## Bronze Layer: Ingest Loan Origination Events

# COMMAND ----------

@dlt.table(
    name="bronze_loan_origination_stream",
    comment="Raw loan origination events from streaming source",
    table_properties={
        "quality": "bronze",
        "pipelines.autoOptimize.zOrderCols": "event_timestamp"
    }
)
@dlt.expect_all_or_drop({
    "valid_event_id": "event_id IS NOT NULL",
    "valid_loan_id": "loan_id IS NOT NULL",
    "valid_amount": "principal_amount > 0"
})
def bronze_loan_origination_stream():
    """
    Read loan origination events from bronze table
    Apply basic data quality checks
    """
    return (
        spark.readStream
            .format("delta")
            .table("cfo_banking_demo.bronze_core_banking.loan_origination_events")
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Silver Layer: Enrich & Transform

# COMMAND ----------

@dlt.table(
    name="silver_loan_origination_enriched",
    comment="Enriched loan originations with accounting logic",
    table_properties={
        "quality": "silver",
        "pipelines.autoOptimize.zOrderCols": "loan_id"
    }
)
@dlt.expect_all({
    "valid_gl_accounts": "debit_account IS NOT NULL AND credit_account IS NOT NULL",
    "balanced_entry": "debit_amount = credit_amount"
})
def silver_loan_origination_enriched():
    """
    Enrich loan originations with:
    - GL account mappings
    - CECL reserve calculations
    - Risk-weighted asset impact
    - Liquidity impact
    """
    df = dlt.read_stream("bronze_loan_origination_stream")

    return (
        df
        .withColumn("entry_id", expr("uuid()"))
        .withColumn("entry_date", col("event_timestamp").cast("date"))
        .withColumn("entry_timestamp", col("event_timestamp"))

        # GL Account Mapping
        .withColumn("debit_account",
            when(col("product_type") == "C&I", lit("1010"))
            .when(col("product_type") == "Commercial_RE", lit("1020"))
            .when(col("product_type") == "Residential_Mortgage", lit("1030"))
            .when(col("product_type").isin("HELOC", "Consumer_Auto", "Consumer_Other"), lit("1040"))
            .otherwise(lit("1050"))
        )
        .withColumn("credit_account", lit("2100"))  # Customer Deposit Account

        # Double-entry amounts
        .withColumn("debit_amount", col("principal_amount"))
        .withColumn("credit_amount", col("principal_amount"))

        # CECL Reserve (simplified: 1-3% based on risk rating)
        .withColumn("cecl_reserve",
            when(col("risk_rating") == "A", col("principal_amount") * 0.01)
            .when(col("risk_rating") == "B", col("principal_amount") * 0.015)
            .when(col("risk_rating") == "C", col("principal_amount") * 0.02)
            .when(col("risk_rating") == "D", col("principal_amount") * 0.03)
            .otherwise(col("principal_amount") * 0.02)
        )

        # Risk-Weighted Assets (Basel III)
        .withColumn("risk_weight",
            when(col("product_type").isin("C&I", "Commercial_RE"), lit(1.00))
            .when(col("product_type") == "Residential_Mortgage", lit(0.35))
            .when(col("product_type").isin("HELOC", "Consumer_Auto", "Consumer_Other"), lit(0.75))
            .otherwise(lit(1.00))
        )
        .withColumn("rwa_impact", col("principal_amount") * col("risk_weight"))

        # Processing metadata
        .withColumn("processing_timestamp", current_timestamp())
        .withColumn("pipeline_version", lit("1.0"))
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gold Layer: GL Entries (Headers)

# COMMAND ----------

@dlt.table(
    name="gold_gl_entries_streaming",
    comment="General Ledger entry headers from loan originations",
    table_properties={
        "quality": "gold",
        "pipelines.autoOptimize.zOrderCols": "entry_date,entry_id"
    }
)
def gold_gl_entries_streaming():
    """
    Create GL entry headers
    Represents the overall transaction
    """
    df = dlt.read_stream("silver_loan_origination_enriched")

    return (
        df.select(
            col("entry_id"),
            col("entry_date"),
            col("entry_timestamp"),
            col("loan_id").alias("source_transaction_id"),
            lit("LOAN_ORIGINATION").alias("source_system"),
            col("debit_amount").alias("total_debits"),
            col("credit_amount").alias("total_credits"),
            lit(True).alias("is_balanced"),
            concat(lit("Loan Origination - "), col("product_type"), lit(" - "), col("loan_id")).alias("description"),
            col("processing_timestamp").alias("posted_timestamp")
        )
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gold Layer: GL Entry Lines (Detail)

# COMMAND ----------

@dlt.table(
    name="gold_gl_entry_lines_streaming",
    comment="General Ledger entry line details with debit/credit pairs",
    table_properties={
        "quality": "gold",
        "pipelines.autoOptimize.zOrderCols": "entry_id"
    }
)
def gold_gl_entry_lines_streaming():
    """
    Create GL entry line items (debit and credit lines)
    Double-entry bookkeeping enforced
    """
    df = dlt.read_stream("silver_loan_origination_enriched")

    # Create debit line
    debit_line = df.select(
        concat(col("entry_id"), lit("-D")).alias("line_id"),
        col("entry_id"),
        col("debit_account").alias("account_number"),
        col("debit_amount").alias("debit_amount"),
        lit(0.0).alias("credit_amount"),
        concat(lit("DR: "), col("product_type"), lit(" Loan - "), col("borrower_name")).alias("description"),
        col("processing_timestamp")
    )

    # Create credit line
    credit_line = df.select(
        concat(col("entry_id"), lit("-C")).alias("line_id"),
        col("entry_id"),
        col("credit_account").alias("account_number"),
        lit(0.0).alias("debit_amount"),
        col("credit_amount").alias("credit_amount"),
        concat(lit("CR: Customer Deposit - "), col("borrower_name")).alias("description"),
        col("processing_timestamp")
    )

    # Union debit and credit lines
    return debit_line.union(credit_line)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gold Layer: Loan Subledger

# COMMAND ----------

@dlt.table(
    name="gold_loan_subledger_streaming",
    comment="Loan subledger entries for detailed transaction tracking",
    table_properties={
        "quality": "gold",
        "pipelines.autoOptimize.zOrderCols": "loan_id,posting_date"
    }
)
def gold_loan_subledger_streaming():
    """
    Create subledger entries for loan transactions
    Provides detailed audit trail
    """
    df = dlt.read_stream("silver_loan_origination_enriched")

    return (
        df.select(
            expr("uuid()").alias("entry_id"),
            col("loan_id"),
            col("entry_date").alias("posting_date"),
            col("entry_timestamp").alias("posting_timestamp"),
            lit("ORIGINATION").alias("transaction_type"),
            col("principal_amount").alias("transaction_amount"),
            col("principal_amount").alias("balance_after"),
            col("entry_id").alias("gl_entry_id"),
            concat(lit("Loan Originated - "), col("product_type")).alias("description"),
            col("cecl_reserve"),
            col("rwa_impact")
        )
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gold Layer: Intraday Liquidity Impact

# COMMAND ----------

@dlt.table(
    name="gold_intraday_liquidity_streaming",
    comment="Real-time liquidity impact from loan originations",
    table_properties={
        "quality": "gold"
    }
)
def gold_intraday_liquidity_streaming():
    """
    Track intraday liquidity changes
    Critical for LCR monitoring
    """
    df = dlt.read_stream("silver_loan_origination_enriched")

    return (
        df.select(
            col("entry_timestamp").alias("timestamp"),
            col("loan_id").alias("transaction_id"),
            lit("LOAN_ORIGINATION").alias("transaction_type"),
            (col("principal_amount") * -1).alias("cash_flow_impact"),  # Negative = outflow
            col("principal_amount").alias("hqla_impact"),  # Loan becomes HQLA-eligible asset
            col("processing_timestamp")
        )
        .withColumn("cumulative_impact",
            sum(col("cash_flow_impact")).over(
                Window.orderBy(col("timestamp")).rowsBetween(Window.unboundedPreceding, Window.currentRow)
            )
        )
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gold Layer: Regulatory Impact Summary

# COMMAND ----------

@dlt.table(
    name="gold_regulatory_impact_streaming",
    comment="Real-time regulatory impact calculations",
    table_properties={
        "quality": "gold"
    }
)
def gold_regulatory_impact_streaming():
    """
    Calculate real-time regulatory impacts:
    - Risk-Weighted Assets (RWA)
    - CECL Reserves (ALLL)
    - Capital Adequacy Ratios
    """
    df = dlt.read_stream("silver_loan_origination_enriched")

    return (
        df.groupBy(
            window(col("entry_timestamp"), "1 minute").alias("time_window"),
            col("product_type")
        )
        .agg(
            count("*").alias("loan_count"),
            sum("principal_amount").alias("total_principal"),
            sum("rwa_impact").alias("total_rwa_impact"),
            sum("cecl_reserve").alias("total_cecl_reserve"),
            avg("risk_weight").alias("avg_risk_weight")
        )
        .select(
            col("time_window.start").alias("window_start"),
            col("time_window.end").alias("window_end"),
            col("product_type"),
            col("loan_count"),
            col("total_principal"),
            col("total_rwa_impact"),
            col("total_cecl_reserve"),
            col("avg_risk_weight"),
            current_timestamp().alias("calculation_timestamp")
        )
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Data Quality Monitoring

# COMMAND ----------

@dlt.table(
    name="gold_dlt_pipeline_metrics",
    comment="Data quality metrics for pipeline monitoring"
)
def gold_dlt_pipeline_metrics():
    """
    Track pipeline health metrics
    """
    df = dlt.read_stream("silver_loan_origination_enriched")

    return (
        df.groupBy(
            window(col("processing_timestamp"), "5 minutes")
        )
        .agg(
            count("*").alias("records_processed"),
            sum("principal_amount").alias("total_amount"),
            countDistinct("loan_id").alias("unique_loans"),
            avg("principal_amount").alias("avg_loan_amount"),
            min("processing_timestamp").alias("first_processed"),
            max("processing_timestamp").alias("last_processed")
        )
        .select(
            col("window.start").alias("window_start"),
            col("window.end").alias("window_end"),
            col("records_processed"),
            col("total_amount"),
            col("unique_loans"),
            col("avg_loan_amount"),
            (unix_timestamp(col("last_processed")) - unix_timestamp(col("first_processed"))).alias("processing_time_seconds")
        )
    )
