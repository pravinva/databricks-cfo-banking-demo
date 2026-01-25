#!/usr/bin/env python3
"""
Start Continuous Loan Origination Event Stream
Generates events and inserts them into the bronze table for DLT pipeline processing
"""

import sys
import os
import time
from datetime import datetime
import json

# Add to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
import random

# Import the event generator
# Read and execute the event generator module
import importlib.util
spec = importlib.util.spec_from_file_location("event_gen",
    os.path.join(os.path.dirname(__file__), "24_loan_origination_event_generator.py"))
event_gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(event_gen)
LoanOriginationEventGenerator = event_gen.LoanOriginationEventGenerator

def log_message(message, level="INFO"):
    """Log messages with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

# Constants
WAREHOUSE_ID = "4b9b953939869799"
CATALOG = "cfo_banking_demo"
SCHEMA = "bronze_core_banking"
TABLE = "loan_origination_events"

def execute_sql(w, sql_statement, warehouse_id=WAREHOUSE_ID):
    """Execute SQL statement with timeout"""
    statement = w.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=sql_statement,
        wait_timeout="30s"
    )

    # Wait for completion
    max_wait_time = 120
    elapsed = 0
    while statement.status.state in [StatementState.PENDING, StatementState.RUNNING] and elapsed < max_wait_time:
        time.sleep(2)
        elapsed += 2
        statement = w.statement_execution.get_statement(statement.statement_id)

    if statement.status.state == StatementState.FAILED:
        error_msg = statement.status.error.message if statement.status.error else "Unknown error"
        raise Exception(f"SQL execution failed: {error_msg}")

    return statement

def insert_event_to_table(w, event):
    """Insert a single event into the bronze table"""

    # Extract key fields from the event
    loan_data = event['loan']
    borrower_data = event['borrower']
    risk_data = event['risk']
    origination_data = event['origination']

    # Build SQL INSERT statement
    insert_sql = f"""
    INSERT INTO {CATALOG}.{SCHEMA}.{TABLE} VALUES (
        '{event['event_id']}',
        '{event['event_type']}',
        TIMESTAMP '{event['event_timestamp']}',
        '{event['source_system']}',
        '{event['event_version']}',
        '{event['loan_id']}',
        '{event['application_id']}',
        '{borrower_data['name'].replace("'", "''")}',
        {borrower_data['credit_score']},
        {borrower_data['annual_income']},
        '{borrower_data['employment_status']}',
        {borrower_data['years_at_residence']},
        '{loan_data['product_type']}',
        {loan_data['principal_amount']},
        {loan_data['interest_rate']},
        {loan_data['term_months']},
        {loan_data['monthly_payment']},
        DATE '{loan_data['origination_date']}',
        DATE '{loan_data['first_payment_date']}',
        DATE '{loan_data['maturity_date']}',
        '{loan_data['loan_purpose'].replace("'", "''")}',
        '{loan_data['collateral_type'].replace("'", "''")}',
        '{risk_data['risk_rating']}',
        {risk_data['probability_of_default']},
        {risk_data['loss_given_default']},
        {risk_data['risk_weight']},
        {risk_data['cecl_reserve_rate']},
        '{origination_data['loan_officer_id']}',
        '{origination_data['loan_officer_name'].replace("'", "''")}',
        '{origination_data['branch_id']}',
        '{origination_data['branch_name'].replace("'", "''")}',
        '{origination_data['region']}',
        '{origination_data['channel']}',
        DATE '{origination_data['approval_date']}',
        {event['fees']['origination_fee']},
        {event['fees']['processing_fee']},
        {event['fees']['appraisal_fee']},
        {event['fees']['total_fees']},
        CURRENT_TIMESTAMP()
    )
    """

    execute_sql(w, insert_sql)

def start_event_stream(w, events_per_minute=5, duration_minutes=60):
    """
    Start continuous event stream

    Args:
        w: WorkspaceClient
        events_per_minute: Number of events to generate per minute
        duration_minutes: How long to run (0 = indefinite)
    """
    log_message("=" * 80)
    log_message("Starting Loan Origination Event Stream")
    log_message("=" * 80)
    log_message(f"Rate: {events_per_minute} events/minute")
    log_message(f"Duration: {'Indefinite' if duration_minutes == 0 else f'{duration_minutes} minutes'}")
    log_message(f"Target table: {CATALOG}.{SCHEMA}.{TABLE}")
    log_message("")

    generator = LoanOriginationEventGenerator()

    interval = 60.0 / events_per_minute  # seconds between events
    event_count = 0
    start_time = datetime.now()

    try:
        while True:
            # Generate event
            event = generator.generate_event()

            # Insert to table
            try:
                insert_event_to_table(w, event)
                event_count += 1

                if event_count % 10 == 0:
                    elapsed_minutes = (datetime.now() - start_time).total_seconds() / 60
                    rate = event_count / elapsed_minutes if elapsed_minutes > 0 else 0
                    log_message(f"Processed {event_count} events (avg rate: {rate:.1f}/min)")
                    log_message(f"  Latest: {event['loan']['product_type']} - ${event['loan']['principal_amount']:,.2f}")

            except Exception as e:
                log_message(f"Failed to insert event {event['event_id']}: {e}", "ERROR")
                continue

            # Check duration
            if duration_minutes > 0:
                elapsed = (datetime.now() - start_time).total_seconds() / 60
                if elapsed >= duration_minutes:
                    break

            # Wait for next event
            time.sleep(interval)

    except KeyboardInterrupt:
        log_message("\nStream stopped by user", "INFO")

    log_message("")
    log_message("=" * 80)
    log_message(f"✅ Event Stream Complete")
    log_message("=" * 80)
    log_message(f"Total events generated: {event_count}")
    elapsed_minutes = (datetime.now() - start_time).total_seconds() / 60
    log_message(f"Total runtime: {elapsed_minutes:.1f} minutes")
    log_message(f"Average rate: {event_count / elapsed_minutes:.1f} events/minute")
    log_message("")

def main():
    """Main execution"""
    log_message("Connecting to Databricks...")
    w = WorkspaceClient()
    log_message("✓ Connected")

    log_message("")

    # Default: 5 events per minute, run for 30 minutes
    start_event_stream(w, events_per_minute=5, duration_minutes=30)

if __name__ == "__main__":
    main()
