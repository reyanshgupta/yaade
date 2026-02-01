"""Embedding model definitions and configurations.

This module contains the curated list of supported embedding models
with their specifications. It's used by both the TUI and CLI tools.
"""

from typing import Optional, List, Dict, Any


# Curated list of embedding models with their specifications
EMBEDDING_MODELS: List[Dict[str, Any]] = [
    {
        "id": "all-MiniLM-L6-v2",
        "name": "MiniLM-L6-v2 (Default)",
        "dimensions": 384,
        "size_mb": 80,
        "ram_mb": 500,
        "speed": 3,      # 1-3 scale (3=fastest)
        "quality": 3,    # 1-5 scale
        "description": "Best balance of speed and quality for most use cases.",
        "recommended_for": "General use, limited hardware"
    },
    {
        "id": "all-MiniLM-L12-v2",
        "name": "MiniLM-L12-v2",
        "dimensions": 384,
        "size_mb": 120,
        "ram_mb": 600,
        "speed": 3,
        "quality": 4,
        "description": "Better quality than L6 with minimal speed impact.",
        "recommended_for": "Better accuracy with good performance"
    },
    {
        "id": "all-mpnet-base-v2",
        "name": "MPNet Base v2",
        "dimensions": 768,
        "size_mb": 420,
        "ram_mb": 1500,
        "speed": 1,
        "quality": 5,
        "description": "Highest quality semantic embeddings. Requires 4GB+ RAM.",
        "recommended_for": "Maximum accuracy, powerful hardware"
    },
    {
        "id": "paraphrase-MiniLM-L6-v2",
        "name": "Paraphrase MiniLM-L6",
        "dimensions": 384,
        "size_mb": 80,
        "ram_mb": 500,
        "speed": 3,
        "quality": 3,
        "description": "Optimized for detecting similar meanings and paraphrases.",
        "recommended_for": "Finding similar content"
    },
    {
        "id": "multi-qa-MiniLM-L6-cos-v1",
        "name": "Multi-QA MiniLM-L6",
        "dimensions": 384,
        "size_mb": 80,
        "ram_mb": 500,
        "speed": 3,
        "quality": 3,
        "description": "Specifically optimized for question-answering retrieval.",
        "recommended_for": "Q&A and information retrieval"
    },
    {
        "id": "bge-small-en-v1.5",
        "name": "BGE Small v1.5",
        "dimensions": 384,
        "size_mb": 130,
        "ram_mb": 600,
        "speed": 3,
        "quality": 4,
        "description": "BAAI's efficient model. Excellent quality-to-size ratio.",
        "recommended_for": "High quality with good efficiency"
    },
    {
        "id": "bge-base-en-v1.5",
        "name": "BGE Base v1.5",
        "dimensions": 768,
        "size_mb": 440,
        "ram_mb": 1500,
        "speed": 2,
        "quality": 5,
        "description": "Top-tier BAAI model. Among the best open-source embeddings.",
        "recommended_for": "Best-in-class accuracy"
    }
]


def get_model_by_id(model_id: str) -> Optional[Dict[str, Any]]:
    """Get model info by ID.
    
    Args:
        model_id: The model identifier
        
    Returns:
        Model info dict or None if not found
    """
    for model in EMBEDDING_MODELS:
        if model["id"] == model_id:
            return model
    return None


def get_model_dimensions(model_id: str) -> Optional[int]:
    """Get embedding dimensions for a model.
    
    Args:
        model_id: The model identifier
        
    Returns:
        Dimensions or None if model not found
    """
    model = get_model_by_id(model_id)
    return model["dimensions"] if model else None


def get_all_model_ids() -> List[str]:
    """Get list of all supported model IDs.
    
    Returns:
        List of model ID strings
    """
    return [model["id"] for model in EMBEDDING_MODELS]
