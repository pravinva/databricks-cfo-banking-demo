-- Creates all schemas required by the backend API tables.
-- Update CATALOG_NAME if you want to target a different catalog.

USE CATALOG cfo_banking_demo;

CREATE SCHEMA IF NOT EXISTS bronze_core_banking;
CREATE SCHEMA IF NOT EXISTS silver_finance;
CREATE SCHEMA IF NOT EXISTS silver_treasury;
CREATE SCHEMA IF NOT EXISTS ml_models;
CREATE SCHEMA IF NOT EXISTS gold_finance;
