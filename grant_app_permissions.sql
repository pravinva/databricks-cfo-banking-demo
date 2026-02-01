-- Grant permissions to Databricks App service principal
-- Service Principal: app-40zbx9 cfo-banking-demo (ID: 70728936211001)
-- App ID: 80ab33fd-2524-4b34-8557-d012d84e50ac

-- Grant warehouse usage permission
-- (This must be done via UI: Compute > SQL Warehouses > warehouse 4b9b953939869799 > Permissions)
-- Add service principal: app-40zbx9 cfo-banking-demo with "Can Use" permission

-- Grant catalog access
GRANT USE CATALOG ON CATALOG cfo_banking_demo TO `app-40zbx9 cfo-banking-demo`;

-- Grant schema access
GRANT USE SCHEMA ON SCHEMA cfo_banking_demo.silver_finance TO `app-40zbx9 cfo-banking-demo`;
GRANT USE SCHEMA ON SCHEMA cfo_banking_demo.silver_treasury TO `app-40zbx9 cfo-banking-demo`;
GRANT USE SCHEMA ON SCHEMA cfo_banking_demo.gold_regulatory TO `app-40zbx9 cfo-banking-demo`;
GRANT USE SCHEMA ON SCHEMA cfo_banking_demo.bronze_market_data TO `app-40zbx9 cfo-banking-demo`;

-- Grant SELECT on all tables in each schema
GRANT SELECT ON SCHEMA cfo_banking_demo.silver_finance TO `app-40zbx9 cfo-banking-demo`;
GRANT SELECT ON SCHEMA cfo_banking_demo.silver_treasury TO `app-40zbx9 cfo-banking-demo`;
GRANT SELECT ON SCHEMA cfo_banking_demo.gold_regulatory TO `app-40zbx9 cfo-banking-demo`;
GRANT SELECT ON SCHEMA cfo_banking_demo.bronze_market_data TO `app-40zbx9 cfo-banking-demo`;

-- Verify permissions
SHOW GRANTS ON CATALOG cfo_banking_demo;
SHOW GRANTS ON SCHEMA cfo_banking_demo.silver_finance;
SHOW GRANTS ON SCHEMA cfo_banking_demo.silver_treasury;
SHOW GRANTS ON SCHEMA cfo_banking_demo.gold_regulatory;
SHOW GRANTS ON SCHEMA cfo_banking_demo.bronze_market_data;
