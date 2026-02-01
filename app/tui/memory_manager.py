"""Memory manager service for TUI operations."""

import uuid
from typing import List, Dict, Any, Optional, cast
from datetime import datetime

from ..models.config import ServerConfig
from ..models.memory import Memory, MemoryType, MemorySource
from ..storage.vector_store import VectorStore
from ..search.embeddings import EmbeddingService


class MemoryManager:
    """Manages memory operations for the TUI using synchronous calls."""

    def __init__(self):
        """Initialize the memory manager with services."""
        self.config = ServerConfig()

        # Ensure data directory exists
        self.config.data_dir.mkdir(parents=True, exist_ok=True)

        # Initialize services
        self.embedding_service = EmbeddingService(self.config.embedding_model_name)
        self.vector_store = VectorStore(str(self.config.chroma_path))

    def list_all_memories_sync(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List all memories (synchronous).

        Args:
            limit: Maximum number of memories to return

        Returns:
            List of memory dictionaries sorted by creation date (newest first)
        """
        try:
            # Get more than limit to allow for sorting, then trim
            fetch_limit = min(limit * 2, 1000)
            results = self.vector_store.collection.get(
                limit=fetch_limit,
                include=["metadatas", "documents"]
            )

            formatted_results = []
            if results.get("ids"):
                documents = results.get("documents") or []
                metadatas = results.get("metadatas") or []
                for i, memory_id in enumerate(results["ids"]):
                    formatted_results.append({
                        "memory_id": memory_id,
                        "content": documents[i] if i < len(documents) else "",
                        "metadata": metadatas[i] if i < len(metadatas) else {}
                    })

            # Sort by created_at (newest first)
            def get_created_at(memory: Dict[str, Any]) -> str:
                return memory.get("metadata", {}).get("created_at", "")

            formatted_results.sort(key=get_created_at, reverse=True)

            # Return only the requested limit
            return formatted_results[:limit]
        except Exception:
            return []

    async def list_all_memories(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List all memories (async wrapper)."""
        return self.list_all_memories_sync(limit)

    def add_memory_sync(
        self,
        content: str,
        memory_type: str = "text",
        source: str = "manual",
        tags: Optional[List[str]] = None,
        importance: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Add a new memory (synchronous).

        Args:
            content: The memory content to store
            memory_type: Type of memory (text, image, document, conversation, code)
            source: Source of the memory
            tags: Optional list of tags for categorization
            importance: Importance score from 0.0 to 10.0
            metadata: Optional additional metadata

        Returns:
            Dictionary with memory_id, status, and timestamp
        """
        # Validate and convert enum values
        try:
            memory_type_enum = MemoryType(memory_type.lower())
        except ValueError:
            memory_type_enum = MemoryType.TEXT

        try:
            source_enum = MemorySource(source.lower())
        except ValueError:
            source_enum = MemorySource.MANUAL

        # Set defaults
        if tags is None:
            tags = []
        if metadata is None:
            metadata = {}

        # Generate embedding using synchronous method
        try:
            embedding = cast(List[float], self.embedding_service._encode_sync(content))
        except Exception as e:
            return {
                "error": f"Failed to generate embedding: {str(e)}",
                "status": "failed"
            }

        # Create memory object
        memory = Memory(
            id=str(uuid.uuid4()),
            content=content,
            type=memory_type_enum,
            source=source_enum,
            tags=tags,
            importance=importance,
            metadata=metadata,
            embedding=embedding,
            updated_at=None
        )

        # Store in vector database
        try:
            chroma_metadata = {
                "type": memory.type.value,
                "source": memory.source.value,
                "tags": ",".join(memory.tags),
                "importance": memory.importance,
                "created_at": memory.created_at.isoformat()
            }
            chroma_metadata.update(memory.metadata)
            
            self.vector_store.collection.add(
                ids=[memory.id],
                embeddings=[memory.embedding],
                metadatas=[chroma_metadata],
                documents=[memory.content]
            )
        except Exception as e:
            return {
                "error": f"Failed to store memory: {str(e)}",
                "status": "failed"
            }

        return {
            "memory_id": memory.id,
            "status": "added",
            "timestamp": memory.created_at.isoformat()
        }

    def generate_embedding_sync(self, content: str) -> List[float]:
        """Generate embedding for content (synchronous).

        This should be called on the main thread to avoid file descriptor issues
        with PyTorch when used in TUI worker threads.

        Args:
            content: The text content to generate embedding for

        Returns:
            Embedding vector as list of floats

        Raises:
            Exception: If embedding generation fails
        """
        return cast(List[float], self.embedding_service._encode_sync(content))

    def store_memory_with_embedding_sync(
        self,
        content: str,
        embedding: List[float],
        memory_type: str = "text",
        source: str = "manual",
        tags: Optional[List[str]] = None,
        importance: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Store a memory with a pre-computed embedding (synchronous).

        This is safe to call from worker threads since it doesn't use PyTorch.

        Args:
            content: The memory content to store
            embedding: Pre-computed embedding vector
            memory_type: Type of memory
            source: Source of the memory
            tags: Optional list of tags
            importance: Importance score
            metadata: Optional additional metadata

        Returns:
            Dictionary with memory_id, status, and timestamp
        """
        # Validate and convert enum values
        try:
            memory_type_enum = MemoryType(memory_type.lower())
        except ValueError:
            memory_type_enum = MemoryType.TEXT

        try:
            source_enum = MemorySource(source.lower())
        except ValueError:
            source_enum = MemorySource.MANUAL

        # Set defaults
        if tags is None:
            tags = []
        if metadata is None:
            metadata = {}

        # Create memory object
        memory = Memory(
            id=str(uuid.uuid4()),
            content=content,
            type=memory_type_enum,
            source=source_enum,
            tags=tags,
            importance=importance,
            metadata=metadata,
            embedding=embedding,
            updated_at=None
        )

        # Store in vector database
        try:
            chroma_metadata = {
                "type": memory.type.value,
                "source": memory.source.value,
                "tags": ",".join(memory.tags),
                "importance": memory.importance,
                "created_at": memory.created_at.isoformat()
            }
            chroma_metadata.update(memory.metadata)

            self.vector_store.collection.add(
                ids=[memory.id],
                embeddings=[memory.embedding],
                metadatas=[chroma_metadata],
                documents=[memory.content]
            )
        except Exception as e:
            return {
                "error": f"Failed to store memory: {str(e)}",
                "status": "failed"
            }

        return {
            "memory_id": memory.id,
            "status": "added",
            "timestamp": memory.created_at.isoformat()
        }

    async def add_memory(
        self,
        content: str,
        memory_type: str = "text",
        source: str = "manual",
        tags: Optional[List[str]] = None,
        importance: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Add a new memory (async wrapper)."""
        return self.add_memory_sync(content, memory_type, source, tags, importance, metadata)

    def get_memory_sync(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific memory by ID (synchronous)."""
        try:
            results = self.vector_store.collection.get(
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
                "content": documents[0] if documents is not None and len(documents) > 0 else None,
                "metadata": metadatas[0] if metadatas is not None and len(metadatas) > 0 else None,
                "embedding": embeddings[0] if embeddings is not None and len(embeddings) > 0 else None
            }
        except Exception:
            return None

    async def get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific memory by ID (async wrapper)."""
        return self.get_memory_sync(memory_id)

    def delete_memory_sync(self, memory_id: str) -> Dict[str, Any]:
        """Delete a memory (synchronous)."""
        try:
            self.vector_store.collection.delete(ids=[memory_id])
            return {
                "memory_id": memory_id,
                "status": "deleted",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "memory_id": memory_id,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def delete_memory(self, memory_id: str) -> Dict[str, Any]:
        """Delete a memory (async wrapper)."""
        return self.delete_memory_sync(memory_id)

    def update_memory_sync(
        self,
        memory_id: str,
        content: str,
        memory_type: str = "text",
        source: str = "manual",
        tags: Optional[List[str]] = None,
        importance: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Update an existing memory (synchronous)."""
        # Delete old memory
        delete_result = self.delete_memory_sync(memory_id)
        if delete_result.get("status") != "deleted":
            return {
                "error": "Failed to delete old memory",
                "status": "failed"
            }

        # Add new memory
        return self.add_memory_sync(
            content=content,
            memory_type=memory_type,
            source=source,
            tags=tags,
            importance=importance,
            metadata=metadata
        )

    def update_memory_with_embedding_sync(
        self,
        memory_id: str,
        content: str,
        embedding: List[float],
        memory_type: str = "text",
        source: str = "manual",
        tags: Optional[List[str]] = None,
        importance: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Update an existing memory with a pre-computed embedding (synchronous).

        This is safe to call from worker threads since it doesn't use PyTorch.
        """
        # Delete old memory
        delete_result = self.delete_memory_sync(memory_id)
        if delete_result.get("status") != "deleted":
            return {
                "error": "Failed to delete old memory",
                "status": "failed"
            }

        # Add new memory with pre-computed embedding
        return self.store_memory_with_embedding_sync(
            content=content,
            embedding=embedding,
            memory_type=memory_type,
            source=source,
            tags=tags,
            importance=importance,
            metadata=metadata
        )

    async def update_memory(
        self,
        memory_id: str,
        content: str,
        memory_type: str = "text",
        source: str = "manual",
        tags: Optional[List[str]] = None,
        importance: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Update an existing memory (async wrapper)."""
        return self.update_memory_sync(memory_id, content, memory_type, source, tags, importance, metadata)

    async def search_memories(
        self,
        query: str,
        limit: int = 10,
        filter_tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Search disabled - returns empty list."""
        return []

    def get_stats_sync(self) -> Dict[str, Any]:
        """Get memory statistics (synchronous)."""
        try:
            total_memories = self.vector_store.collection.count()
            storage_bytes, storage_size = self._calculate_storage_size_sync()
            return {
                "total_memories": total_memories,
                "embedding_model": self.config.embedding_model_name,
                "data_directory": str(self.config.data_dir),
                "storage_location": str(self.config.data_dir.absolute()),
                "storage_size": storage_size,
                "storage_bytes": storage_bytes
            }
        except Exception as e:
            return {
                "total_memories": 0,
                "error": str(e)
            }

    async def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics (async wrapper)."""
        return self.get_stats_sync()

    def _calculate_storage_size_sync(self) -> tuple[int, str]:
        """Calculate total size of data directory (synchronous)."""
        try:
            total_size = 0
            for file_path in self.config.data_dir.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size

            size_bytes = total_size
            size = float(total_size)
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if size < 1024.0:
                    return size_bytes, f"{size:.1f} {unit}"
                size /= 1024.0
            return size_bytes, f"{size:.1f} PB"
        except Exception:
            return 0, "0 B"

    async def calculate_storage_size(self) -> tuple[int, str]:
        """Calculate total size of data directory (async wrapper)."""
        return self._calculate_storage_size_sync()
