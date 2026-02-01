"""Unit tests for VectorStore."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from app.storage.vector_store import VectorStore
from app.models.memory import Memory, MemoryType, MemorySource


class TestVectorStore:
    """Tests for VectorStore class."""

    @pytest.fixture
    def mock_chroma_client(self):
        """Create a mock ChromaDB client."""
        mock_collection = MagicMock()
        mock_collection.add = MagicMock()
        mock_collection.query = MagicMock(return_value={
            "ids": [["id1", "id2"]],
            "documents": [["content1", "content2"]],
            "metadatas": [[{"tags": "test"}, {"tags": "sample"}]],
            "distances": [[0.1, 0.2]],
            "embeddings": [[[0.1] * 384, [0.2] * 384]]
        })
        mock_collection.get = MagicMock(return_value={
            "ids": ["test-id"],
            "documents": ["Test content"],
            "metadatas": [{"tags": "test", "importance": 5.0}],
            "embeddings": [[0.1] * 384]
        })
        mock_collection.delete = MagicMock()
        mock_collection.count = MagicMock(return_value=10)

        mock_client = MagicMock()
        mock_client.get_or_create_collection = MagicMock(return_value=mock_collection)
        
        return mock_client, mock_collection

    @pytest.fixture
    def vector_store(self, mock_chroma_client, temp_dir):
        """Create a VectorStore with mocked ChromaDB."""
        mock_client, _ = mock_chroma_client
        with patch('app.storage.vector_store.chromadb.PersistentClient', return_value=mock_client):
            store = VectorStore(str(temp_dir))
            return store

    def test_vector_store_initialization(self, mock_chroma_client, temp_dir):
        """Test VectorStore initialization."""
        mock_client, _ = mock_chroma_client
        with patch('app.storage.vector_store.chromadb.PersistentClient', return_value=mock_client):
            store = VectorStore(str(temp_dir))
            
            assert store.persist_directory == str(temp_dir)
            assert store.client is not None
            assert store.collection is not None
            mock_client.get_or_create_collection.assert_called_once_with(
                name="memories",
                metadata={"description": "Memory embeddings"}
            )

    @pytest.mark.asyncio
    async def test_add_memory_success(self, vector_store, mock_chroma_client, sample_memory):
        """Test adding a memory with embedding."""
        _, mock_collection = mock_chroma_client
        vector_store.collection = mock_collection
        
        await vector_store.add_memory(sample_memory)
        
        mock_collection.add.assert_called_once()
        call_kwargs = mock_collection.add.call_args[1]
        assert call_kwargs["ids"] == [sample_memory.id]
        assert call_kwargs["embeddings"] == [sample_memory.embedding]
        assert call_kwargs["documents"] == [sample_memory.content]

    @pytest.mark.asyncio
    async def test_add_memory_without_embedding_raises(self, vector_store, sample_memory_without_embedding):
        """Test that adding memory without embedding raises ValueError."""
        with pytest.raises(ValueError, match="Memory must have embedding"):
            await vector_store.add_memory(sample_memory_without_embedding)

    @pytest.mark.asyncio
    async def test_add_memory_metadata_formatting(self, vector_store, mock_chroma_client, sample_memory):
        """Test that memory metadata is correctly formatted."""
        _, mock_collection = mock_chroma_client
        vector_store.collection = mock_collection
        
        await vector_store.add_memory(sample_memory)
        
        call_kwargs = mock_collection.add.call_args[1]
        metadata = call_kwargs["metadatas"][0]
        
        assert metadata["type"] == "text"
        assert metadata["source"] == "api"
        assert metadata["tags"] == "test,ml"
        assert metadata["importance"] == 5.0
        assert "created_at" in metadata

    @pytest.mark.asyncio
    async def test_search_similar(self, vector_store, mock_chroma_client):
        """Test searching for similar memories."""
        _, mock_collection = mock_chroma_client
        vector_store.collection = mock_collection
        
        query_embedding = [0.1] * 384
        results = await vector_store.search_similar(query_embedding, n_results=5)
        
        mock_collection.query.assert_called_once_with(
            query_embeddings=[query_embedding],
            n_results=5,
            where=None
        )
        assert "ids" in results
        assert "documents" in results
        assert "metadatas" in results

    @pytest.mark.asyncio
    async def test_search_similar_with_filter(self, vector_store, mock_chroma_client):
        """Test searching with metadata filter."""
        _, mock_collection = mock_chroma_client
        vector_store.collection = mock_collection
        
        query_embedding = [0.1] * 384
        filter_metadata = {"type": "text"}
        
        await vector_store.search_similar(
            query_embedding,
            n_results=10,
            filter_metadata=filter_metadata
        )
        
        mock_collection.query.assert_called_once_with(
            query_embeddings=[query_embedding],
            n_results=10,
            where=filter_metadata
        )

    @pytest.mark.asyncio
    async def test_get_memory_by_id_found(self, vector_store, mock_chroma_client):
        """Test retrieving an existing memory by ID."""
        _, mock_collection = mock_chroma_client
        vector_store.collection = mock_collection
        
        result = await vector_store.get_memory_by_id("test-id")
        
        mock_collection.get.assert_called_once_with(
            ids=["test-id"],
            include=["metadatas", "documents", "embeddings"]
        )
        assert result is not None
        assert result["id"] == "test-id"
        assert result["content"] == "Test content"

    @pytest.mark.asyncio
    async def test_get_memory_by_id_not_found(self, vector_store, mock_chroma_client):
        """Test retrieving a non-existent memory."""
        _, mock_collection = mock_chroma_client
        mock_collection.get.return_value = {
            "ids": [],
            "documents": [],
            "metadatas": [],
            "embeddings": []
        }
        vector_store.collection = mock_collection
        
        result = await vector_store.get_memory_by_id("nonexistent-id")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_memory_by_id_error_handling(self, vector_store, mock_chroma_client):
        """Test error handling when retrieving memory."""
        _, mock_collection = mock_chroma_client
        mock_collection.get.side_effect = Exception("Database error")
        vector_store.collection = mock_collection
        
        result = await vector_store.get_memory_by_id("test-id")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_memory_success(self, vector_store, mock_chroma_client):
        """Test deleting a memory."""
        _, mock_collection = mock_chroma_client
        vector_store.collection = mock_collection
        
        result = await vector_store.delete_memory("test-id")
        
        mock_collection.delete.assert_called_once_with(ids=["test-id"])
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_memory_error(self, vector_store, mock_chroma_client):
        """Test error handling when deleting memory."""
        _, mock_collection = mock_chroma_client
        mock_collection.delete.side_effect = Exception("Delete error")
        vector_store.collection = mock_collection
        
        result = await vector_store.delete_memory("test-id")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_count_memories(self, vector_store, mock_chroma_client):
        """Test counting memories."""
        _, mock_collection = mock_chroma_client
        vector_store.collection = mock_collection
        
        count = await vector_store.count_memories()
        
        mock_collection.count.assert_called_once()
        assert count == 10

    @pytest.mark.asyncio
    async def test_count_memories_error(self, vector_store, mock_chroma_client):
        """Test error handling when counting memories."""
        _, mock_collection = mock_chroma_client
        mock_collection.count.side_effect = Exception("Count error")
        vector_store.collection = mock_collection
        
        count = await vector_store.count_memories()
        
        assert count == 0

    @pytest.mark.asyncio
    async def test_get_all_memories(self, vector_store, mock_chroma_client):
        """Test getting all memories."""
        _, mock_collection = mock_chroma_client
        mock_collection.get.return_value = {
            "ids": ["id1", "id2", "id3"],
            "documents": ["doc1", "doc2", "doc3"],
            "metadatas": [{"a": 1}, {"b": 2}, {"c": 3}]
        }
        vector_store.collection = mock_collection
        
        result = await vector_store.get_all_memories()
        
        mock_collection.get.assert_called_with(
            limit=None,
            include=["metadatas", "documents"]
        )
        assert len(result["ids"]) == 3

    @pytest.mark.asyncio
    async def test_get_all_memories_with_limit(self, vector_store, mock_chroma_client):
        """Test getting all memories with limit."""
        _, mock_collection = mock_chroma_client
        vector_store.collection = mock_collection
        
        await vector_store.get_all_memories(limit=5)
        
        mock_collection.get.assert_called_with(
            limit=5,
            include=["metadatas", "documents"]
        )

    @pytest.mark.asyncio
    async def test_get_all_memories_error(self, vector_store, mock_chroma_client):
        """Test error handling when getting all memories."""
        _, mock_collection = mock_chroma_client
        mock_collection.get.side_effect = Exception("Get error")
        vector_store.collection = mock_collection
        
        result = await vector_store.get_all_memories()
        
        assert result == {"ids": [], "documents": [], "metadatas": []}

    @pytest.mark.asyncio
    async def test_update_memory(self, vector_store, mock_chroma_client):
        """Test updating a memory."""
        _, mock_collection = mock_chroma_client
        vector_store.collection = mock_collection
        
        result = await vector_store.update_memory("test-id", {"content": "updated"})
        
        # Current implementation is simplified and always returns True
        assert result is True
