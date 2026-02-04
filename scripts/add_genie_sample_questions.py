#!/usr/bin/env python3
"""
Add Sample Questions to Genie Space: Treasury Modeling - Deposits & Fee Income

This script adds curated sample questions to guide users on what they can ask Genie.
Sample questions are organized by domain: Deposit Beta, Vintage Analysis, Stress Testing, and PPNR.

Usage:
    python3 add_genie_sample_questions.py
"""

import json
import subprocess
import uuid

# Genie Space Configuration
SPACE_ID = "01f101adda151c09835a99254d4c308c"
SPACE_NAME = "Treasury Modeling - Deposits & Fee Income"


def generate_uuid() -> str:
    """Generate 32-character hex ID (UUID without hyphens)"""
    return uuid.uuid4().hex


def get_current_space_config():
    """Fetch current Genie space configuration"""
    cmd = [
        "databricks", "api", "get",
        f"/api/2.0/genie/spaces/{SPACE_ID}",
        "--output", "json"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    space_data = json.loads(result.stdout)

    # Parse serialized_space JSON string
    serialized_space_str = space_data.get("serialized_space", "{}")
    serialized_space = json.loads(serialized_space_str)

    return serialized_space


def create_sample_questions():
    """
    Create sample questions organized by domain

    Returns list of sample question dictionaries with:
    - id: 32-char hex UUID
    - question: List with single string (the question)
    """
    questions = []

    # ===================================================================
    # PHASE 1: DEPOSIT BETA MODELING
    # ===================================================================

    questions.extend([
        {
            "id": generate_uuid(),
            "question": ["What is the average deposit beta by relationship category?"]
        },
        {
            "id": generate_uuid(),
            "question": ["Show me at-risk accounts for Strategic customers"]
        },
        {
            "id": generate_uuid(),
            "question": ["What is the average rate gap by product type?"]
        },
        {
            "id": generate_uuid(),
            "question": ["How many accounts are priced below market rate?"]
        },
        {
            "id": generate_uuid(),
            "question": ["Show me the top 10 accounts by balance with high flight risk"]
        },
        {
            "id": generate_uuid(),
            "question": ["What percentage of MMDA accounts are at-risk?"]
        },
    ])

    # ===================================================================
    # PHASE 2: VINTAGE ANALYSIS & RUNOFF FORECASTING
    # ===================================================================

    questions.extend([
        {
            "id": generate_uuid(),
            "question": ["What is the 12-month survival rate for Tactical customers?"]
        },
        {
            "id": generate_uuid(),
            "question": ["Show me the 3-year deposit runoff forecast by segment"]
        },
        {
            "id": generate_uuid(),
            "question": ["What is the closure rate for Expendable customers?"]
        },
        {
            "id": generate_uuid(),
            "question": ["Compare account survival rates across all relationship categories at 24 months"]
        },
        {
            "id": generate_uuid(),
            "question": ["What is the projected balance for Strategic deposits in 36 months?"]
        },
    ])

    # ===================================================================
    # PHASE 3: CCAR/DFAST STRESS TESTING
    # ===================================================================

    questions.extend([
        {
            "id": generate_uuid(),
            "question": ["What is the CET1 ratio under severely adverse scenario?"]
        },
        {
            "id": generate_uuid(),
            "question": ["Show me NII impact across all stress test scenarios"]
        },
        {
            "id": generate_uuid(),
            "question": ["Does the bank pass the CCAR stress test?"]
        },
        {
            "id": generate_uuid(),
            "question": ["What is today's LCR ratio?"]
        },
        {
            "id": generate_uuid(),
            "question": ["Show me HQLA composition by level"]
        },
        {
            "id": generate_uuid(),
            "question": ["What is the stressed beta under adverse scenario?"]
        },
        {
            "id": generate_uuid(),
            "question": ["Compare delta EVE across baseline, adverse, and severely adverse scenarios"]
        },
    ])

    # ===================================================================
    # PHASE 4: PPNR MODELING
    # ===================================================================

    questions.extend([
        {
            "id": generate_uuid(),
            "question": ["What is the forecasted PPNR for next quarter?"]
        },
        {
            "id": generate_uuid(),
            "question": ["Show me 9-quarter PPNR projections"]
        },
        {
            "id": generate_uuid(),
            "question": ["What is the efficiency ratio trend over the next 2 years?"]
        },
        {
            "id": generate_uuid(),
            "question": ["Compare net interest income vs non-interest income"]
        },
        {
            "id": generate_uuid(),
            "question": ["What is the expected non-interest expense growth rate?"]
        },
    ])

    # ===================================================================
    # CROSS-DOMAIN COMPLEX QUERIES
    # ===================================================================

    questions.extend([
        {
            "id": generate_uuid(),
            "question": ["Show me the complete risk dashboard: at-risk deposits, runoff forecast, and CET1 ratio"]
        },
        {
            "id": generate_uuid(),
            "question": ["What is the relationship between deposit beta and account survival rates?"]
        },
        {
            "id": generate_uuid(),
            "question": ["How does PPNR vary across different stress scenarios?"]
        },
    ])

    # Sort by ID (API requirement)
    questions.sort(key=lambda x: x["id"])

    return questions


def update_space_with_sample_questions():
    """Main execution: fetch config, add sample questions, update space"""

    print("=" * 70)
    print("Add Sample Questions to Genie Space")
    print("=" * 70)
    print(f"\nSpace: {SPACE_NAME}")
    print(f"Space ID: {SPACE_ID}")

    # Fetch current configuration
    print("\n📥 Fetching current Genie space configuration...")
    current_config = get_current_space_config()

    current_questions = current_config.get("config", {}).get("sample_questions", [])
    print(f"   ✅ Current sample questions: {len(current_questions)}")

    # Generate sample questions
    print("\n📝 Generating sample questions...")
    sample_questions = create_sample_questions()
    print(f"   ✅ New sample questions: {len(sample_questions)}")

    # Categorize by domain
    beta_qs = sample_questions[0:6]
    vintage_qs = sample_questions[6:11]
    stress_qs = sample_questions[11:18]
    ppnr_qs = sample_questions[18:23]
    complex_qs = sample_questions[23:]

    print(f"\n   📊 Deposit Beta: {len(beta_qs)} questions")
    print(f"   📊 Vintage Analysis: {len(vintage_qs)} questions")
    print(f"   📊 Stress Testing: {len(stress_qs)} questions")
    print(f"   📊 PPNR Forecasting: {len(ppnr_qs)} questions")
    print(f"   📊 Cross-Domain: {len(complex_qs)} questions")

    # Ensure version is set (required by API)
    if "version" not in current_config or current_config["version"] is None:
        current_config["version"] = 2

    # Add sample questions to config
    if "config" not in current_config:
        current_config["config"] = {}
    current_config["config"]["sample_questions"] = sample_questions

    # Save updated config
    output_file = "/tmp/genie_space_with_questions.json"
    with open(output_file, "w") as f:
        json.dump(current_config, f, indent=2)
    print(f"\n   ✅ Saved updated config to {output_file}")

    # Prepare API payload
    payload = {
        "serialized_space": json.dumps(current_config)
    }

    payload_file = "/tmp/genie_questions_payload.json"
    with open(payload_file, "w") as f:
        json.dump(payload, f, indent=2)

    # Execute PATCH request
    print("\n🚀 Updating Genie Space via API...")
    try:
        cmd = [
            "databricks", "api", "patch",
            f"/api/2.0/genie/spaces/{SPACE_ID}",
            "--json", f"@{payload_file}"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        print("\n✅ SUCCESS - Sample questions added to Genie Space!")
        print("\n" + "=" * 70)
        print("SAMPLE QUESTIONS ADDED")
        print("=" * 70)

        print(f"\n📊 Deposit Beta ({len(beta_qs)} questions):")
        for q in beta_qs:
            print(f"   • {q['question'][0]}")

        print(f"\n📊 Vintage Analysis ({len(vintage_qs)} questions):")
        for q in vintage_qs:
            print(f"   • {q['question'][0]}")

        print(f"\n📊 Stress Testing ({len(stress_qs)} questions):")
        for q in stress_qs:
            print(f"   • {q['question'][0]}")

        print(f"\n📊 PPNR Forecasting ({len(ppnr_qs)} questions):")
        for q in ppnr_qs:
            print(f"   • {q['question'][0]}")

        print(f"\n📊 Cross-Domain ({len(complex_qs)} questions):")
        for q in complex_qs:
            print(f"   • {q['question'][0]}")

        print("\n" + "=" * 70)
        print("NEXT STEPS")
        print("=" * 70)
        print("\n1. Open Genie Space in Databricks UI")
        print("2. Verify sample questions appear in the space")
        print("3. Click on sample questions to test them")
        print("4. Users can now see suggested queries when they open the space!")

    except subprocess.CalledProcessError as e:
        print(f"\n❌ FAILED to update Genie Space")
        print(f"\nError: {e.stderr}")
        print(f"\nTroubleshooting:")
        print(f"1. Review payload: {payload_file}")
        print(f"2. Review config: {output_file}")
        print(f"3. Check API permissions")


if __name__ == "__main__":
    update_space_with_sample_questions()
