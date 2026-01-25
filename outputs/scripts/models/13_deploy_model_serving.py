#!/usr/bin/env python3
"""
Deploy Deposit Beta Model to Model Serving Endpoint
Creates a serverless endpoint for real-time predictions
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import *
from databricks.sdk.service.sql import StatementState
import time
from datetime import datetime

def log_message(message, level="INFO"):
    """Log messages with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

# Constants
CATALOG = "cfo_banking_demo"
SCHEMA = "ml_models"
MODEL_NAME = "deposit_beta_predictor"
ENDPOINT_NAME = "deposit-beta-predictor-endpoint"

def check_model_exists(w):
    """Check if model exists in Unity Catalog"""
    log_message(f"Checking if model exists: {CATALOG}.{SCHEMA}.{MODEL_NAME}")

    try:
        # List models in the schema
        models = list(w.registered_models.list(catalog_name=CATALOG, schema_name=SCHEMA))

        for model in models:
            if model.name == f"{CATALOG}.{SCHEMA}.{MODEL_NAME}":
                log_message(f"  ✓ Model found: {model.name}")

                # Get model versions
                versions = list(w.model_versions.list(full_name=f"{CATALOG}.{SCHEMA}.{MODEL_NAME}"))
                if versions:
                    log_message(f"  ✓ Model has {len(versions)} version(s)")

                    # Check for champion alias
                    for version in versions:
                        if version.aliases:
                            log_message(f"    - Version {version.version}: aliases = {version.aliases}")

                    return True
                else:
                    log_message(f"  ⚠ Model exists but has no versions", "WARNING")
                    return False

        log_message(f"  ✗ Model not found in catalog", "WARNING")
        return False

    except Exception as e:
        log_message(f"  ✗ Error checking model: {e}", "ERROR")
        return False

def create_or_update_endpoint(w):
    """Create or update Model Serving endpoint"""
    log_message(f"Creating/updating Model Serving endpoint: {ENDPOINT_NAME}")

    # Check if endpoint already exists
    existing_endpoint = None
    try:
        existing_endpoints = list(w.serving_endpoints.list())
        for ep in existing_endpoints:
            if ep.name == ENDPOINT_NAME:
                existing_endpoint = ep
                log_message(f"  ✓ Found existing endpoint: {ep.name}")
                break
    except Exception as e:
        log_message(f"  Note: {e}", "INFO")

    # Define endpoint configuration
    endpoint_config = ServedEntityInput(
        entity_name=f"{CATALOG}.{SCHEMA}.{MODEL_NAME}",
        entity_version="1",  # Use version 1 or champion alias
        scale_to_zero_enabled=True,
        workload_size=ServedEntityInputWorkloadSize.SMALL
    )

    if existing_endpoint:
        # Update existing endpoint
        log_message(f"  Updating existing endpoint...")
        try:
            w.serving_endpoints.update_config(
                name=ENDPOINT_NAME,
                served_entities=[endpoint_config]
            )
            log_message(f"  ✓ Endpoint update initiated")
        except Exception as e:
            log_message(f"  ✗ Failed to update endpoint: {e}", "ERROR")
            raise
    else:
        # Create new endpoint
        log_message(f"  Creating new endpoint...")
        try:
            endpoint = w.serving_endpoints.create(
                name=ENDPOINT_NAME,
                config=EndpointCoreConfigInput(
                    served_entities=[endpoint_config]
                )
            )
            log_message(f"  ✓ Endpoint creation initiated")
        except Exception as e:
            log_message(f"  ✗ Failed to create endpoint: {e}", "ERROR")
            raise

    return ENDPOINT_NAME

def wait_for_endpoint_ready(w, endpoint_name, max_wait=600):
    """Wait for endpoint to be ready"""
    log_message(f"Waiting for endpoint to be ready (max {max_wait}s)...")

    elapsed = 0
    while elapsed < max_wait:
        try:
            endpoint = w.serving_endpoints.get(name=endpoint_name)
            state = endpoint.state.config_update if endpoint.state else None

            if state == EndpointStateConfigUpdate.IN_PROGRESS:
                log_message(f"  Endpoint state: IN_PROGRESS ({elapsed}s elapsed)")
                time.sleep(10)
                elapsed += 10
            elif state == EndpointStateConfigUpdate.READY:
                log_message(f"  ✓ Endpoint is READY!")
                return endpoint
            else:
                log_message(f"  Endpoint state: {state}")
                time.sleep(10)
                elapsed += 10
        except Exception as e:
            log_message(f"  Error checking endpoint: {e}", "WARNING")
            time.sleep(10)
            elapsed += 10

    log_message(f"  ⚠ Endpoint did not become ready within {max_wait}s", "WARNING")
    return None

def test_endpoint(w, endpoint_name):
    """Test the endpoint with sample data"""
    log_message(f"Testing endpoint with sample data...")

    # Sample input matching training features
    test_input = {
        "dataframe_records": [
            {
                "fed_funds_rate": 4.5,
                "rate_change": 0.25,
                "rate_direction": "INCREASE",
                "beginning_balance": 50000.0,
                "ending_balance": 48500.0,
                "balance_change": -1500.0,
                "balance_tier": "MEDIUM",
                "product_type": "Savings",
                "customer_segment": "Mass_Market",
                "has_online_banking": True,
                "month": 1,
                "quarter": 1,
                "rate_balance_interaction": 12500.0,
                "balance_volatility": 3.0
            }
        ]
    }

    try:
        response = w.serving_endpoints.query(
            name=endpoint_name,
            dataframe_records=test_input["dataframe_records"]
        )

        log_message(f"  ✓ Endpoint test successful!")
        log_message(f"  Response: {response}")
        return response

    except Exception as e:
        log_message(f"  ⚠ Endpoint test failed: {e}", "WARNING")
        log_message(f"  This is expected if the model hasn't been trained yet", "INFO")
        return None

def main():
    log_message("=" * 80)
    log_message("Deploy Deposit Beta Model to Model Serving")
    log_message("=" * 80)

    # Initialize Databricks client
    w = WorkspaceClient()
    log_message("✓ Connected to Databricks")

    log_message("")
    log_message("-" * 80)

    # Step 1: Check if model exists
    model_exists = check_model_exists(w)

    if not model_exists:
        log_message("")
        log_message("=" * 80)
        log_message("⚠ Model Not Found or No Versions Available")
        log_message("=" * 80)
        log_message("")
        log_message("The model must be trained before deploying to serving.")
        log_message("Please run the AutoML training notebook first:")
        log_message("  1. Open: /Users/pravin.varma@databricks.com/Deposit_Beta_AutoML_Training")
        log_message("  2. Attach to a cluster with ML Runtime")
        log_message("  3. Run all cells to train and register the model")
        log_message("")
        log_message("After training completes, re-run this script to deploy.")
        log_message("")
        return

    log_message("")
    log_message("-" * 80)

    # Step 2: Create/update endpoint
    endpoint_name = create_or_update_endpoint(w)

    log_message("")
    log_message("-" * 80)

    # Step 3: Wait for endpoint to be ready
    endpoint = wait_for_endpoint_ready(w, endpoint_name, max_wait=300)

    if endpoint:
        log_message("")
        log_message("-" * 80)

        # Step 4: Test endpoint
        test_endpoint(w, endpoint_name)

    log_message("")
    log_message("=" * 80)
    log_message("✅ Model Serving Deployment Complete")
    log_message("=" * 80)
    log_message("")
    log_message(f"Endpoint Name: {endpoint_name}")
    log_message(f"Endpoint URL: https://e2-demo-field-eng.cloud.databricks.com/ml/endpoints/{endpoint_name}")
    log_message("")
    log_message("To query the endpoint:")
    log_message(f"  databricks serving-endpoints query --name {endpoint_name} --data '{{}}'")
    log_message("")

if __name__ == "__main__":
    main()
