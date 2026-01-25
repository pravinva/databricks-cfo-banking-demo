#!/usr/bin/env python3
"""
Deploy DLT Pipeline for Loan Origination GL Posting
Creates a Delta Live Tables pipeline in Databricks workspace
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.pipelines import *
from databricks.sdk.service.workspace import ImportFormat, Language
import time
from datetime import datetime

def log_message(message, level="INFO"):
    """Log messages with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def upload_notebook_to_workspace(w, local_path, workspace_path):
    """Upload DLT notebook to Databricks workspace"""
    log_message(f"Uploading notebook to workspace: {workspace_path}")

    # Read local notebook content
    with open(local_path, 'r') as f:
        content = f.read()

    # Convert to base64 for upload
    import base64
    content_b64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')

    # Upload to workspace
    w.workspace.import_(
        path=workspace_path,
        format=ImportFormat.SOURCE,
        language=Language.PYTHON,
        content=content_b64,
        overwrite=True
    )

    log_message(f"  ✓ Notebook uploaded successfully")
    return workspace_path

def create_dlt_pipeline(w, notebook_path, pipeline_name):
    """Create Delta Live Tables pipeline"""
    log_message(f"Creating DLT pipeline: {pipeline_name}")

    # Create pipeline
    try:
        pipeline = w.pipelines.create(
            name=pipeline_name,
            storage="/dbfs/pipelines/cfo_banking_demo/loan_origination_gl",
            target="cfo_banking_demo",
            continuous=False,  # Triggered mode
            channel="CURRENT",
            photon=True,
            libraries=[{
                "notebook": {"path": notebook_path}
            }],
            clusters=[{
                "label": "default",
                "num_workers": 2,
                "custom_tags": {
                    "Project": "CFO Banking Demo",
                    "Component": "DLT Pipeline"
                }
            }],
            configuration={
                "pipelines.applyChanges.enabled": "true"
            },
            development=False,
            edition="ADVANCED"
        )
        pipeline_id = pipeline.pipeline_id
        log_message(f"  ✓ Pipeline created with ID: {pipeline_id}")
        return pipeline_id
    except Exception as e:
        # Check if pipeline already exists
        if "already exists" in str(e).lower():
            log_message(f"  Pipeline '{pipeline_name}' already exists, retrieving ID...")
            pipelines = list(w.pipelines.list_pipelines())
            for p in pipelines:
                if p.name == pipeline_name:
                    log_message(f"  ✓ Found existing pipeline ID: {p.pipeline_id}")
                    return p.pipeline_id
        raise e

def start_pipeline_update(w, pipeline_id):
    """Start a pipeline update (runs the pipeline)"""
    log_message(f"Starting pipeline update...")

    try:
        update = w.pipelines.start_update(pipeline_id=pipeline_id)
        update_id = update.update_id
        log_message(f"  ✓ Pipeline update started: {update_id}")
        return update_id
    except Exception as e:
        log_message(f"  Pipeline update may already be running: {e}", "WARNING")
        return None

def check_pipeline_status(w, pipeline_id):
    """Check pipeline status"""
    log_message("Checking pipeline status...")

    pipeline = w.pipelines.get(pipeline_id=pipeline_id)

    log_message(f"  Pipeline Name: {pipeline.name}")
    log_message(f"  Pipeline ID: {pipeline.pipeline_id}")
    log_message(f"  State: {pipeline.state}")
    log_message(f"  Creator: {pipeline.creator_user_name}")

    if pipeline.latest_updates:
        latest = pipeline.latest_updates[0]
        log_message(f"  Latest Update:")
        log_message(f"    - Update ID: {latest.update_id}")
        log_message(f"    - State: {latest.state}")
        log_message(f"    - Creation Time: {latest.creation_time}")

    return pipeline

def main():
    log_message("=" * 80)
    log_message("DLT Pipeline Deployment: Loan Origination GL Posting")
    log_message("=" * 80)

    # Initialize Databricks client
    w = WorkspaceClient()
    log_message("✓ Connected to Databricks")

    # Configuration
    LOCAL_NOTEBOOK_PATH = "../../../notebooks/DLT_Loan_Origination_GL_Pipeline.py"
    WORKSPACE_NOTEBOOK_PATH = "/Users/pravin.varma@databricks.com/DLT_Loan_Origination_GL_Pipeline"
    PIPELINE_NAME = "CFO_Banking_Demo_Loan_Origination_GL_Pipeline"

    log_message("")
    log_message("-" * 80)

    # Step 1: Upload notebook
    try:
        notebook_path = upload_notebook_to_workspace(w, LOCAL_NOTEBOOK_PATH, WORKSPACE_NOTEBOOK_PATH)
    except FileNotFoundError:
        # Try alternative path
        LOCAL_NOTEBOOK_PATH = "../../notebooks/DLT_Loan_Origination_GL_Pipeline.py"
        notebook_path = upload_notebook_to_workspace(w, LOCAL_NOTEBOOK_PATH, WORKSPACE_NOTEBOOK_PATH)

    log_message("")
    log_message("-" * 80)

    # Step 2: Create pipeline
    pipeline_id = create_dlt_pipeline(w, notebook_path, PIPELINE_NAME)

    log_message("")
    log_message("-" * 80)

    # Step 3: Check pipeline status
    pipeline = check_pipeline_status(w, pipeline_id)

    log_message("")
    log_message("=" * 80)
    log_message("✅ DLT Pipeline Deployment Complete")
    log_message("=" * 80)
    log_message("")
    log_message(f"Pipeline ID: {pipeline_id}")
    log_message(f"Pipeline URL: https://e2-demo-field-eng.cloud.databricks.com/#joblist/pipelines/{pipeline_id}")
    log_message("")
    log_message("To start the pipeline:")
    log_message(f"  1. Navigate to the pipeline URL above")
    log_message(f"  2. Click 'Start' button")
    log_message(f"  3. Or run: databricks pipelines start-update --pipeline-id {pipeline_id}")
    log_message("")

    # Optionally start the pipeline (commented out by default)
    # log_message("")
    # log_message("-" * 80)
    # update_id = start_pipeline_update(w, pipeline_id)
    # if update_id:
    #     log_message(f"Pipeline update {update_id} started. Monitor progress in Databricks UI.")

if __name__ == "__main__":
    main()
