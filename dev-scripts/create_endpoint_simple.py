#!/usr/bin/env python3
import requests
import json
import os

# Get Databricks config
profile = "DEFAULT"
config_file = os.path.expanduser("~/.databrickscfg")

host = None
token = None

with open(config_file, 'r') as f:
    in_profile = False
    for line in f:
        line = line.strip()
        if line == f"[{profile}]":
            in_profile = True
        elif line.startswith('['):
            in_profile = False
        elif in_profile:
            if line.startswith('host'):
                host = line.split('=', 1)[1].strip()
            elif line.startswith('token'):
                token = line.split('=', 1)[1].strip()

if not host or not token:
    print("Error: Could not find host or token in ~/.databrickscfg")
    exit(1)

# Create endpoint
url = f"{host}/api/2.0/serving-endpoints"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

payload = {
    "name": "deposit-beta-model-pravin-varma",
    "config": {
        "served_entities": [{
            "entity_name": "cfo_banking_demo.models.deposit_beta_model",
            "entity_version": "1",
            "workload_size": "Small",
            "scale_to_zero_enabled": True
        }]
    }
}

print("Creating serving endpoint for deposit_beta_model...")
print(f"Endpoint name: deposit-beta-model-pravin-varma")

try:
    response = requests.post(url, headers=headers, json=payload, timeout=30)

    if response.status_code in [200, 201]:
        result = response.json()
        print(f"\n✓ Serving endpoint created successfully!")
        print(f"  Name: {result.get('name', 'N/A')}")
        print(f"  State: {result.get('state', {}).get('config_update', 'CREATING')}")
        print(f"\nThe endpoint will take several minutes to become ready.")
        print(f"You can check its status in the Databricks UI under 'Serving'.")
    else:
        print(f"\nError: {response.status_code}")
        print(response.text)

except Exception as e:
    print(f"Error: {e}")
