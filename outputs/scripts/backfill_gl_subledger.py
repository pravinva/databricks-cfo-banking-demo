#!/usr/bin/env python3
"""
Backfill GL Entries and Subledger Transactions for Existing Loans
Generates accounting entries for all loans in the loan_portfolio table
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agent_tools_library import CFOAgentTools
from datetime import datetime, timedelta
import random
from decimal import Decimal

def log_message(message, level="INFO"):
    """Log messages with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

class GLSubledgerBackfill:
    def __init__(self):
        self.agent = CFOAgentTools()

    def backfill_gl_entries(self, batch_size=1000):
        """Generate GL entries for all loans"""
        log_message("Starting GL entries backfill...")

        # Get all loans
        loans_query = """
            SELECT
                loan_id,
                borrower_name,
                product_type,
                current_balance,
                original_amount,
                interest_rate,
                origination_date,
                cecl_reserve
            FROM cfo_banking_demo.silver_finance.loan_portfolio
            WHERE is_current = true
            LIMIT 10000
        """

        result = self.agent.query_unity_catalog(loans_query)
        if not result["success"]:
            log_message(f"Failed to fetch loans: {result.get('error')}", "ERROR")
            return

        loans = result["data"]
        log_message(f"Found {len(loans)} loans to process")

        # Process in batches
        for i in range(0, len(loans), batch_size):
            batch = loans[i:i+batch_size]
            self._insert_gl_batch(batch)
            log_message(f"Processed {min(i+batch_size, len(loans))}/{len(loans)} loans")

        log_message("GL entries backfill completed!")

    def _insert_gl_batch(self, loans):
        """Insert GL entries for a batch of loans"""

        gl_entries = []
        for loan in loans:
            loan_id = loan[0]
            product_type = loan[2]
            current_balance = float(loan[3]) if loan[3] else 0
            original_amount = float(loan[4]) if loan[4] else 0
            origination_date = loan[6]
            cecl_reserve = float(loan[7]) if loan[7] else 0

            # Generate entry_id
            entry_id = f"GLE-{loan_id}"
            entry_timestamp = datetime.now().isoformat()

            # Determine GL accounts based on product type
            if product_type == 'C&I':
                loan_account = '1010'
                loan_account_name = 'Loans - Commercial & Industrial'
            elif product_type == 'Commercial_RE':
                loan_account = '1020'
                loan_account_name = 'Loans - Commercial Real Estate'
            elif product_type == 'Residential_Mortgage':
                loan_account = '1030'
                loan_account_name = 'Loans - Residential Mortgage'
            else:  # Consumer_Auto
                loan_account = '1040'
                loan_account_name = 'Loans - Consumer Auto'

            # Create GL entry (Loan origination)
            gl_entries.append({
                'entry_id': entry_id,
                'source_transaction_id': loan_id,
                'entry_timestamp': entry_timestamp,
                'account_number': loan_account,
                'account_name': loan_account_name,
                'debit_amount': original_amount,
                'credit_amount': 0,
                'is_balanced': False,
                'description': f'Loan origination - {loan_id}'
            })

            # Corresponding credit entry (Cash/Funding)
            gl_entries.append({
                'entry_id': f"{entry_id}-CASH",
                'source_transaction_id': loan_id,
                'entry_timestamp': entry_timestamp,
                'account_number': '1000',
                'account_name': 'Cash and Cash Equivalents',
                'debit_amount': 0,
                'credit_amount': original_amount,
                'is_balanced': True,
                'description': f'Loan funding - {loan_id}'
            })

            # CECL reserve entry if exists
            if cecl_reserve > 0:
                gl_entries.append({
                    'entry_id': f"{entry_id}-CECL",
                    'source_transaction_id': loan_id,
                    'entry_timestamp': entry_timestamp,
                    'account_number': '5010',
                    'account_name': 'CECL Provision Expense',
                    'debit_amount': cecl_reserve,
                    'credit_amount': 0,
                    'is_balanced': False,
                    'description': f'CECL reserve - {loan_id}'
                })

                gl_entries.append({
                    'entry_id': f"{entry_id}-CECL-RES",
                    'source_transaction_id': loan_id,
                    'entry_timestamp': entry_timestamp,
                    'account_number': '1090',
                    'account_name': 'Allowance for Credit Losses',
                    'debit_amount': 0,
                    'credit_amount': cecl_reserve,
                    'is_balanced': True,
                    'description': f'CECL reserve contra - {loan_id}'
                })

        # Insert batch
        if gl_entries:
            self._bulk_insert_gl(gl_entries)

    def _bulk_insert_gl(self, gl_entries):
        """Bulk insert GL entries"""

        # Build VALUES clause
        values_list = []
        for entry in gl_entries:
            values_list.append(f"""(
                '{entry['entry_id']}',
                '{entry['source_transaction_id']}',
                '{entry['entry_timestamp']}',
                '{entry['account_number']}',
                '{entry['account_name']}',
                {entry['debit_amount']},
                {entry['credit_amount']},
                {str(entry['is_balanced']).lower()},
                '{entry['description']}'
            )""")

        insert_sql = f"""
            INSERT INTO cfo_banking_demo.silver_finance.gl_entries
            (entry_id, source_transaction_id, entry_timestamp, account_number, account_name,
             debit_amount, credit_amount, is_balanced, description)
            VALUES {', '.join(values_list)}
        """

        result = self.agent.query_unity_catalog(insert_sql)
        if not result["success"]:
            log_message(f"Failed to insert GL entries: {result.get('error')}", "ERROR")

    def backfill_subledger(self, batch_size=1000):
        """Generate subledger transactions for all loans"""
        log_message("Starting subledger backfill...")

        # Get all loans
        loans_query = """
            SELECT
                loan_id,
                current_balance,
                original_amount,
                interest_rate,
                origination_date,
                maturity_date
            FROM cfo_banking_demo.silver_finance.loan_portfolio
            WHERE is_current = true
            LIMIT 10000
        """

        result = self.agent.query_unity_catalog(loans_query)
        if not result["success"]:
            log_message(f"Failed to fetch loans: {result.get('error')}", "ERROR")
            return

        loans = result["data"]
        log_message(f"Found {len(loans)} loans to process")

        # Process in batches
        for i in range(0, len(loans), batch_size):
            batch = loans[i:i+batch_size]
            self._insert_subledger_batch(batch)
            log_message(f"Processed {min(i+batch_size, len(loans))}/{len(loans)} loans")

        log_message("Subledger backfill completed!")

    def _insert_subledger_batch(self, loans):
        """Insert subledger entries for a batch of loans"""

        subledger_entries = []
        for loan in loans:
            loan_id = loan[0]
            current_balance = float(loan[1]) if loan[1] else 0
            original_amount = float(loan[2]) if loan[2] else 0
            interest_rate = float(loan[3]) if loan[3] else 0
            origination_date = loan[4]

            # Generate 3-5 payment transactions per loan
            num_payments = random.randint(3, 5)
            balance = original_amount

            # Origination entry
            subledger_entries.append({
                'transaction_id': f"LST-{loan_id}-ORIG",
                'loan_id': loan_id,
                'transaction_timestamp': origination_date,
                'transaction_type': 'Origination',
                'principal_amount': original_amount,
                'interest_amount': 0,
                'balance_after': balance
            })

            # Payment entries
            for j in range(num_payments):
                # Calculate payment date (monthly)
                payment_date = datetime.fromisoformat(origination_date) + timedelta(days=30*(j+1))

                # Calculate principal and interest
                monthly_rate = interest_rate / 100 / 12
                principal_payment = (original_amount / 360) * 30  # Simplified monthly
                interest_payment = balance * monthly_rate
                balance -= principal_payment

                if balance < 0:
                    balance = 0

                subledger_entries.append({
                    'transaction_id': f"LST-{loan_id}-PAY{j+1}",
                    'loan_id': loan_id,
                    'transaction_timestamp': payment_date.isoformat(),
                    'transaction_type': 'Payment',
                    'principal_amount': principal_payment,
                    'interest_amount': interest_payment,
                    'balance_after': balance
                })

        # Insert batch
        if subledger_entries:
            self._bulk_insert_subledger(subledger_entries)

    def _bulk_insert_subledger(self, subledger_entries):
        """Bulk insert subledger entries"""

        # Build VALUES clause
        values_list = []
        for entry in subledger_entries:
            values_list.append(f"""(
                '{entry['transaction_id']}',
                '{entry['loan_id']}',
                '{entry['transaction_timestamp']}',
                '{entry['transaction_type']}',
                {entry['principal_amount']},
                {entry['interest_amount']},
                {entry['balance_after']}
            )""")

        insert_sql = f"""
            INSERT INTO cfo_banking_demo.silver_finance.loan_subledger
            (transaction_id, loan_id, transaction_timestamp, transaction_type,
             principal_amount, interest_amount, balance_after)
            VALUES {', '.join(values_list)}
        """

        result = self.agent.query_unity_catalog(insert_sql)
        if not result["success"]:
            log_message(f"Failed to insert subledger entries: {result.get('error')}", "ERROR")

def main():
    """Main execution"""
    log_message("=== GL and Subledger Backfill Script ===")

    backfill = GLSubledgerBackfill()

    # Backfill GL entries
    backfill.backfill_gl_entries(batch_size=500)

    # Backfill subledger
    backfill.backfill_subledger(batch_size=500)

    log_message("=== Backfill Complete ===")

if __name__ == "__main__":
    main()
