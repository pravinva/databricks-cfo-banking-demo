#!/usr/bin/env python3
"""
Comprehensive Backfill: GL Entries and Subledger for ALL Assets
Generates accounting entries for loans, securities, and deposits
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agent_tools_library import CFOAgentTools
from datetime import datetime, timedelta, date
import random

def log_message(message, level="INFO"):
    """Log messages with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

class AccountingBackfill:
    def __init__(self):
        self.agent = CFOAgentTools()
        self.current_date = date.today()

    def backfill_loans(self, batch_size=500):
        """Backfill GL and subledger for loans"""
        log_message("=== Starting Loans Backfill ===")

        # Get loans
        loans_query = """
            SELECT
                l.loan_id,
                l.product_type,
                l.current_balance,
                l.original_amount,
                l.interest_rate,
                l.origination_date,
                l.cecl_reserve
            FROM cfo_banking_demo.silver_finance.loan_portfolio l
            LEFT JOIN cfo_banking_demo.silver_finance.gl_entries gl
                ON gl.source_transaction_id = l.loan_id
            WHERE l.is_current = true
            AND gl.entry_id IS NULL
            LIMIT 100000
        """

        result = self.agent.query_unity_catalog(loans_query)
        if not result["success"]:
            log_message(f"Failed to fetch loans: {result.get('error')}", "ERROR")
            return

        loans = result["data"]
        log_message(f"Found {len(loans)} loans")

        for i in range(0, len(loans), batch_size):
            batch = loans[i:i+batch_size]
            self._insert_loan_accounting_batch(batch)
            log_message(f"Processed {min(i+batch_size, len(loans))}/{len(loans)} loans")

        log_message("Loans backfill completed!")

    def _insert_loan_accounting_batch(self, loans):
        """Insert GL header, lines, and subledger for loans"""

        gl_headers = []
        gl_lines = []
        subledger_entries = []

        for loan in loans:
            loan_id = loan[0]
            product_type = loan[1]
            current_balance = float(loan[2]) if loan[2] else 0
            original_amount = float(loan[3]) if loan[3] else 0
            interest_rate = float(loan[4]) if loan[4] else 0
            origination_date = loan[5]
            cecl_reserve = float(loan[6]) if loan[6] else 0

            # GL Header
            entry_id = f"GLE-{loan_id}"
            gl_headers.append({
                'entry_id': entry_id,
                'entry_date': origination_date,
                'entry_timestamp': datetime.now().isoformat(),
                'posting_date': origination_date,
                'accounting_period': origination_date[:7],  # YYYY-MM
                'entry_type': 'Loan Origination',
                'source_system': 'BACKFILL',
                'source_transaction_id': loan_id,
                'batch_id': f'BACKFILL-{self.current_date}',
                'entry_status': 'Posted',
                'description': f'Loan origination - {loan_id}',
                'total_debits': original_amount,
                'total_credits': original_amount,
                'created_by': 'SYSTEM',
                'approved_by': 'SYSTEM',
                'is_balanced': True,
                'is_reversed': False,
                'reversed_by_entry_id': None,
                'effective_timestamp': datetime.now().isoformat()
            })

            # GL Lines - Debit (Loan Asset)
            loan_account = {'C&I': '1010', 'Commercial_RE': '1020', 'Residential_Mortgage': '1030', 'Consumer_Auto': '1040'}.get(product_type, '1000')

            gl_lines.append({
                'line_id': f"{entry_id}-L1",
                'entry_id': entry_id,
                'line_number': 1,
                'account_number': loan_account,
                'debit_amount': original_amount,
                'credit_amount': 0,
                'line_description': f'Loan disbursement - {product_type}',
                'cost_center': 'LENDING',
                'department': 'OPERATIONS',
                'product_code': product_type,
                'customer_id': loan_id,
                'reference_number': loan_id,
                'effective_timestamp': datetime.now().isoformat()
            })

            # GL Lines - Credit (Cash)
            gl_lines.append({
                'line_id': f"{entry_id}-L2",
                'entry_id': entry_id,
                'line_number': 2,
                'account_number': '1000',
                'debit_amount': 0,
                'credit_amount': original_amount,
                'line_description': 'Cash disbursement',
                'cost_center': 'LENDING',
                'department': 'OPERATIONS',
                'product_code': product_type,
                'customer_id': loan_id,
                'reference_number': loan_id,
                'effective_timestamp': datetime.now().isoformat()
            })

            # Subledger - Origination
            subledger_entries.append({
                'transaction_id': f"LST-{loan_id}-ORIG",
                'transaction_timestamp': datetime.now().isoformat(),
                'posting_date': origination_date,
                'loan_id': loan_id,
                'transaction_type': 'Origination',
                'principal_amount': original_amount,
                'interest_amount': 0,
                'fee_amount': 0,
                'balance_before': 0,
                'balance_after': original_amount,
                'gl_entry_id': entry_id,
                'payment_method': 'ACH',
                'description': 'Loan origination',
                'effective_timestamp': datetime.now().isoformat()
            })

            # Subledger - Simulated payments
            balance = original_amount
            for j in range(random.randint(2, 4)):
                payment_date = (datetime.fromisoformat(origination_date) + timedelta(days=30*(j+1))).date().isoformat()
                principal_payment = original_amount / 360 * 30
                interest_payment = balance * (interest_rate / 100 / 12)
                balance_before = balance
                balance -= principal_payment

                subledger_entries.append({
                    'transaction_id': f"LST-{loan_id}-PAY{j+1}",
                    'transaction_timestamp': datetime.now().isoformat(),
                    'posting_date': payment_date,
                    'loan_id': loan_id,
                    'transaction_type': 'Payment',
                    'principal_amount': principal_payment,
                    'interest_amount': interest_payment,
                    'fee_amount': 0,
                    'balance_before': balance_before,
                    'balance_after': max(balance, 0),
                    'gl_entry_id': entry_id,
                    'payment_method': 'ACH',
                    'description': f'Monthly payment {j+1}',
                    'effective_timestamp': datetime.now().isoformat()
                })

        # Bulk insert
        self._bulk_insert_gl_headers(gl_headers)
        self._bulk_insert_gl_lines(gl_lines)
        self._bulk_insert_loan_subledger(subledger_entries)

    def backfill_securities(self, batch_size=500):
        """Backfill GL for securities purchases"""
        log_message("=== Starting Securities Backfill ===")

        securities_query = """
            SELECT
                security_id,
                security_type,
                security_name,
                market_value,
                book_value,
                purchase_date
            FROM cfo_banking_demo.silver_finance.securities
            WHERE is_current = true
            LIMIT 1000
        """

        result = self.agent.query_unity_catalog(securities_query)
        if not result["success"]:
            log_message(f"Failed to fetch securities", "ERROR")
            return

        securities = result["data"]
        log_message(f"Found {len(securities)} securities")

        for i in range(0, len(securities), batch_size):
            batch = securities[i:i+batch_size]
            self._insert_securities_accounting_batch(batch)
            log_message(f"Processed {min(i+batch_size, len(securities))}/{len(securities)} securities")

        log_message("Securities backfill completed!")

    def _insert_securities_accounting_batch(self, securities):
        """Insert GL for securities"""

        gl_headers = []
        gl_lines = []

        for sec in securities:
            security_id = sec[0]
            security_type = sec[1]
            security_name = sec[2]  # security_name instead of issuer
            market_value = float(sec[3]) if sec[3] else 0
            book_value = float(sec[4]) if sec[4] else market_value  # book_value instead of purchase_price
            purchase_date = sec[5]

            entry_id = f"GLE-SEC-{security_id}"

            gl_headers.append({
                'entry_id': entry_id,
                'entry_date': purchase_date,
                'entry_timestamp': datetime.now().isoformat(),
                'posting_date': purchase_date,
                'accounting_period': purchase_date[:7] if purchase_date else '2024-01',
                'entry_type': 'Security Purchase',
                'source_system': 'BACKFILL',
                'source_transaction_id': security_id,
                'batch_id': f'BACKFILL-{self.current_date}',
                'entry_status': 'Posted',
                'description': f'Security purchase - {security_name}',
                'total_debits': book_value,
                'total_credits': book_value,
                'created_by': 'SYSTEM',
                'approved_by': 'SYSTEM',
                'is_balanced': True,
                'is_reversed': False,
                'reversed_by_entry_id': None,
                'effective_timestamp': datetime.now().isoformat()
            })

            # Debit - Securities
            gl_lines.append({
                'line_id': f"{entry_id}-L1",
                'entry_id': entry_id,
                'line_number': 1,
                'account_number': '1200',
                'debit_amount': book_value,
                'credit_amount': 0,
                'line_description': f'Security purchase - {security_type}',
                'cost_center': 'TREASURY',
                'department': 'INVESTMENTS',
                'product_code': security_type,
                'customer_id': None,
                'reference_number': security_id,
                'effective_timestamp': datetime.now().isoformat()
            })

            # Credit - Cash
            gl_lines.append({
                'line_id': f"{entry_id}-L2",
                'entry_id': entry_id,
                'line_number': 2,
                'account_number': '1000',
                'debit_amount': 0,
                'credit_amount': book_value,
                'line_description': 'Cash payment for security',
                'cost_center': 'TREASURY',
                'department': 'INVESTMENTS',
                'product_code': security_type,
                'customer_id': None,
                'reference_number': security_id,
                'effective_timestamp': datetime.now().isoformat()
            })

        self._bulk_insert_gl_headers(gl_headers)
        self._bulk_insert_gl_lines(gl_lines)

    def backfill_deposits(self, batch_size=500):
        """Backfill GL and subledger for deposits"""
        log_message("=== Starting Deposits Backfill ===")

        deposits_query = """
            SELECT
                account_id,
                customer_name,
                product_type,
                current_balance,
                stated_rate,
                account_open_date
            FROM cfo_banking_demo.bronze_core_banking.deposit_accounts
            WHERE account_status = 'Active'
            LIMIT 5000
        """

        result = self.agent.query_unity_catalog(deposits_query)
        if not result["success"]:
            log_message(f"Failed to fetch deposits", "ERROR")
            return

        deposits = result["data"]
        log_message(f"Found {len(deposits)} deposits")

        for i in range(0, len(deposits), batch_size):
            batch = deposits[i:i+batch_size]
            self._insert_deposits_accounting_batch(batch)
            log_message(f"Processed {min(i+batch_size, len(deposits))}/{len(deposits)} deposits")

        log_message("Deposits backfill completed!")

    def _insert_deposits_accounting_batch(self, deposits):
        """Insert GL and subledger for deposits"""

        gl_headers = []
        gl_lines = []
        deposit_subledger = []

        for dep in deposits:
            account_id = dep[0]
            customer_name = dep[1]
            product_type = dep[2]
            current_balance = float(dep[3]) if dep[3] else 0
            stated_rate = float(dep[4]) if dep[4] else 0
            account_open_date = dep[5]

            entry_id = f"GLE-DEP-{account_id}"

            gl_headers.append({
                'entry_id': entry_id,
                'entry_date': account_open_date,
                'entry_timestamp': datetime.now().isoformat(),
                'posting_date': account_open_date,
                'accounting_period': account_open_date[:7],
                'entry_type': 'Deposit Opening',
                'source_system': 'BACKFILL',
                'source_transaction_id': account_id,
                'batch_id': f'BACKFILL-{self.current_date}',
                'entry_status': 'Posted',
                'description': f'Deposit account opening - {customer_name}',
                'total_debits': current_balance,
                'total_credits': current_balance,
                'created_by': 'SYSTEM',
                'approved_by': 'SYSTEM',
                'is_balanced': True,
                'is_reversed': False,
                'reversed_by_entry_id': None,
                'effective_timestamp': datetime.now().isoformat()
            })

            # Debit - Cash
            gl_lines.append({
                'line_id': f"{entry_id}-L1",
                'entry_id': entry_id,
                'line_number': 1,
                'account_number': '1000',
                'debit_amount': current_balance,
                'credit_amount': 0,
                'line_description': f'Deposit receipt - {product_type}',
                'cost_center': 'DEPOSITS',
                'department': 'OPERATIONS',
                'product_code': product_type,
                'customer_id': account_id,
                'reference_number': account_id,
                'effective_timestamp': datetime.now().isoformat()
            })

            # Credit - Deposit Liability
            deposit_account = {'Checking': '2010', 'Savings': '2020', 'Money_Market': '2030', 'CD': '2040'}.get(product_type, '2000')

            gl_lines.append({
                'line_id': f"{entry_id}-L2",
                'entry_id': entry_id,
                'line_number': 2,
                'account_number': deposit_account,
                'debit_amount': 0,
                'credit_amount': current_balance,
                'line_description': f'Deposit liability - {product_type}',
                'cost_center': 'DEPOSITS',
                'department': 'OPERATIONS',
                'product_code': product_type,
                'customer_id': account_id,
                'reference_number': account_id,
                'effective_timestamp': datetime.now().isoformat()
            })

            # Deposit subledger
            deposit_subledger.append({
                'transaction_id': f"DST-{account_id}-OPEN",
                'transaction_timestamp': datetime.now().isoformat(),
                'posting_date': account_open_date,
                'account_id': account_id,
                'transaction_type': 'Opening',
                'transaction_amount': current_balance,
                'balance_before': 0,
                'balance_after': current_balance,
                'gl_entry_id': entry_id,
                'channel': 'BRANCH',
                'description': 'Account opening deposit',
                'effective_timestamp': datetime.now().isoformat()
            })

        self._bulk_insert_gl_headers(gl_headers)
        self._bulk_insert_gl_lines(gl_lines)
        self._bulk_insert_deposit_subledger(deposit_subledger)

    def _bulk_insert_gl_headers(self, headers):
        """Bulk insert GL headers"""
        if not headers:
            return

        values_list = []
        for h in headers:
            values_list.append(f"""(
                '{h['entry_id']}', '{h['entry_date']}', '{h['entry_timestamp']}', '{h['posting_date']}',
                '{h['accounting_period']}', '{h['entry_type']}', '{h['source_system']}', '{h['source_transaction_id']}',
                '{h['batch_id']}', '{h['entry_status']}', '{h['description']}',
                {h['total_debits']}, {h['total_credits']}, '{h['created_by']}', '{h['approved_by']}',
                {str(h['is_balanced']).lower()}, {str(h['is_reversed']).lower()}, NULL, '{h['effective_timestamp']}'
            )""")

        insert_sql = f"""
            INSERT INTO cfo_banking_demo.silver_finance.gl_entries
            VALUES {', '.join(values_list)}
        """

        result = self.agent.query_unity_catalog(insert_sql)
        if not result["success"]:
            log_message(f"Failed to insert GL headers: {result.get('error')}", "ERROR")

    def _bulk_insert_gl_lines(self, lines):
        """Bulk insert GL lines"""
        if not lines:
            return

        values_list = []
        for l in lines:
            customer_id = f"'{l['customer_id']}'" if l['customer_id'] else "NULL"
            values_list.append(f"""(
                '{l['line_id']}', '{l['entry_id']}', {l['line_number']}, '{l['account_number']}',
                {l['debit_amount']}, {l['credit_amount']}, '{l['line_description']}',
                '{l['cost_center']}', '{l['department']}', '{l['product_code']}',
                {customer_id}, '{l['reference_number']}', '{l['effective_timestamp']}'
            )""")

        insert_sql = f"""
            INSERT INTO cfo_banking_demo.silver_finance.gl_entry_lines
            VALUES {', '.join(values_list)}
        """

        result = self.agent.query_unity_catalog(insert_sql)
        if not result["success"]:
            log_message(f"Failed to insert GL lines: {result.get('error')}", "ERROR")

    def _bulk_insert_loan_subledger(self, entries):
        """Bulk insert loan subledger"""
        if not entries:
            return

        values_list = []
        for e in entries:
            values_list.append(f"""(
                '{e['transaction_id']}', '{e['transaction_timestamp']}', '{e['posting_date']}',
                '{e['loan_id']}', '{e['transaction_type']}', {e['principal_amount']},
                {e['interest_amount']}, {e['fee_amount']}, {e['balance_before']}, {e['balance_after']},
                '{e['gl_entry_id']}', '{e['payment_method']}', '{e['description']}', '{e['effective_timestamp']}'
            )""")

        insert_sql = f"""
            INSERT INTO cfo_banking_demo.silver_finance.loan_subledger
            VALUES {', '.join(values_list)}
        """

        result = self.agent.query_unity_catalog(insert_sql)
        if not result["success"]:
            log_message(f"Failed to insert loan subledger: {result.get('error')}", "ERROR")

    def _bulk_insert_deposit_subledger(self, entries):
        """Bulk insert deposit subledger"""
        if not entries:
            return

        values_list = []
        for e in entries:
            values_list.append(f"""(
                '{e['transaction_id']}', '{e['transaction_timestamp']}', '{e['posting_date']}',
                '{e['account_id']}', '{e['transaction_type']}', {e['transaction_amount']},
                {e['balance_before']}, {e['balance_after']}, '{e['gl_entry_id']}',
                '{e['channel']}', '{e['description']}', '{e['effective_timestamp']}'
            )""")

        insert_sql = f"""
            INSERT INTO cfo_banking_demo.silver_finance.deposit_subledger
            VALUES {', '.join(values_list)}
        """

        result = self.agent.query_unity_catalog(insert_sql)
        if not result["success"]:
            log_message(f"Failed to insert deposit subledger: {result.get('error')}", "ERROR")

def main():
    """Main execution"""
    log_message("=== COMPREHENSIVE ACCOUNTING BACKFILL ===")

    backfill = AccountingBackfill()

    # Backfill all asset types
    backfill.backfill_loans(batch_size=250)
    backfill.backfill_securities(batch_size=250)
    backfill.backfill_deposits(batch_size=250)

    log_message("=== ALL BACKFILLS COMPLETE ===")

if __name__ == "__main__":
    main()
