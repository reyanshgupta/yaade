"""Configuration models for Yaade."""

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings.sources import (
    JsonConfigSettingsSource,
    PydanticBaseSettingsSource,
)
from pathlib import Path
from typing import Optional, Type, Tuple


# Central config: ~/.yaade is always the config home; user's data path is stored there
YAADE_HOME = Path.home() / ".yaade"
CENTRAL_CONFIG_PATH = YAADE_HOME / "config.json"


def _default_data_dir() -> Path:
    """Default data directory: ~/.yaade (central, not per-directory)."""
    return Path.home() / ".yaade"


class ServerConfig(BaseSettings):
    """Server configuration: ~/.yaade/config.json first, then env vars, then defaults."""

    # Storage configuration: central ~/.yaade by default (not per-directory .yaade)
    data_dir: Path = Field(
        default_factory=_default_data_dir,
        description="Base directory for data storage"
    )

    @field_validator("data_dir", mode="before")
    @classmethod
    def expand_data_dir(cls, v: object) -> Path:
        """Expand ~, convert to Path, and resolve to absolute so storage never depends on cwd."""
        if v is None:
            return _default_data_dir()
        p = Path(str(v)) if not isinstance(v, Path) else v
        p = p.expanduser()
        # Resolve relative paths to absolute (e.g. .yaade or relative dirs) so
        # the server works when launched with a missing or sandboxed cwd.
        if not p.is_absolute():
            p = (Path.cwd() / p).resolve()
        return p

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

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        """Load config from ~/.yaade/config.json then env; env overrides file."""
        json_source = JsonConfigSettingsSource(settings_cls, json_file=CENTRAL_CONFIG_PATH)
        return (
            init_settings,
            json_source,
            env_settings,
            dotenv_settings,
            file_secret_settings,
        )

    model_config = SettingsConfigDict(
        env_prefix="YAADE_",
        env_file=".env",
        extra="ignore"
    )