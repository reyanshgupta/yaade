"""Model downloading utilities for embedding models.

This module provides functions to download, cache-check, and manage
sentence transformer models used for embeddings.
"""

import os
from pathlib import Path
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


def get_cache_paths() -> tuple[Path, Path]:
    """Get the cache paths for sentence-transformers and HuggingFace.

    Returns:
        Tuple of (sentence_transformers_cache, huggingface_hub_cache)
    """
    # Sentence-transformers cache
    st_cache = os.environ.get(
        "SENTENCE_TRANSFORMERS_HOME",
        str(Path.home() / ".cache" / "torch" / "sentence_transformers")
    )

    # HuggingFace hub cache
    hf_home = os.environ.get("HF_HOME")
    if hf_home:
        hf_hub = Path(hf_home) / "hub"
    else:
        hf_hub = Path.home() / ".cache" / "huggingface" / "hub"

    return Path(st_cache), hf_hub


def is_model_cached(model_id: str) -> bool:
    """Check if a model is already downloaded and cached.

    Args:
        model_id: The model identifier (e.g., 'all-MiniLM-L6-v2')

    Returns:
        True if model is cached, False otherwise
    """
    st_cache, hf_hub = get_cache_paths()

    # Check sentence-transformers cache
    # Models can be stored as "sentence-transformers_<model>" or just "<model>"
    for prefix in ["sentence-transformers_", ""]:
        st_model_path = st_cache / f"{prefix}{model_id}"
        if st_model_path.exists() and (st_model_path / "config.json").exists():
            return True

    # Check HuggingFace hub cache
    # Models can be stored with different organization prefixes
    for org in ["sentence-transformers", "BAAI"]:
        hf_model_path = hf_hub / f"models--{org}--{model_id}"
        if hf_model_path.exists():
            snapshots = hf_model_path / "snapshots"
            if snapshots.exists() and any(snapshots.iterdir()):
                return True

    return False


def get_model_hub_path(model_id: str) -> str:
    """Get the correct HuggingFace hub path for a model.

    Args:
        model_id: The model identifier (e.g., 'all-MiniLM-L6-v2')

    Returns:
        Full model path with organization (e.g., 'BAAI/bge-small-en-v1.5')
    """
    # BGE models are from BAAI
    if model_id.startswith("bge-"):
        return f"BAAI/{model_id}"
    # Most other models are from sentence-transformers
    return f"sentence-transformers/{model_id}"


def download_model(model_id: str, force: bool = False) -> bool:
    """Download a specific embedding model.

    Args:
        model_id: The model identifier (e.g., 'all-MiniLM-L6-v2')
        force: If True, re-download even if cached

    Returns:
        True if successful, False otherwise
    """
    try:
        from app.models.embedding_models import get_model_by_id

        # Get model info for display
        model_info = get_model_by_id(model_id)
        if model_info:
            model_name = model_info["name"]
            size_mb = model_info["size_mb"]
        else:
            model_name = model_id
            size_mb = "unknown"

        # Check if already cached
        if not force and is_model_cached(model_id):
            print(f"Model '{model_id}' is already cached. Use --force to re-download.")
            return True

        print(f"Downloading {model_name} ({model_id})...")
        print(f"  Size: ~{size_mb} MB")
        print("  This may take a few minutes...")

        # Import and load the model - this triggers download
        from sentence_transformers import SentenceTransformer

        # Get the correct hub path based on model organization
        hub_path = get_model_hub_path(model_id)

        try:
            model = SentenceTransformer(hub_path)
        except Exception as e:
            # Fall back to just the model id
            logger.debug(f"Failed to load {hub_path}, trying {model_id}: {e}")
            model = SentenceTransformer(model_id)

        # Verify it loaded correctly
        dim = model.get_sentence_embedding_dimension()
        print(f"  Downloaded successfully! Dimensions: {dim}")

        return True

    except Exception as e:
        logger.error(f"Failed to download model {model_id}: {e}")
        print(f"Error downloading {model_id}: {e}")
        return False


def download_all_models(skip_cached: bool = True) -> bool:
    """Download all supported embedding models.

    Args:
        skip_cached: If True, skip models that are already cached

    Returns:
        True if all downloads succeeded, False otherwise
    """
    from app.models.embedding_models import EMBEDDING_MODELS

    success = True
    total = len(EMBEDDING_MODELS)

    print(f"Downloading {total} embedding models...\n")

    for i, model in enumerate(EMBEDDING_MODELS, 1):
        model_id = model["id"]
        print(f"[{i}/{total}] ", end="")

        if skip_cached and is_model_cached(model_id):
            print(f"Skipping {model_id} (already cached)")
            continue

        if not download_model(model_id, force=not skip_cached):
            success = False
        print()

    if success:
        print("\nAll models downloaded successfully!")
    else:
        print("\nSome models failed to download. Check the logs for details.")

    return success


def list_models() -> None:
    """List all available models with their cache status."""
    from app.models.embedding_models import EMBEDDING_MODELS

    print("\nAvailable Embedding Models:")
    print("=" * 70)
    print(f"{'Model ID':<30} {'Size':>8} {'Status':>12} {'Dims':>6}")
    print("-" * 70)

    for model in EMBEDDING_MODELS:
        model_id = model["id"]
        size = f"~{model['size_mb']}MB"
        dims = str(model["dimensions"])

        if is_model_cached(model_id):
            status = "\033[32m[cached]\033[0m"  # Green
        else:
            status = "\033[33m[not cached]\033[0m"  # Yellow

        # Print without ANSI codes for width calculation
        print(f"{model_id:<30} {size:>8} {status:>22} {dims:>6}")

    print("-" * 70)
    print("\nTo download a model: yaade download-model download <model_id>")
    print("To download all:      yaade download-model all")
    print()
