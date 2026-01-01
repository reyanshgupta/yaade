"""Memory manager service for TUI operations."""

import uuid
import asyncio
from typing import List, Dict, Any, Optional, cast
from datetime import datetime

from ..models.config import ServerConfig
from ..models.memory import Memory, MemoryType, MemorySource
from ..storage.vector_store import VectorStore
from ..search.embeddings import EmbeddingService


class MemoryManager:
    """Manages memory operations for the TUI."""

    def __init__(self):
        """Initialize the memory manager with services."""
        self.config = ServerConfig()

        # Ensure data directory exists
        self.config.data_dir.mkdir(parents=True, exist_ok=True)

        # Initialize services
        self.embedding_service = EmbeddingService(self.config.embedding_model_name)
        self.vector_store = VectorStore(str(self.config.chroma_path))

    async def list_all_memories(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List all memories.

        Args:
            limit: Maximum number of memories to return

        Returns:
            List of memory dictionaries
        """
        try:
            # Get all memories directly from vector store
            results = await self.vector_store.get_all_memories(limit=limit)

            formatted_results = []
            if results.get("ids"):
                for i, memory_id in enumerate(results["ids"]):
                    formatted_results.append({
                        "memory_id": memory_id,
                        "content": results["documents"][i],
                        "metadata": results["metadatas"][i]
                    })

            return formatted_results
        except Exception:
            return []

    async def add_memory(
        self,
        content: str,
        memory_type: str = "text",
        source: str = "manual",
        tags: Optional[List[str]] = None,
        importance: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Add a new memory.

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

        # Generate embedding
        try:
            # encode_text returns List[float] for a single string input
            embedding = cast(List[float], await self.embedding_service.encode_text(content))
        except Exception:
            return {
                "error": "Failed to generate embedding",
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
            await self.vector_store.add_memory(memory)
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

    async def get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific memory by ID.

        Args:
            memory_id: Unique memory identifier

        Returns:
            Memory data if found, None otherwise
        """
        try:
            memory_data = await self.vector_store.get_memory_by_id(memory_id)
            return memory_data
        except Exception as e:
            return None

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
        """Update an existing memory.

        This is implemented as delete + add to update the embedding.

        Args:
            memory_id: Memory identifier to update
            content: The new memory content
            memory_type: Type of memory
            source: Source of the memory
            tags: Optional list of tags
            importance: Importance score from 0.0 to 10.0
            metadata: Optional additional metadata

        Returns:
            Dictionary with status information
        """
        # Delete old memory
        delete_result = await self.delete_memory(memory_id)
        if delete_result.get("status") != "deleted":
            return {
                "error": "Failed to delete old memory",
                "status": "failed"
            }

        # Add new memory
        return await self.add_memory(
            content=content,
            memory_type=memory_type,
            source=source,
            tags=tags,
            importance=importance,
            metadata=metadata
        )

    async def delete_memory(self, memory_id: str) -> Dict[str, Any]:
        """Delete a memory.

        Args:
            memory_id: Memory identifier to delete

        Returns:
            Status information
        """
        try:
            success = await self.vector_store.delete_memory(memory_id)
            if success:
                return {
                    "memory_id": memory_id,
                    "status": "deleted",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "memory_id": memory_id,
                    "status": "not_found",
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            return {
                "memory_id": memory_id,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def search_memories(
        self,
        query: str,
        limit: int = 10,
        filter_tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Search disabled - returns empty list."""
        return []

    async def calculate_storage_size(self) -> tuple[int, str]:
        """Calculate total size of data directory.

        Returns:
            Tuple of (size_in_bytes, human_readable_size)
        """
        try:
            total_size = 0
            for file_path in self.config.data_dir.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size

            # Convert to human-readable format
            size_bytes = total_size
            size = float(total_size)
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if size < 1024.0:
                    return size_bytes, f"{size:.1f} {unit}"
                size /= 1024.0
            return size_bytes, f"{size:.1f} PB"
        except Exception:
            return 0, "0 B"

    async def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics.

        Returns:
            Dictionary with memory statistics including storage info
        """
        try:
            total_memories = await self.vector_store.count_memories()
            storage_bytes, storage_size = await self.calculate_storage_size()
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
