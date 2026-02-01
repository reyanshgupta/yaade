"""Shared pytest fixtures for Yaade tests."""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, MagicMock, AsyncMock
import uuid

from app.models.memory import Memory, MemoryType, MemorySource, MemoryCollection
from app.models.config import ServerConfig


@pytest.fixture
def sample_memory():
    """Create a sample Memory object for testing."""
    return Memory(
        id=str(uuid.uuid4()),
        content="This is a test memory about machine learning.",
        type=MemoryType.TEXT,
        source=MemorySource.API,
        tags=["test", "ml"],
        metadata={"category": "test"},
        importance=5.0,
        embedding=[0.1] * 384  # Simulated 384-dim embedding
    )


@pytest.fixture
def sample_memory_without_embedding():
    """Create a sample Memory object without embedding."""
    return Memory(
        id=str(uuid.uuid4()),
        content="Test memory without embedding",
        type=MemoryType.TEXT,
        source=MemorySource.MANUAL,
        tags=["test"],
        importance=3.0
    )


@pytest.fixture
def sample_memory_collection():
    """Create a sample MemoryCollection for testing."""
    return MemoryCollection(
        id=str(uuid.uuid4()),
        name="Test Collection",
        description="A test collection for unit tests",
        memories=["mem1", "mem2", "mem3"]
    )


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test data."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def temp_env_file(temp_dir):
    """Create a temporary .env file for testing."""
    env_path = temp_dir / ".env"
    env_path.write_text("EXISTING_VAR=existing_value\nANOTHER_VAR=another_value\n")
    yield env_path


@pytest.fixture
def mock_vector_store():
    """Create a mock VectorStore for testing."""
    store = AsyncMock()
    store.add_memory = AsyncMock()
    store.search_similar = AsyncMock(return_value={
        "ids": [["id1", "id2"]],
        "documents": [["content1", "content2"]],
        "metadatas": [[{"tags": "test"}, {"tags": "sample"}]],
        "distances": [[0.1, 0.2]],
        "embeddings": [[[0.1] * 384, [0.2] * 384]]
    })
    store.get_memory_by_id = AsyncMock(return_value={
        "id": "test-id",
        "content": "Test content",
        "metadata": {"tags": "test"},
        "embedding": [0.1] * 384
    })
    store.delete_memory = AsyncMock(return_value=True)
    store.count_memories = AsyncMock(return_value=10)
    store.get_all_memories = AsyncMock(return_value={
        "ids": ["id1", "id2"],
        "documents": ["content1", "content2"],
        "metadatas": [{"tags": "test"}, {"tags": "sample"}]
    })
    return store


@pytest.fixture
def mock_embedding_service():
    """Create a mock EmbeddingService for testing."""
    service = AsyncMock()
    service.encode_text = AsyncMock(return_value=[0.1] * 384)
    service.encode_query = AsyncMock(return_value=[0.1] * 384)
    service.get_embedding_dimension = Mock(return_value=384)
    return service


@pytest.fixture
def sample_memories_for_cleanup():
    """Create sample memories for cleanup testing."""
    base_embedding = [0.1] * 384
    similar_embedding = [0.1 + 0.001 * i for i in range(384)]  # Very similar
    
    return [
        {
            "id": "mem1",
            "content": "Test content about Python programming",
            "metadata": {"tags": "python,programming", "importance": 5.0, "created_at": "2024-01-01T00:00:00"},
            "embedding": base_embedding
        },
        {
            "id": "mem2",
            "content": "Test content about Python programming",  # Exact duplicate
            "metadata": {"tags": "python", "importance": 3.0, "created_at": "2024-01-02T00:00:00"},
            "embedding": base_embedding
        },
        {
            "id": "mem3",
            "content": "Test content about Python programming language",  # Near duplicate
            "metadata": {"tags": "python,lang", "importance": 7.0, "created_at": "2024-01-03T00:00:00"},
            "embedding": similar_embedding
        },
        {
            "id": "mem4",
            "content": "Different content about JavaScript",
            "metadata": {"tags": "javascript", "importance": 4.0, "created_at": "2024-01-04T00:00:00"},
            "embedding": [0.9] * 384  # Very different
        }
    ]
