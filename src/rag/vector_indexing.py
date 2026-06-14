"""
RAG vector indexing for clinical notes and research data.
Indexes Gold layer aggregated data into Azure AI Search for AI consumption.
"""
import pandas as pd
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex, SimpleField, SearchableField, VectorSearch, 
    HnswAlgorithmConfiguration, VectorSearchProfile
)

class ClinicalRAGIndexer:
    def __init__(self, endpoint: str, admin_key: str, index_name: str = "clinical-rag-index"):
        self.endpoint = endpoint
        self.admin_key = admin_key
        self.index_name = index_name
        self.index_client = SearchIndexClient(endpoint, AzureKeyCredential(admin_key))
        self.search_client = SearchClient(endpoint, index_name, AzureKeyCredential(admin_key))
    
    def create_index(self):
        """Create Azure AI Search index with vector search capability."""
        fields = [
            SimpleField(name="id", type="Edm.String", key=True),
            SearchableField(name="content", type="Edm.String", analyzer="en.microsoft"),
            SimpleField(name="patient_id", type="Edm.String", filterable=True),
            SimpleField(name="document_type", type="Edm.String", filterable=True, facetable=True),
            SimpleField(name="clinical_category", type="Edm.String", filterable=True, facetable=True),
            SimpleField(name="timestamp", type="Edm.DateTimeOffset", filterable=True, sortable=True),
            SimpleField(name="source_table", type="Edm.String", filterable=True),
        ]
        
        vector_search = VectorSearch(
            algorithms=[HnswAlgorithmConfiguration(name="hnsw-config")],
            profiles=[VectorSearchProfile(name="vector-profile", algorithm_configuration_name="hnsw-config")]
        )
        
        index = SearchIndex(
            name=self.index_name,
            fields=fields,
            vector_search=vector_search
        )
        
        self.index_client.create_or_update_index(index)
        print(f"Created/updated index: {self.index_name}")
    
    def index_clinical_notes(self, gold_data_path: str):
        """Index clinical notes from Gold layer Parquet files."""
        df = pd.read_parquet(gold_data_path)
        
        documents = []
        for idx, row in df.iterrows():
            doc = {
                "id": f"note_{idx}",
                "content": f"Patient {row.get('patient_id', 'unknown')}: Risk level {row.get('risk_stratification', 'unknown')}. "
                          f"Average observation value: {row.get('avg_observation_value', 'N/A')}. "
                          f"Age: {row.get('age', 'N/A')}, Gender: {row.get('gender', 'N/A')}",
                "patient_id": str(row.get("patient_id", "")),
                "document_type": "clinical_summary",
                "clinical_category": row.get("risk_stratification", "unknown"),
                "timestamp": row.get("last_observation_time", "2024-01-01T00:00:00Z"),
                "source_table": "gold_patient_risk_metrics"
            }
            documents.append(doc)
        
        for i in range(0, len(documents), 1000):
            batch = documents[i:i+1000]
            self.search_client.upload_documents(batch)
            print(f"Indexed batch {i//1000 + 1}: {len(batch)} documents")
        
        print(f"Total indexed: {len(documents)} clinical summaries")

if __name__ == "__main__":
    indexer = ClinicalRAGIndexer(
        endpoint="https://your-search-service.search.windows.net",
        admin_key="your-admin-key"
    )
    indexer.create_index()
    indexer.index_clinical_notes("data/gold/patient_risk_metrics.parquet")
