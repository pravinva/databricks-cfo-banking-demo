-- Grant SELECT and MODIFY permissions to all account users for cfo_banking_demo catalog

-- Grant catalog-level permissions
GRANT USE CATALOG ON CATALOG cfo_banking_demo TO `account users`;
GRANT SELECT ON CATALOG cfo_banking_demo TO `account users`;
GRANT MODIFY ON CATALOG cfo_banking_demo TO `account users`;

-- Grant schema-level permissions for silver_finance
GRANT USE SCHEMA ON SCHEMA cfo_banking_demo.silver_finance TO `account users`;
GRANT SELECT ON SCHEMA cfo_banking_demo.silver_finance TO `account users`;
GRANT MODIFY ON SCHEMA cfo_banking_demo.silver_finance TO `account users`;

-- Grant schema-level permissions for silver_treasury
GRANT USE SCHEMA ON SCHEMA cfo_banking_demo.silver_treasury TO `account users`;
GRANT SELECT ON SCHEMA cfo_banking_demo.silver_treasury TO `account users`;
GRANT MODIFY ON SCHEMA cfo_banking_demo.silver_treasury TO `account users`;

-- Grant schema-level permissions for gold_regulatory
GRANT USE SCHEMA ON SCHEMA cfo_banking_demo.gold_regulatory TO `account users`;
GRANT SELECT ON SCHEMA cfo_banking_demo.gold_regulatory TO `account users`;
GRANT MODIFY ON SCHEMA cfo_banking_demo.gold_regulatory TO `account users`;

-- Grant schema-level permissions for bronze_market_data
GRANT USE SCHEMA ON SCHEMA cfo_banking_demo.bronze_market_data TO `account users`;
GRANT SELECT ON SCHEMA cfo_banking_demo.bronze_market_data TO `account users`;
GRANT MODIFY ON SCHEMA cfo_banking_demo.bronze_market_data TO `account users`;

-- Grant schema-level permissions for ml_models (if exists)
GRANT USE SCHEMA ON SCHEMA cfo_banking_demo.ml_models TO `account users`;
GRANT SELECT ON SCHEMA cfo_banking_demo.ml_models TO `account users`;
GRANT MODIFY ON SCHEMA cfo_banking_demo.ml_models TO `account users`;

-- Grant schema-level permissions for models (if exists)
GRANT USE SCHEMA ON SCHEMA cfo_banking_demo.models TO `account users`;
GRANT SELECT ON SCHEMA cfo_banking_demo.models TO `account users`;
GRANT MODIFY ON SCHEMA cfo_banking_demo.models TO `account users`;

-- Verify grants
SHOW GRANTS ON CATALOG cfo_banking_demo;
