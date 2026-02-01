"""Unit tests for Memory models."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from app.models.memory import Memory, MemoryType, MemorySource, MemoryCollection


class TestMemoryType:
    """Tests for MemoryType enum."""

    def test_memory_type_values(self):
        """Test all MemoryType enum values exist."""
        assert MemoryType.TEXT == "text"
        assert MemoryType.IMAGE == "image"
        assert MemoryType.DOCUMENT == "document"
        assert MemoryType.CONVERSATION == "conversation"
        assert MemoryType.CODE == "code"

    def test_memory_type_from_string(self):
        """Test creating MemoryType from string value."""
        assert MemoryType("text") == MemoryType.TEXT
        assert MemoryType("code") == MemoryType.CODE

    def test_memory_type_invalid_value(self):
        """Test that invalid MemoryType raises ValueError."""
        with pytest.raises(ValueError):
            MemoryType("invalid_type")


class TestMemorySource:
    """Tests for MemorySource enum."""

    def test_memory_source_values(self):
        """Test all MemorySource enum values exist."""
        assert MemorySource.CLAUDE == "claude"
        assert MemorySource.CHATGPT == "chatgpt"
        assert MemorySource.CURSOR == "cursor"
        assert MemorySource.BROWSER == "browser"
        assert MemorySource.API == "api"
        assert MemorySource.MANUAL == "manual"

    def test_memory_source_from_string(self):
        """Test creating MemorySource from string value."""
        assert MemorySource("claude") == MemorySource.CLAUDE
        assert MemorySource("api") == MemorySource.API

    def test_memory_source_invalid_value(self):
        """Test that invalid MemorySource raises ValueError."""
        with pytest.raises(ValueError):
            MemorySource("invalid_source")


class TestMemory:
    """Tests for Memory model."""

    def test_memory_creation_minimal(self):
        """Test creating Memory with minimal required fields."""
        memory = Memory(
            id="test-123",
            content="Test content",
            source=MemorySource.API
        )
        assert memory.id == "test-123"
        assert memory.content == "Test content"
        assert memory.source == MemorySource.API
        assert memory.type == MemoryType.TEXT  # Default
        assert memory.importance == 1.0  # Default
        assert memory.tags == []  # Default
        assert memory.metadata == {}  # Default
        assert memory.embedding is None  # Default
        assert memory.updated_at is None  # Default

    def test_memory_creation_full(self, sample_memory):
        """Test creating Memory with all fields."""
        assert sample_memory.id is not None
        assert sample_memory.content == "This is a test memory about machine learning."
        assert sample_memory.type == MemoryType.TEXT
        assert sample_memory.source == MemorySource.API
        assert sample_memory.tags == ["test", "ml"]
        assert sample_memory.metadata == {"category": "test"}
        assert sample_memory.importance == 5.0
        assert sample_memory.embedding is not None
        assert len(sample_memory.embedding) == 384

    def test_memory_importance_validation_lower_bound(self):
        """Test that importance must be >= 0.0."""
        with pytest.raises(ValidationError) as exc_info:
            Memory(
                id="test",
                content="Test",
                source=MemorySource.API,
                importance=-1.0
            )
        assert "greater than or equal to 0" in str(exc_info.value).lower()

    def test_memory_importance_validation_upper_bound(self):
        """Test that importance must be <= 10.0."""
        with pytest.raises(ValidationError) as exc_info:
            Memory(
                id="test",
                content="Test",
                source=MemorySource.API,
                importance=11.0
            )
        assert "less than or equal to 10" in str(exc_info.value).lower()

    def test_memory_importance_edge_cases(self):
        """Test importance at boundary values."""
        # Minimum value
        memory_min = Memory(
            id="test1",
            content="Test",
            source=MemorySource.API,
            importance=0.0
        )
        assert memory_min.importance == 0.0

        # Maximum value
        memory_max = Memory(
            id="test2",
            content="Test",
            source=MemorySource.API,
            importance=10.0
        )
        assert memory_max.importance == 10.0

    def test_memory_created_at_default(self):
        """Test that created_at is automatically set."""
        before = datetime.now()
        memory = Memory(
            id="test",
            content="Test",
            source=MemorySource.API
        )
        after = datetime.now()
        
        assert before <= memory.created_at <= after

    def test_memory_json_serialization(self, sample_memory):
        """Test Memory JSON serialization."""
        json_data = sample_memory.model_dump_json()
        assert isinstance(json_data, str)
        assert sample_memory.id in json_data
        assert sample_memory.content in json_data

    def test_memory_model_dump(self, sample_memory):
        """Test Memory model_dump."""
        data = sample_memory.model_dump()
        assert isinstance(data, dict)
        assert data["id"] == sample_memory.id
        assert data["content"] == sample_memory.content
        assert data["type"] == MemoryType.TEXT
        assert data["tags"] == ["test", "ml"]

    def test_memory_with_enum_string_conversion(self):
        """Test Memory accepts string values for enums."""
        memory = Memory(
            id="test",
            content="Test",
            type="code",  # String instead of MemoryType.CODE
            source="claude"  # String instead of MemorySource.CLAUDE
        )
        assert memory.type == MemoryType.CODE
        assert memory.source == MemorySource.CLAUDE

    def test_memory_empty_content(self):
        """Test Memory with empty content."""
        memory = Memory(
            id="test",
            content="",
            source=MemorySource.API
        )
        assert memory.content == ""

    def test_memory_long_content(self):
        """Test Memory with very long content."""
        long_content = "x" * 10000
        memory = Memory(
            id="test",
            content=long_content,
            source=MemorySource.API
        )
        assert len(memory.content) == 10000


class TestMemoryCollection:
    """Tests for MemoryCollection model."""

    def test_collection_creation_minimal(self):
        """Test creating MemoryCollection with minimal fields."""
        collection = MemoryCollection(
            id="col-123",
            name="Test Collection"
        )
        assert collection.id == "col-123"
        assert collection.name == "Test Collection"
        assert collection.description is None
        assert collection.memories == []

    def test_collection_creation_full(self, sample_memory_collection):
        """Test creating MemoryCollection with all fields."""
        assert sample_memory_collection.id is not None
        assert sample_memory_collection.name == "Test Collection"
        assert sample_memory_collection.description == "A test collection for unit tests"
        assert sample_memory_collection.memories == ["mem1", "mem2", "mem3"]

    def test_collection_created_at_default(self):
        """Test that created_at is automatically set."""
        before = datetime.now()
        collection = MemoryCollection(
            id="test",
            name="Test"
        )
        after = datetime.now()
        
        assert before <= collection.created_at <= after

    def test_collection_json_serialization(self, sample_memory_collection):
        """Test MemoryCollection JSON serialization."""
        json_data = sample_memory_collection.model_dump_json()
        assert isinstance(json_data, str)
        assert sample_memory_collection.name in json_data

    def test_collection_model_dump(self, sample_memory_collection):
        """Test MemoryCollection model_dump."""
        data = sample_memory_collection.model_dump()
        assert isinstance(data, dict)
        assert data["id"] == sample_memory_collection.id
        assert data["name"] == "Test Collection"
        assert data["memories"] == ["mem1", "mem2", "mem3"]

    def test_collection_empty_memories(self):
        """Test collection with no memories."""
        collection = MemoryCollection(
            id="test",
            name="Empty Collection",
            memories=[]
        )
        assert collection.memories == []

    def test_collection_add_memory_ids(self):
        """Test adding memory IDs to collection."""
        collection = MemoryCollection(
            id="test",
            name="Test"
        )
        # Simulate adding memories by creating new collection
        updated_memories = collection.memories + ["new-mem-1"]
        assert updated_memories == ["new-mem-1"]
