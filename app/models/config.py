"""Configuration models for Yaade."""

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import Optional


def _default_data_dir() -> Path:
    """Default data directory: ~/.yaade (central, not per-directory)."""
    return Path.home() / ".yaade"


class ServerConfig(BaseSettings):
    """Server configuration using environment variables."""
    
    # Storage configuration: central ~/.yaade by default (not per-directory .yaade)
    data_dir: Path = Field(
        default_factory=_default_data_dir,
        description="Base directory for data storage"
    )
    
    @field_validator("data_dir", mode="before")
    @classmethod
    def expand_data_dir(cls, v: object) -> Path:
        """Expand ~ and convert env string to Path."""
        if v is None:
            return _default_data_dir()
        p = Path(str(v)) if not isinstance(v, Path) else v
        return p.expanduser()
    
    # Embedding configuration
    embedding_model_name: str = Field(
        default="all-MiniLM-L6-v2",
        description="Sentence transformer model name"
    )
    embedding_batch_size: int = Field(
        default=32,
        description="Batch size for embedding generation"
    )
    embedding_max_seq_length: int = Field(
        default=512,
        description="Maximum sequence length for embeddings"
    )
    host: str = Field(
        default="localhost",
        description="Server host"
    )
    port: int = Field(
        default=8000,
        description="Server port"
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    
    @property
    def chroma_path(self) -> Path:
        """Get the ChromaDB storage path."""
        return self.data_dir / "chroma"
    
    @property
    def sqlite_path(self) -> Path:
        """Get the SQLite database path."""
        return self.data_dir / "metadata.db"

    model_config = SettingsConfigDict(
        env_prefix="YAADE_",
        env_file=".env",
        extra="ignore"
    )