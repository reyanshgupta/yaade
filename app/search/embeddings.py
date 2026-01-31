"""Embedding service using sentence-transformers."""

from sentence_transformers import SentenceTransformer
from typing import List, Union, Optional
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

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
        self.executor = ThreadPoolExecutor(max_workers=4)
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

    async def encode_text(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """Generate embeddings for text asynchronously.
        
        Args:
            text: Single text string or list of text strings
            
        Returns:
            Embedding vector(s) as list(s) of floats
        """
        model = self._ensure_model_loaded()
        
        loop = asyncio.get_event_loop()
        
        if isinstance(text, str):
            # Single text input
            embedding = await loop.run_in_executor(
                self.executor, 
                model.encode, 
                text
            )
            result = embedding.tolist()
            logger.debug(f"Generated embedding for text: {text[:50]}...")
            return result
        else:
            # Batch text input
            embeddings = await loop.run_in_executor(
                self.executor, 
                model.encode, 
                text
            )
            result = [emb.tolist() for emb in embeddings]
            logger.debug(f"Generated embeddings for {len(text)} texts")
            return result

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

    def __del__(self):
        """Cleanup executor when service is destroyed."""
        if hasattr(self, "executor"):
            self.executor.shutdown(wait=False)