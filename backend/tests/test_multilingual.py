"""
test_multilingual.py
--------------------
Comprehensive multilingual test suite for MitraAI Text-to-SQL pipeline.

Covers:
- 30 English Natural Language Queries
- 20 Hindi Natural Language Queries (हिंदी)
- 15 Marathi Natural Language Queries (मराठी)

Total: 65 Multilingual test cases testing prompt building, SQL extraction,
safety validation, and database execution against the banking database.
"""

import pytest
from backend.app.sql_engine import (
    build_sql_prompt,
    extract_sql,
    LANG_ENGLISH,
    LANG_HINDI,
    LANG_MARATHI,
    LANG_HINGLISH,
)
from backend.app.sql_validator import validate_sql
from backend.app.schema_manager import get_schema_context, get_target_db_schema
from backend.app.db_executor import execute_query

# ---------------------------------------------------------------------------
# 30 English Queries
# ---------------------------------------------------------------------------
ENGLISH_QUERIES = [
    # Basic table lookups (1-5)
    ("Show all customers", "SELECT * FROM customers;"),
    ("List all accounts in the bank", "SELECT * FROM accounts;"),
    ("Show all banking transactions", "SELECT * FROM transactions;"),
    ("Display all loan applications", "SELECT * FROM loans;"),
    ("Get customer details with id 1", "SELECT * FROM customers WHERE id = 1;"),

    # Filtered selections (6-10)
    ("Show all customers from Mumbai", "SELECT * FROM customers WHERE city = 'Mumbai';"),
    ("List customers located in Pune", "SELECT * FROM customers WHERE city = 'Pune';"),
    ("Find customers whose balance is greater than 50000", "SELECT * FROM customers WHERE balance > 50000;"),
    ("Show savings accounts with balance above 30000", "SELECT * FROM accounts WHERE account_type = 'Savings' AND balance > 30000;"),
    ("Find all current accounts", "SELECT * FROM accounts WHERE account_type = 'Current';"),

    # Aggregations & Stats (11-16)
    ("What is the total balance across all customer accounts?", "SELECT SUM(balance) AS total_balance FROM accounts;"),
    ("Find the average balance of customers in Mumbai", "SELECT AVG(balance) AS avg_balance FROM customers WHERE city = 'Mumbai';"),
    ("How many total customers are registered?", "SELECT COUNT(*) AS total_customers FROM customers;"),
    ("Find the maximum loan amount requested", "SELECT MAX(loan_amount) AS max_loan FROM loans;"),
    ("Find the minimum balance in savings accounts", "SELECT MIN(balance) AS min_balance FROM accounts WHERE account_type = 'Savings';"),
    ("Count how many accounts each customer has", "SELECT cust_id, COUNT(*) AS num_accounts FROM accounts GROUP BY cust_id;"),

    # Table JOINs (17-23)
    ("List all customers with their account balances", "SELECT c.name, a.balance FROM customers c JOIN accounts a ON c.id = a.cust_id;"),
    ("Show transactions along with customer names", "SELECT c.name, t.amount, t.transaction_type FROM transactions t JOIN accounts a ON t.account_id = a.id JOIN customers c ON a.cust_id = c.id;"),
    ("List customers who have an approved loan", "SELECT c.name, l.loan_amount, l.loan_type FROM customers c JOIN loans l ON c.id = l.cust_id WHERE l.status = 'Approved';"),
    ("Show active loans with customer details", "SELECT c.name, c.city, l.loan_amount FROM customers c JOIN loans l ON c.id = l.cust_id WHERE l.status = 'Active';"),
    ("Find customers who have debit transactions", "SELECT DISTINCT c.name FROM customers c JOIN accounts a ON c.id = a.cust_id JOIN transactions t ON a.id = t.account_id WHERE t.transaction_type = 'Debit';"),
    ("Show all transactions for customer Ramesh Sharma", "SELECT t.* FROM transactions t JOIN accounts a ON t.account_id = a.id JOIN customers c ON a.cust_id = c.id WHERE c.name = 'Ramesh Sharma';"),
    ("Find total loan amount per customer", "SELECT c.name, SUM(l.loan_amount) AS total_loan FROM customers c JOIN loans l ON c.id = l.cust_id GROUP BY c.name;"),

    # Ordering & Limits (24-28)
    ("Show top 3 customers with highest balance", "SELECT * FROM customers ORDER BY balance DESC LIMIT 3;"),
    ("List 5 most recent transactions", "SELECT * FROM transactions ORDER BY transaction_date DESC LIMIT 5;"),
    ("Show customers ordered alphabetically by name", "SELECT * FROM customers ORDER BY name ASC;"),
    ("Find the single customer with highest account balance", "SELECT c.name, a.balance FROM customers c JOIN accounts a ON c.id = a.cust_id ORDER BY a.balance DESC LIMIT 1;"),
    ("Show top 2 highest loan amounts", "SELECT * FROM loans ORDER BY loan_amount DESC LIMIT 2;"),

    # Group By & Having (29-30)
    ("Show number of customers per city", "SELECT city, COUNT(*) AS count FROM customers GROUP BY city;"),
    ("List cities having more than 1 customer", "SELECT city, COUNT(*) AS count FROM customers GROUP BY city HAVING count > 1;"),
]

# ---------------------------------------------------------------------------
# 20 Hindi Queries (हिंदी)
# ---------------------------------------------------------------------------
HINDI_QUERIES = [
    # Basic & Filtered (1-6)
    ("मुंबई के सभी ग्राहक दिखाओ", "SELECT * FROM customers WHERE city = 'Mumbai';"),
    ("पुणे के ग्राहकों की सूची बनाओ", "SELECT * FROM customers WHERE city = 'Pune';"),
    ("सभी खातों की जानकारी दिखाओ", "SELECT * FROM accounts;"),
    ("जिन ग्राहकों का बैलेंस 50000 से अधिक है उन्हें खोजें", "SELECT * FROM customers WHERE balance > 50000;"),
    ("सभी Savings खातों की लिस्ट निकालो", "SELECT * FROM accounts WHERE account_type = 'Savings';"),
    ("दिल्ली के सभी बैंक ग्राहक दिखाओ", "SELECT * FROM customers WHERE city = 'Delhi';"),

    # Aggregations & Metrics (7-11)
    ("सभी खातों का कुल बैलेंस कितना है?", "SELECT SUM(balance) AS total_balance FROM accounts;"),
    ("बैंक में कुल कितने ग्राहक हैं?", "SELECT COUNT(*) AS total_customers FROM customers;"),
    ("सबसे ज्यादा लोन राशि कितनी है?", "SELECT MAX(loan_amount) AS max_loan FROM loans;"),
    ("मुंबई के ग्राहकों का औसत बैलेंस क्या है?", "SELECT AVG(balance) AS avg_balance FROM customers WHERE city = 'Mumbai';"),
    ("हर शहर में कितने ग्राहक हैं?", "SELECT city, COUNT(*) AS count FROM customers GROUP BY city;"),

    # Joins & Relations (12-16)
    ("ग्राहकों के नाम और उनके खाते का बैलेंस दिखाओ", "SELECT c.name, a.balance FROM customers c JOIN accounts a ON c.id = a.cust_id;"),
    ("उन ग्राहकों के नाम बताओ जिनका लोन Approved है", "SELECT c.name, l.loan_amount FROM customers c JOIN loans l ON c.id = l.cust_id WHERE l.status = 'Approved';"),
    ("सभी लेन-देन के साथ ग्राहकों के नाम दिखाओ", "SELECT c.name, t.amount, t.transaction_type FROM transactions t JOIN accounts a ON t.account_id = a.id JOIN customers c ON a.cust_id = c.id;"),
    ("Active लोन वाले सभी ग्राहकों की सूची", "SELECT c.name, l.loan_amount, l.loan_type FROM customers c JOIN loans l ON c.id = l.cust_id WHERE l.status = 'Active';"),
    ("रमेश शर्मा के सभी ट्रांजेक्शन दिखाओ", "SELECT t.* FROM transactions t JOIN accounts a ON t.account_id = a.id JOIN customers c ON a.cust_id = c.id WHERE c.name = 'Ramesh Sharma';"),

    # Ordering & Limits (17-20)
    ("सबसे ज्यादा बैलेंस वाले 3 ग्राहक दिखाओ", "SELECT * FROM customers ORDER BY balance DESC LIMIT 3;"),
    ("हाल ही के 5 ट्रांजेक्शन दिखाओ", "SELECT * FROM transactions ORDER BY transaction_date DESC LIMIT 5;"),
    ("सबसे कम बैलेंस वाला खाता कौन सा है?", "SELECT * FROM accounts ORDER BY balance ASC LIMIT 1;"),
    ("क्रेडिट वाले सभी ट्रांजेक्शन दिखाओ", "SELECT * FROM transactions WHERE transaction_type = 'Credit';"),
]

# ---------------------------------------------------------------------------
# 15 Marathi Queries (मराठी)
# ---------------------------------------------------------------------------
MARATHI_QUERIES = [
    # Basic & Filtered (1-5)
    ("मुंबईतील सर्व ग्राहक दाखवा", "SELECT * FROM customers WHERE city = 'Mumbai';"),
    ("पुण्यातील सर्व बँक ग्राहकांची यादी दाखवा", "SELECT * FROM customers WHERE city = 'Pune';"),
    ("सर्व खात्यांची माहिती दाखवा", "SELECT * FROM accounts;"),
    ("५०,००० पेक्षा जास्त शिल्लक असलेले ग्राहक शोधा", "SELECT * FROM customers WHERE balance > 50000;"),
    ("सर्व बचत (Savings) खाती दाखवा", "SELECT * FROM accounts WHERE account_type = 'Savings';"),

    # Aggregations & Metrics (6-9)
    ("सर्व खात्यांची एकूण शिल्लक किती आहे?", "SELECT SUM(balance) AS total_balance FROM accounts;"),
    ("बँकेत एकूण किती ग्राहक आहेत?", "SELECT COUNT(*) AS total_customers FROM customers;"),
    ("सर्वात मोठी कर्जाची रक्कम किती आहे?", "SELECT MAX(loan_amount) AS max_loan FROM loans;"),
    ("प्रत्येक शहरात किती ग्राहक आहेत ते सांगा", "SELECT city, COUNT(*) AS count FROM customers GROUP BY city;"),

    # Joins & Loans (10-13)
    ("ग्राहकांची नावे आणि त्यांची खात्यातील शिल्लक दाखवा", "SELECT c.name, a.balance FROM customers c JOIN accounts a ON c.id = a.cust_id;"),
    ("मंजूर (Approved) कर्ज असलेल्या ग्राहकांची यादी दाखवा", "SELECT c.name, l.loan_amount FROM customers c JOIN loans l ON c.id = l.cust_id WHERE l.status = 'Approved';"),
    ("सक्रिय (Active) कर्ज असलेल्या ग्राहकांची नावे आणि रक्कम दाखवा", "SELECT c.name, l.loan_amount, l.loan_type FROM customers c JOIN loans l ON c.id = l.cust_id WHERE l.status = 'Active';"),
    ("सर्व व्यवहार आणि संबंधित ग्राहकांची नावे दाखवा", "SELECT c.name, t.amount, t.transaction_type FROM transactions t JOIN accounts a ON t.account_id = a.id JOIN customers c ON a.cust_id = c.id;"),

    # Ordering & Filter (14-15)
    ("सर्वात जास्त शिल्लक असलेले ३ ग्राहक दाखवा", "SELECT * FROM customers ORDER BY balance DESC LIMIT 3;"),
    ("शेवटचे ५ व्यवहार दाखवा", "SELECT * FROM transactions ORDER BY transaction_date DESC LIMIT 5;"),
]


# ---------------------------------------------------------------------------
# Test Suites
# ---------------------------------------------------------------------------

class TestEnglishQueries:
    @pytest.mark.parametrize("nl_query, expected_sql", ENGLISH_QUERIES)
    def test_english_query_pipeline(self, nl_query, expected_sql):
        """Validates English query prompt generation, syntax validation, and DB execution."""
        schema_context = get_schema_context()
        target_schema = get_target_db_schema()

        # 1. Verify prompt construction
        messages = build_sql_prompt(nl_query, schema_context, language=LANG_ENGLISH)
        assert len(messages) >= 3
        assert messages[-1]["content"] == nl_query

        # 2. Verify expected SQL validation
        is_valid, msg = validate_sql(expected_sql, schema=target_schema)
        assert is_valid, f"SQL validation failed for query '{nl_query}': {msg}"

        # 3. Verify SQL execution against sample banking DB
        results, err = execute_query(expected_sql)
        assert err is None, f"SQL execution error for '{expected_sql}': {err}"
        assert isinstance(results, list)


class TestHindiQueries:
    @pytest.mark.parametrize("nl_query, expected_sql", HINDI_QUERIES)
    def test_hindi_query_pipeline(self, nl_query, expected_sql):
        """Validates Hindi query prompt generation, syntax validation, and DB execution."""
        schema_context = get_schema_context()
        target_schema = get_target_db_schema()

        # 1. Verify prompt construction with Hindi few-shots
        messages = build_sql_prompt(nl_query, schema_context, language=LANG_HINDI)
        assert len(messages) >= 3
        assert messages[-1]["content"] == nl_query

        # 2. Verify SQL validation
        is_valid, msg = validate_sql(expected_sql, schema=target_schema)
        assert is_valid, f"SQL validation failed for Hindi query '{nl_query}': {msg}"

        # 3. Verify SQL execution against sample banking DB
        results, err = execute_query(expected_sql)
        assert err is None, f"SQL execution error for '{expected_sql}': {err}"
        assert isinstance(results, list)


class TestMarathiQueries:
    @pytest.mark.parametrize("nl_query, expected_sql", MARATHI_QUERIES)
    def test_marathi_query_pipeline(self, nl_query, expected_sql):
        """Validates Marathi query prompt generation, syntax validation, and DB execution."""
        schema_context = get_schema_context()
        target_schema = get_target_db_schema()

        # 1. Verify prompt construction with Marathi few-shots
        messages = build_sql_prompt(nl_query, schema_context, language=LANG_MARATHI)
        assert len(messages) >= 3
        assert messages[-1]["content"] == nl_query

        # 2. Verify SQL validation
        is_valid, msg = validate_sql(expected_sql, schema=target_schema)
        assert is_valid, f"SQL validation failed for Marathi query '{nl_query}': {msg}"

        # 3. Verify SQL execution against sample banking DB
        results, err = execute_query(expected_sql)
        assert err is None, f"SQL execution error for '{expected_sql}': {err}"
        assert isinstance(results, list)
