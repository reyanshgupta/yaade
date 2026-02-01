"""Embedding service using sentence-transformers."""

# Disable tokenizers parallelism to avoid file descriptor issues with TUI
import os
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import torch
# Disable torch parallelism to avoid file descriptor issues
torch.set_num_threads(1)
# Note: set_num_interop_threads must be called before any parallel work starts
# It may fail if torch has already started - that's OK, we just ignore it
try:
    torch.set_num_interop_threads(1)
except RuntimeError:
    pass  # Already set or parallel work has started

from sentence_transformers import SentenceTransformer
from typing import List, Union, Optional, Dict, Any
import asyncio
import logging

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings using sentence-transformers."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize the embedding service.
        
        Args:
            model_name: Name of the sentence transformer model to use
        """
        self.model_name = model_name
        self.model: Optional[SentenceTransformer] = None
        logger.info(f"Initializing embedding service with model: {model_name}")

    def _ensure_model_loaded(self) -> SentenceTransformer:
        """Ensure the model is loaded (lazy loading).
        
        Returns:
            The loaded SentenceTransformer model
        """
        if self.model is None:
            logger.info(f"Loading sentence transformer model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info("Model loaded successfully")
        return self.model

    def _encode_sync(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """Generate embeddings synchronously.

        Args:
            text: Single text string or list of text strings

        Returns:
            Embedding vector(s) as list(s) of floats
        """
        model = self._ensure_model_loaded()

        # Use show_progress_bar=False and convert_to_numpy=True to avoid
        # any UI or multiprocessing operations that conflict with Textual
        if isinstance(text, str):
            # Single text input
            embedding = model.encode(
                text,
                show_progress_bar=False,
                convert_to_numpy=True,
            )
            result = embedding.tolist()
            logger.debug(f"Generated embedding for text: {text[:50]}...")
            return result
        else:
            # Batch text input
            embeddings = model.encode(
                text,
                show_progress_bar=False,
                convert_to_numpy=True,
            )
            result = [emb.tolist() for emb in embeddings]
            logger.debug(f"Generated embeddings for {len(text)} texts")
            return result

    async def encode_text(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """Generate embeddings for text asynchronously.
        
        This runs the encoding synchronously but is async-compatible.
        For TUI applications, this avoids issues with ThreadPoolExecutor.
        
        Args:
            text: Single text string or list of text strings
            
        Returns:
            Embedding vector(s) as list(s) of floats
        """
        # Run synchronously - the model is fast enough for single texts
        # and this avoids issues with ThreadPoolExecutor in Textual
        return self._encode_sync(text)

    async def encode_query(self, query: str) -> List[float]:
        """Generate embedding for a search query.
        
        Args:
            query: Search query text
            
        Returns:
            Query embedding as list of floats
        """
        result = await self.encode_text(query)
        # Since we're passing a single string, we'll get a single embedding
        return result  # type: ignore[return-value]

    def get_embedding_dimension(self) -> int:
        """Get the dimensionality of the embeddings.
        
        Returns:
            Embedding vector dimension
        """
        model = self._ensure_model_loaded()
        dim = model.get_sentence_embedding_dimension()
        if dim is None:
            raise RuntimeError("Unable to determine embedding dimension")
        return dim

    @staticmethod
    def get_supported_model_info(model_name: str) -> Optional[Dict[str, Any]]:
        """Get model info from the predefined supported models list.
        
        This is a convenience method that imports from the TUI module.
        Returns None if the model is not in the predefined list (custom model).
        
        Args:
            model_name: The model identifier
            
        Returns:
            Model info dict or None if not in predefined list
        """
        try:
            from app.tui.screens.modals.embedding_model_select import get_model_by_id
            return get_model_by_id(model_name)
        except ImportError:
            return None