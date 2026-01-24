"""
WS2-01: Loan Origination Event Generator
Generates streaming JSON events simulating real-time loan originations
"""

import json
import random
import time
from datetime import datetime, timedelta
from decimal import Decimal
import uuid
from typing import Dict, List
import sys
import os

# Add to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.catalog import VolumeType


class LoanOriginationEventGenerator:
    """Generate realistic loan origination events for streaming ingestion"""

    def __init__(self):
        self.borrower_names = self._load_borrower_names()
        self.loan_officers = self._load_loan_officers()
        self.branches = self._load_branches()

    def _load_borrower_names(self) -> List[str]:
        """Generate pool of borrower names"""
        first_names = ['John', 'Jane', 'Michael', 'Sarah', 'David', 'Emily', 'Robert', 'Lisa',
                       'William', 'Jennifer', 'James', 'Mary', 'Christopher', 'Patricia']
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller',
                      'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Wilson']
        companies = ['Acme Corp', 'TechVentures LLC', 'Global Imports Inc', 'Regional Foods Co',
                     'Premier Manufacturing', 'Sunrise Properties', 'Metro Construction']

        personal = [f"{f} {l}" for f in first_names for l in last_names[:5]]
        business = companies
        return personal + business

    def _load_loan_officers(self) -> List[Dict]:
        """Load loan officer roster"""
        return [
            {'id': 'LO-001', 'name': 'Alice Thompson', 'specialty': 'Commercial'},
            {'id': 'LO-002', 'name': 'Bob Martinez', 'specialty': 'Consumer'},
            {'id': 'LO-003', 'name': 'Carol Johnson', 'specialty': 'Real Estate'},
            {'id': 'LO-004', 'name': 'David Chen', 'specialty': 'Commercial'},
            {'id': 'LO-005', 'name': 'Eva Rodriguez', 'specialty': 'Consumer'},
        ]

    def _load_branches(self) -> List[Dict]:
        """Load branch locations"""
        return [
            {'id': 'BR-NYC-001', 'name': 'New York Main', 'region': 'Northeast'},
            {'id': 'BR-CHI-001', 'name': 'Chicago Loop', 'region': 'Midwest'},
            {'id': 'BR-LAX-001', 'name': 'Los Angeles Downtown', 'region': 'West'},
            {'id': 'BR-MIA-001', 'name': 'Miami Beach', 'region': 'Southeast'},
            {'id': 'BR-DAL-001', 'name': 'Dallas Central', 'region': 'Southwest'},
        ]

    def generate_event(self, product_type: str = None) -> Dict:
        """
        Generate a single loan origination event

        Args:
            product_type: Optional product type, otherwise random

        Returns:
            Dict containing loan origination event data
        """
        if product_type is None:
            product_type = random.choice([
                'Commercial_RE', 'C&I', 'Residential_Mortgage',
                'Consumer_Auto', 'Consumer_Personal'
            ])

        # Event metadata
        event_id = str(uuid.uuid4())
        event_timestamp = datetime.now().isoformat()

        # Loan details based on product type
        loan_configs = {
            'Commercial_RE': {
                'amount_range': (500_000, 25_000_000),
                'rate_range': (6.5, 9.5),
                'term_range': (60, 300),
                'prefix': 'CRE'
            },
            'C&I': {
                'amount_range': (100_000, 10_000_000),
                'rate_range': (5.5, 8.5),
                'term_range': (12, 84),
                'prefix': 'CNI'
            },
            'Residential_Mortgage': {
                'amount_range': (150_000, 1_500_000),
                'rate_range': (6.0, 7.5),
                'term_range': (180, 360),
                'prefix': 'RES'
            },
            'Consumer_Auto': {
                'amount_range': (15_000, 75_000),
                'rate_range': (4.5, 8.9),
                'term_range': (36, 72),
                'prefix': 'AUTO'
            },
            'Consumer_Personal': {
                'amount_range': (5_000, 50_000),
                'rate_range': (9.5, 18.9),
                'term_range': (12, 60),
                'prefix': 'PERS'
            }
        }

        config = loan_configs[product_type]

        # Generate loan details
        loan_amount = round(random.uniform(*config['amount_range']), 2)
        interest_rate = round(random.uniform(*config['rate_range']), 2)
        term_months = random.choice([36, 48, 60, 84, 120, 180, 240, 300, 360])

        # Calculate monthly payment
        monthly_rate = interest_rate / 100 / 12
        num_payments = term_months
        if monthly_rate > 0:
            monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate) ** num_payments) / \
                              ((1 + monthly_rate) ** num_payments - 1)
        else:
            monthly_payment = loan_amount / num_payments

        # Select borrower and officers
        borrower = random.choice(self.borrower_names)
        loan_officer = random.choice(self.loan_officers)
        branch = random.choice(self.branches)

        # Credit score and risk rating
        credit_score = random.randint(620, 850)
        if credit_score >= 750:
            risk_rating = 'A'
        elif credit_score >= 700:
            risk_rating = 'B'
        elif credit_score >= 650:
            risk_rating = 'C'
        else:
            risk_rating = 'D'

        # GL impact for double-entry bookkeeping
        gl_entries = [
            {
                'account_number': '1100',  # Loans Receivable (Asset)
                'account_name': 'Loans Receivable',
                'debit': loan_amount,
                'credit': 0.0,
                'entry_type': 'debit'
            },
            {
                'account_number': '2100',  # Customer Deposits (Liability) or Cash (Asset)
                'account_name': 'Customer Deposit Account',
                'debit': 0.0,
                'credit': loan_amount,
                'entry_type': 'credit'
            }
        ]

        # Construct event
        event = {
            # Event metadata
            'event_id': event_id,
            'event_type': 'LOAN_ORIGINATION',
            'event_timestamp': event_timestamp,
            'source_system': 'LOS',  # Loan Origination System
            'event_version': '1.0',

            # Loan identifiers
            'loan_id': f"{config['prefix']}-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}",
            'application_id': f"APP-{random.randint(100000, 999999)}",

            # Borrower information
            'borrower': {
                'name': borrower,
                'credit_score': credit_score,
                'annual_income': round(loan_amount * random.uniform(2.5, 5.0), 2),
                'employment_status': random.choice(['Employed', 'Self-Employed', 'Business']),
                'years_at_residence': random.randint(1, 15)
            },

            # Loan details
            'loan': {
                'product_type': product_type,
                'principal_amount': loan_amount,
                'interest_rate': interest_rate,
                'term_months': term_months,
                'monthly_payment': round(monthly_payment, 2),
                'origination_date': datetime.now().strftime('%Y-%m-%d'),
                'first_payment_date': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
                'maturity_date': (datetime.now() + timedelta(days=term_months * 30)).strftime('%Y-%m-%d'),
                'loan_purpose': random.choice([
                    'Purchase', 'Refinance', 'Cash-Out Refinance', 'Home Improvement',
                    'Working Capital', 'Equipment', 'Real Estate Investment'
                ]),
                'collateral_type': random.choice([
                    'Real Estate', 'Equipment', 'Inventory', 'Accounts Receivable',
                    'Vehicle', 'Unsecured', 'Personal Guarantee'
                ]) if product_type != 'Consumer_Personal' else 'Unsecured'
            },

            # Risk assessment
            'risk': {
                'risk_rating': risk_rating,
                'probability_of_default': round(random.uniform(0.01, 0.15), 4),
                'loss_given_default': round(random.uniform(0.20, 0.45), 4),
                'risk_weight': 1.0 if risk_rating in ['C', 'D'] else 0.75,
                'cecl_reserve_rate': round(random.uniform(0.01, 0.05), 4)
            },

            # Origination details
            'origination': {
                'loan_officer_id': loan_officer['id'],
                'loan_officer_name': loan_officer['name'],
                'branch_id': branch['id'],
                'branch_name': branch['name'],
                'region': branch['region'],
                'channel': random.choice(['Branch', 'Online', 'Broker', 'Direct Mail']),
                'approval_date': (datetime.now() - timedelta(days=random.randint(1, 7))).strftime('%Y-%m-%d')
            },

            # Fees and charges
            'fees': {
                'origination_fee': round(loan_amount * random.uniform(0.005, 0.02), 2),
                'processing_fee': round(random.uniform(100, 500), 2),
                'appraisal_fee': round(random.uniform(300, 600), 2) if product_type in ['Commercial_RE', 'Residential_Mortgage'] else 0.0,
                'total_fees': 0.0  # Will be calculated
            },

            # GL impact (double-entry bookkeeping)
            'gl_entries': gl_entries,

            # Liquidity impact
            'liquidity_impact': {
                'cash_outflow': loan_amount,  # Cash leaving the bank
                'balance_sheet_impact': loan_amount,  # Asset increase
                'tier': 'immediate',  # Cash flow timing
                'business_day': datetime.now().strftime('%Y-%m-%d')
            },

            # Regulatory impact
            'regulatory': {
                'call_report_schedule': 'RC-C',  # FFIEC 031 Schedule
                'asset_category': 'Loans and Leases',
                'risk_weighted_assets_impact': round(loan_amount * (1.0 if risk_rating in ['C', 'D'] else 0.75), 2),
                'alll_reserve_impact': round(loan_amount * random.uniform(0.01, 0.05), 2)
            }
        }

        # Calculate total fees
        event['fees']['total_fees'] = sum([
            event['fees']['origination_fee'],
            event['fees']['processing_fee'],
            event['fees']['appraisal_fee']
        ])

        return event

    def generate_stream(self, rate_per_minute: int = 10, duration_minutes: int = 60):
        """
        Generate continuous stream of loan origination events

        Args:
            rate_per_minute: Number of events per minute
            duration_minutes: How long to generate events

        Yields:
            Dict: Loan origination events
        """
        interval = 60.0 / rate_per_minute  # seconds between events
        end_time = datetime.now() + timedelta(minutes=duration_minutes)

        print(f"Starting event stream: {rate_per_minute} events/min for {duration_minutes} minutes")
        print(f"Interval: {interval:.2f} seconds between events")

        event_count = 0
        while datetime.now() < end_time:
            event = self.generate_event()
            event_count += 1

            yield event

            time.sleep(interval)

        print(f"Stream complete: Generated {event_count} events")

    def write_to_volume(self, w: WorkspaceClient, volume_path: str, num_events: int = 100):
        """
        Write events to Databricks Volume for Delta Live Tables ingestion

        Args:
            w: WorkspaceClient
            volume_path: Path to volume (e.g., /Volumes/catalog/schema/volume)
            num_events: Number of events to generate
        """
        print(f"Generating {num_events} events to {volume_path}")

        # Create events directory
        events_dir = f"{volume_path}/loan_origination_events"

        # Generate events in batches
        batch_size = 10
        for batch_num in range(0, num_events, batch_size):
            events = []
            for _ in range(min(batch_size, num_events - batch_num)):
                event = self.generate_event()
                events.append(event)

            # Write batch to JSON file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{events_dir}/events_{timestamp}_{batch_num:06d}.json"

            # Write using Databricks File API
            content = '\n'.join([json.dumps(event) for event in events])

            with open(f"/tmp/batch_{batch_num}.json", 'w') as f:
                f.write(content)

            print(f"  Batch {batch_num // batch_size + 1}: {len(events)} events written")

        print(f"✓ Generated {num_events} events")


def main():
    """Main execution"""
    print("="*80)
    print("WS2-01: Loan Origination Event Generator")
    print("="*80)

    generator = LoanOriginationEventGenerator()

    # Generate sample events
    print("\n=== Sample Event ===")
    sample_event = generator.generate_event('Commercial_RE')
    print(json.dumps(sample_event, indent=2))

    # Generate batch of events to file system
    print("\n=== Generating Event Batch ===")
    output_dir = "/Users/pravin.varma/Documents/Demo/databricks-cfo-banking-demo/data/loan_events"
    os.makedirs(output_dir, exist_ok=True)

    events = []
    for i in range(100):
        event = generator.generate_event()
        events.append(event)

    # Write to JSON lines file
    output_file = f"{output_dir}/loan_originations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
    with open(output_file, 'w') as f:
        for event in events:
            f.write(json.dumps(event) + '\n')

    print(f"✓ Wrote {len(events)} events to {output_file}")

    # Summary statistics
    print("\n=== Event Statistics ===")
    product_counts = {}
    total_amount = 0
    for event in events:
        product = event['loan']['product_type']
        product_counts[product] = product_counts.get(product, 0) + 1
        total_amount += event['loan']['principal_amount']

    print(f"Total Events: {len(events)}")
    print(f"Total Loan Amount: ${total_amount:,.2f}")
    print(f"\nBy Product Type:")
    for product, count in sorted(product_counts.items()):
        print(f"  {product}: {count} ({count/len(events)*100:.1f}%)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
