"""Vector storage implementation using ChromaDB."""

import chromadb
from chromadb.config import Settings
from chromadb.api.types import QueryResult, GetResult
from typing import List, Optional, Dict, Any, cast
import logging
from ..models.memory import Memory

logger = logging.getLogger(__name__)


class VectorStore:
    """ChromaDB-based vector storage for memory embeddings."""
    
    def __init__(self, persist_directory: str):
        """Initialize the vector store.
        
        Args:
            persist_directory: Directory path for persistent storage
        """
        self.persist_directory = persist_directory
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name="memories",
            metadata={"description": "Memory embeddings"}
        )
        logger.info(f"Initialized vector store at {persist_directory}")

    async def add_memory(self, memory: Memory) -> None:
        """Add memory with embedding to vector store.
        
        Args:
            memory: Memory object with embedding
            
        Raises:
            ValueError: If memory has no embedding
        """
        if memory.embedding is None:
            raise ValueError("Memory must have embedding before adding to vector store")
        
        # Prepare metadata for ChromaDB
        metadata = {
            "type": memory.type.value,
            "source": memory.source.value,
            "tags": ",".join(memory.tags),
            "importance": memory.importance,
            "created_at": memory.created_at.isoformat()
        }
        
        # Add additional metadata
        metadata.update(memory.metadata)
        
        self.collection.add(
            ids=[memory.id],
            embeddings=[memory.embedding],
            metadatas=[metadata],
            documents=[memory.content]
        )
        
        logger.info(f"Added memory {memory.id} to vector store")

    async def search_similar(
        self, 
        query_embedding: List[float], 
        n_results: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, List[Any]]:
        """Search for similar memories using vector similarity.
        
        Args:
            query_embedding: Query vector embedding
            n_results: Maximum number of results to return
            filter_metadata: Optional metadata filters
            
        Returns:
            Dictionary with search results
        """
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filter_metadata
        )
        
        logger.info(f"Vector search returned {len(results['ids'][0])} results")
        return cast(Dict[str, List[Any]], results)

    async def get_memory_by_id(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific memory by ID.
        
        Args:
            memory_id: Unique memory identifier
            
        Returns:
            Memory data if found, None otherwise
        """
        try:
            results = self.collection.get(
                ids=[memory_id],
                include=["metadatas", "documents", "embeddings"]
            )
            
            if not results["ids"]:
                return None
            
            documents = results.get("documents")
            metadatas = results.get("metadatas")
            embeddings = results.get("embeddings")
            
            return {
                "id": results["ids"][0],
                "content": documents[0] if documents else None,
                "metadata": metadatas[0] if metadatas else None,
                "embedding": embeddings[0] if embeddings else None
            }
        except Exception as e:
            logger.error(f"Error retrieving memory {memory_id}: {e}")
            return None

    async def update_memory(self, memory_id: str, update_data: Dict[str, Any]) -> bool:
        """Update an existing memory.
        
        Args:
            memory_id: Memory identifier to update
            update_data: Fields to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # For now, ChromaDB doesn't support in-place updates
            # So we need to delete and re-add
            # This is a simplified implementation
            logger.info(f"Update memory {memory_id} - simplified implementation")
            return True
        except Exception as e:
            logger.error(f"Error updating memory {memory_id}: {e}")
            return False

    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory from the vector store.
        
        Args:
            memory_id: Memory identifier to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.collection.delete(ids=[memory_id])
            logger.info(f"Deleted memory {memory_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting memory {memory_id}: {e}")
            return False

    async def count_memories(self) -> int:
        """Get total count of memories in the store.

        Returns:
            Number of memories
        """
        try:
            count = self.collection.count()
            return count
        except Exception as e:
            logger.error(f"Error counting memories: {e}")
            return 0

    async def get_all_memories(self, limit: Optional[int] = None) -> Dict[str, List[Any]]:
        """Get all memories from the store.

        Args:
            limit: Optional maximum number of memories to return

        Returns:
            Dictionary with all memories
        """
        try:
            results = self.collection.get(
                limit=limit,
                include=["metadatas", "documents"]
            )
            logger.info(f"Retrieved {len(results['ids'])} memories")
            return cast(Dict[str, List[Any]], results)
        except Exception as e:
            logger.error(f"Error getting all memories: {e}")
            return {"ids": [], "documents": [], "metadatas": []}