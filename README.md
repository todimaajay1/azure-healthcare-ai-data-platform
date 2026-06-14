# Azure Healthcare AI Data Platform

End-to-end healthcare data platform built on Azure and Databricks, implementing medallion architecture with Unity Catalog governance, HIPAA-compliant data handling, and RAG-based AI retrieval for clinical decision support.

## Architecture
[HL7 FHIR APIs / EHR Systems / Medical IoT]
                 ↓
    [Azure Event Hubs / IoT Hub]
                 ↓
     [Databricks Auto Loader]
                 ↓
   [Bronze: Raw Clinical Events]
                 ↓
[Delta Live Tables: Quality Checks]
                 ↓
[Silver: Validated Patient Data]
                 ↓
 [dbt + PySpark: Gold Aggregates]
                 ↓
[Unity Catalog: RLS + PII Masking]
                 ↓
[Azure AI Search: RAG Vector Index]
                 ↓
[Power BI / ML Models / Reverse ETL]


## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Ingestion** | Azure Event Hubs, IoT Hub, FHIR APIs | Real-time + batch clinical data |
| **Compute** | Databricks (DBR 13.3 LTS+) | Unified analytics & ML |
| **Storage** | Delta Lake on ADLS Gen2 | ACID transactions, time travel |
| **Governance** | Unity Catalog | Fine-grained access, HIPAA audit |
| **Transform** | dbt + PySpark | Gold layer business models |
| **AI Retrieval** | Azure AI Search | RAG for clinical AI assistants |
| **Reverse ETL** | Azure Data Factory + SQL | Sync to operational EHR |
| **IaC** | Terraform | Reproducible infrastructure |
| **CI/CD** | Azure DevOps | Automated testing & deployment |
| **Quality** | Great Expectations + DLT | Data validation & anomaly detection |

## Key Features

### 🔒 HIPAA Compliance & Governance
- **Encryption**: ADLS encryption at rest, TLS 1.3 in transit
- **PII Masking**: Dynamic masking via Unity Catalog functions
- **Row-Level Security**: Patient data access restricted by provider ID
- **Audit Logging**: Complete data lineage and access tracking
- **Data Retention**: Automated lifecycle policies per HIPAA requirements

### 🤖 AI & RAG Integration
- **Vector Indexing**: Clinical notes and research papers indexed into Azure AI Search
- **RAG Retrieval**: Semantic search for AI-powered clinical decision support
- **ML Feature Store**: Patient features for readmission prediction models
- **Model Monitoring**: MLflow tracking for model drift and performance

### 🔄 Reverse ETL
- **Operational Sync**: Gold layer patient risk scores synced back to EHR via Azure Data Factory
- **Real-Time Alerts**: Critical lab values trigger immediate provider notifications
- **CRM Integration**: Patient engagement data synced to Salesforce

## Project Structure
azure-healthcare-ai-data-platform/
├── infrastructure/
│   ├── terraform/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── unity_catalog.tf
│   └── azure-devops/
│       └── pipeline.yml
├── src/
│   ├── ingestion/
│   │   ├── fhir_api_client.py
│   │   ├── iot_hub_consumer.py
│   │   └── event_hubs_streaming.py
│   ├── dlt/
│   │   └── clinical_pipeline.py
│   ├── dbt/
│   │   ├── models/
│   │   │   ├── staging/
│   │   │   ├── silver/
│   │   │   └── gold/
│   │   └── tests/
│   ├── rag/
│   │   ├── vector_indexing.py
│   │   └── retrieval.py
│   ├── reverse_etl/
│   │   └── sync_to_ehr.py
│   └── governance/
│       └── unity_catalog_setup.sql
├── tests/
│   ├── test_data_quality.py
│   └── test_hipaa_compliance.py
├── docs/
│   ├── architecture.md
│   ├── data_contracts.md
│   └── hipaa_compliance.md
└── README.md

## Data Contracts

- **Bronze → Silver**: Schema enforced via Auto Loader; FHIR R4 validation; DLT expectations for null checks, timestamp ranges, and patient ID format
- **Silver → Gold**: Business rules for episode grouping, risk stratification, and outcome metrics
- **Gold → AI**: Vector embeddings generated for clinical notes; schema enforced for feature store
- **Gold → Ops**: Reverse ETL syncs with watermark tracking; SLA: < 5 minutes for critical alerts

## Quick Start

```bash
# 1. Deploy Azure infrastructure
cd infrastructure/terraform
terraform init && terraform apply

# 2. Start DLT pipeline
databricks jobs run --job-id clinical_ingestion_pipeline

# 3. Run dbt models
cd src/dbt
dbt run --target prod

# 4. Index for RAG
python src/rag/vector_indexing.py

# 5. Reverse ETL sync
python src/reverse_etl/sync_to_ehr.py

Compliance & Security
HIPAA: All PHI encrypted, access logged, minimum necessary principle enforced
SOC-2: Audit trails, change management, automated data quality gates
GDPR: Right to erasure implemented via Delta Lake time travel and vacuum operations

License
Built for enterprise healthcare analytics. Not for production clinical use without proper validation.

## Step 1C: Create `infrastructure/terraform/main.tf`
1. In the repo, click: **Add file** → **Create new file**
2. In the filename box, type EXACTLY: `infrastructure/terraform/main.tf`
3. **COPY the block below** and paste it in the file body
4. Commit message: `Add Terraform IaC`
5. Click: **Commit new file**

```hcl
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.75"
    }
    databricks = {
      source  = "databricks/databricks"
      version = "~> 1.28"
    }
  }
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}

provider "databricks" {
  host  = azurerm_databricks_workspace.healthcare.workspace_url
  token = var.databricks_token
}

# Resource Group
resource "azurerm_resource_group" "healthcare" {
  name     = "${var.project_name}-rg-${var.environment}"
  location = var.location
}

# Storage Account (ADLS Gen2)
resource "azurerm_storage_account" "healthcare" {
  name                     = "${var.project_name}sa${var.environment}"
  resource_group_name      = azurerm_resource_group.healthcare.name
  location                 = azurerm_resource_group.healthcare.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  is_hns_enabled           = true

  blob_properties {
    versioning_enabled = true
  }

  network_rules {
    default_action = "Deny"
    bypass         = ["AzureServices"]
  }
}

# Containers for Medallion Architecture
resource "azurerm_storage_container" "bronze" {
  name                  = "bronze"
  storage_account_name  = azurerm_storage_account.healthcare.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "silver" {
  name                  = "silver"
  storage_account_name  = azurerm_storage_account.healthcare.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "gold" {
  name                  = "gold"
  storage_account_name  = azurerm_storage_account.healthcare.name
  container_access_type = "private"
}

# Databricks Workspace
resource "azurerm_databricks_workspace" "healthcare" {
  name                = "${var.project_name}-dbw-${var.environment}"
  resource_group_name = azurerm_resource_group.healthcare.name
  location            = azurerm_resource_group.healthcare.location
  sku                 = "premium"
}

# Azure Event Hubs Namespace
resource "azurerm_eventhub_namespace" "healthcare" {
  name                = "${var.project_name}-ehns-${var.environment}"
  location            = azurerm_resource_group.healthcare.location
  resource_group_name = azurerm_resource_group.healthcare.name
  sku                 = "Standard"
  capacity            = 1
}

# Event Hub for Clinical Data
resource "azurerm_eventhub" "clinical_data" {
  name                = "clinical-events"
  namespace_name      = azurerm_eventhub_namespace.healthcare.name
  resource_group_name = azurerm_resource_group.healthcare.name
  partition_count     = 4
  message_retention   = 7
}

# Azure AI Search
resource "azurerm_search_service" "healthcare" {
  name                = "${var.project_name}-search-${var.environment}"
  resource_group_name = azurerm_resource_group.healthcare.name
  location            = azurerm_resource_group.healthcare.location
  sku                 = "standard"
}

# Variables
variable "subscription_id" { type = string }
variable "databricks_token" { type = string sensitive = true }
variable "project_name" { default = "healthcareai" }
variable "environment" { default = "prod" }
variable "location" { default = "East US" }

