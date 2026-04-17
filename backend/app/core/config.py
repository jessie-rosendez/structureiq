from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    google_cloud_project: str = "structureiq"
    google_application_credentials: str = ""
    gcs_bucket_name: str = "structureiq-docs"
    vertex_location: str = "us-east1"   # Vector Search region
    gemini_location: str = "global"  # LLM generation endpoint
    gemini_model: str = "gemini-2.5-flash"
    gemini_fallback_model: str = "gemini-2.5-flash-lite"
    gemini_max_retries: int = 3

    vertex_standards_index_id: str = ""
    vertex_documents_index_id: str = ""
    vertex_standards_index_endpoint: str = ""
    vertex_documents_index_endpoint: str = ""
    vertex_standards_deployed_index_id: str = "standards_v2"
    vertex_documents_deployed_index_id: str = "documents_v2"

    google_api_key: str = ""
    langchain_api_key: str = ""
    langchain_tracing_v2: bool = True
    langchain_project: str = "structureiq"

    environment: str = "development"
    max_file_size_mb: int = 100
    chunk_size: int = 1000
    chunk_overlap: int = 200
    retrieval_top_k_docs: int = 5
    retrieval_top_k_standards: int = 3
    confidence_threshold: float = 0.75

    @property
    def standards_index_resource_name(self) -> str:
        return (
            f"projects/{self.google_cloud_project}"
            f"/locations/{self.vertex_location}"
            f"/indexes/{self.vertex_standards_index_id}"
        )

    @property
    def documents_index_resource_name(self) -> str:
        return (
            f"projects/{self.google_cloud_project}"
            f"/locations/{self.vertex_location}"
            f"/indexes/{self.vertex_documents_index_id}"
        )

    @property
    def standards_endpoint_resource_name(self) -> str:
        return (
            f"projects/{self.google_cloud_project}"
            f"/locations/{self.vertex_location}"
            f"/indexEndpoints/{self.vertex_standards_index_endpoint}"
        )

    @property
    def documents_endpoint_resource_name(self) -> str:
        return (
            f"projects/{self.google_cloud_project}"
            f"/locations/{self.vertex_location}"
            f"/indexEndpoints/{self.vertex_documents_index_endpoint}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
