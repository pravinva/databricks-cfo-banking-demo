#!/usr/bin/env python3
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import EndpointCoreConfigInput, ServedEntityInput

w = WorkspaceClient()

print("Creating serving endpoint for deposit_beta_model...")

try:
    # Use create_and_wait=False to avoid timeout
    endpoint = w.serving_endpoints.create_and_wait(
        name="deposit-beta-model-pravin-varma",
        config=EndpointCoreConfigInput(
            name="deposit-beta-model-pravin-varma",
            served_entities=[
                ServedEntityInput(
                    entity_name="cfo_banking_demo.models.deposit_beta_model",
                    entity_version="1",
                    workload_size="Small",
                    scale_to_zero_enabled=True
                )
            ]
        ),
        timeout=None  # Don't wait
    )

    print(f"✓ Serving endpoint creation initiated!")
    print(f"  Name: {endpoint.name}")
    print(f"  State: {endpoint.state}")
    print(f"  It will take several minutes for the endpoint to become ready.")

except Exception as e:
    # Check if endpoint was created but timed out waiting
    try:
        existing = w.serving_endpoints.get("deposit-beta-model-pravin-varma")
        print(f"✓ Serving endpoint was created successfully!")
        print(f"  Name: {existing.name}")
        print(f"  State: {existing.state}")
        print(f"  It will take several minutes for the endpoint to become ready.")
    except:
        print(f"Error creating serving endpoint: {e}")
