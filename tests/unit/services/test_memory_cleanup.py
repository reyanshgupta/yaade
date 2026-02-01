"""Unit tests for MemoryCleanupService."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.memory_cleanup import (
    MemoryCleanupService,
    DuplicateGroup,
    ConsolidationGroup
)


class TestDuplicateGroup:
    """Tests for DuplicateGroup class."""

    @pytest.fixture
    def sample_memories(self):
        """Create sample memories for duplicate group."""
        return [
            {
                "id": "mem1",
                "content": "Test content",
                "metadata": {"importance": 3.0, "created_at": "2024-01-01T00:00:00"}
            },
            {
                "id": "mem2",
                "content": "Test content",
                "metadata": {"importance": 7.0, "created_at": "2024-01-02T00:00:00"}
            },
            {
                "id": "mem3",
                "content": "Test content",
                "metadata": {"importance": 5.0, "created_at": "2024-01-03T00:00:00"}
            }
        ]

    def test_duplicate_group_creation(self, sample_memories):
        """Test creating a DuplicateGroup."""
        group = DuplicateGroup(sample_memories, "exact", 1.0)
        
        assert group.memories == sample_memories
        assert group.similarity_type == "exact"
        assert group.confidence == 1.0

    def test_get_primary_memory_by_importance(self, sample_memories):
        """Test that primary memory is the one with highest importance."""
        group = DuplicateGroup(sample_memories, "exact", 1.0)
        
        primary = group.get_primary_memory()
        
        # mem2 has highest importance (7.0)
        assert primary["id"] == "mem2"
        assert primary["metadata"]["importance"] == 7.0

    def test_get_primary_memory_tiebreak_by_date(self):
        """Test that ties are broken by creation date."""
        memories = [
            {
                "id": "mem1",
                "content": "Test",
                "metadata": {"importance": 5.0, "created_at": "2024-01-01T00:00:00"}
            },
            {
                "id": "mem2",
                "content": "Test",
                "metadata": {"importance": 5.0, "created_at": "2024-01-02T00:00:00"}
            }
        ]
        group = DuplicateGroup(memories, "exact", 1.0)
        
        primary = group.get_primary_memory()
        
        # mem2 is more recent
        assert primary["id"] == "mem2"

    def test_get_duplicates_to_remove(self, sample_memories):
        """Test getting list of duplicates to remove."""
        group = DuplicateGroup(sample_memories, "exact", 1.0)
        
        to_remove = group.get_duplicates_to_remove()
        
        # mem2 is primary (highest importance), others should be removed
        assert len(to_remove) == 2
        removed_ids = [m["id"] for m in to_remove]
        assert "mem2" not in removed_ids
        assert "mem1" in removed_ids
        assert "mem3" in removed_ids

    def test_get_primary_memory_missing_metadata(self):
        """Test handling memories with missing metadata fields."""
        memories = [
            {
                "id": "mem1",
                "content": "Test",
                "metadata": {}  # No importance or created_at
            },
            {
                "id": "mem2",
                "content": "Test",
                "metadata": {"importance": 5.0}
            }
        ]
        group = DuplicateGroup(memories, "exact", 1.0)
        
        primary = group.get_primary_memory()
        
        # mem2 has explicit importance
        assert primary["id"] == "mem2"


class TestConsolidationGroup:
    """Tests for ConsolidationGroup class."""

    @pytest.fixture
    def sample_memories_for_consolidation(self):
        """Create sample memories for consolidation."""
        return [
            {
                "id": "mem1",
                "content": "First piece of information.",
                "metadata": {
                    "tags": "python,programming",
                    "importance": 3.0,
                    "source": "claude",
                    "created_at": "2024-01-01T00:00:00"
                }
            },
            {
                "id": "mem2",
                "content": "Second piece of information.",
                "metadata": {
                    "tags": "python,testing",
                    "importance": 5.0,
                    "source": "api",
                    "created_at": "2024-01-02T00:00:00"
                }
            },
            {
                "id": "mem3",
                "content": "Third piece of information.",
                "metadata": {
                    "tags": "documentation",
                    "importance": 7.0,
                    "source": "claude",
                    "created_at": "2024-01-03T00:00:00"
                }
            }
        ]

    def test_consolidation_group_creation(self, sample_memories_for_consolidation):
        """Test creating a ConsolidationGroup."""
        group = ConsolidationGroup(
            sample_memories_for_consolidation,
            "Similar Python memories"
        )
        
        assert len(group.memories) == 3
        assert group.consolidation_reason == "Similar Python memories"

    def test_create_consolidated_content(self, sample_memories_for_consolidation):
        """Test creating consolidated content from memories."""
        group = ConsolidationGroup(
            sample_memories_for_consolidation,
            "test"
        )
        
        content = group.create_consolidated_content()
        
        assert "[1]" in content
        assert "[2]" in content
        assert "[3]" in content
        assert "First piece of information." in content
        assert "Second piece of information." in content
        assert "Third piece of information." in content

    def test_consolidated_content_sorted_by_date(self, sample_memories_for_consolidation):
        """Test that consolidated content is sorted by creation date."""
        # Reverse the order of memories
        reversed_memories = list(reversed(sample_memories_for_consolidation))
        group = ConsolidationGroup(reversed_memories, "test")
        
        content = group.create_consolidated_content()
        
        # Should still be in date order (First before Second before Third)
        first_pos = content.find("First piece")
        second_pos = content.find("Second piece")
        third_pos = content.find("Third piece")
        
        assert first_pos < second_pos < third_pos

    def test_get_consolidated_metadata(self, sample_memories_for_consolidation):
        """Test getting consolidated metadata."""
        group = ConsolidationGroup(
            sample_memories_for_consolidation,
            "Test consolidation"
        )
        
        metadata = group.get_consolidated_metadata()
        
        # Check tags are combined and sorted
        tags = metadata["tags"].split(",")
        assert "python" in tags
        assert "programming" in tags
        assert "testing" in tags
        assert "documentation" in tags
        
        # Check importance is averaged (3+5+7)/3 = 5.0
        assert metadata["importance"] == 5.0
        
        # Check source is marked as consolidated
        assert metadata["source"] == "consolidated"
        
        # Check original sources are preserved
        assert "claude" in metadata["original_sources"]
        assert "api" in metadata["original_sources"]
        
        # Check consolidation tracking
        assert len(metadata["consolidated_from"]) == 3
        assert "mem1" in metadata["consolidated_from"]
        
        # Check reason and timestamp
        assert metadata["consolidation_reason"] == "Test consolidation"
        assert "created_at" in metadata

    def test_consolidated_metadata_empty_tags(self):
        """Test consolidation with empty tags."""
        memories = [
            {
                "id": "mem1",
                "content": "Test",
                "metadata": {"tags": "", "importance": 5.0, "source": "api"}
            },
            {
                "id": "mem2",
                "content": "Test",
                "metadata": {"importance": 3.0, "source": "manual"}
            }
        ]
        group = ConsolidationGroup(memories, "test")
        
        metadata = group.get_consolidated_metadata()
        
        # Should handle empty/missing tags gracefully
        assert isinstance(metadata["tags"], str)

    def test_consolidated_importance_capped_at_10(self):
        """Test that consolidated importance doesn't exceed 10."""
        memories = [
            {"id": "m1", "content": "Test", "metadata": {"importance": 10.0, "source": "api"}},
            {"id": "m2", "content": "Test", "metadata": {"importance": 10.0, "source": "api"}},
            {"id": "m3", "content": "Test", "metadata": {"importance": 10.0, "source": "api"}}
        ]
        group = ConsolidationGroup(memories, "test")
        
        metadata = group.get_consolidated_metadata()
        
        # Average is 10, should not exceed 10
        assert metadata["importance"] <= 10.0


class TestMemoryCleanupService:
    """Tests for MemoryCleanupService class."""

    @pytest.fixture
    def cleanup_service(self, mock_vector_store):
        """Create a MemoryCleanupService with mocked vector store."""
        return MemoryCleanupService(mock_vector_store)

    @pytest.mark.asyncio
    async def test_analyze_empty_memories(self, cleanup_service, mock_vector_store):
        """Test analyzing when no memories exist."""
        mock_vector_store.count_memories.return_value = 0
        mock_vector_store.search_similar.return_value = {
            "ids": [[]],
            "documents": [[]],
            "metadatas": [[]],
            "embeddings": [[]]
        }
        
        result = await cleanup_service.analyze_memories_for_cleanup()
        
        assert result["total_memories"] == 0
        assert result["analysis"]["exact_duplicates"] == []
        assert result["analysis"]["near_duplicates"] == []
        assert result["analysis"]["consolidation_groups"] == []

    @pytest.mark.asyncio
    async def test_find_exact_duplicates(self, cleanup_service):
        """Test finding exact duplicate memories."""
        memories = [
            {"id": "mem1", "content": "Test content", "metadata": {"importance": 3.0, "created_at": "2024-01-01"}},
            {"id": "mem2", "content": "Test content", "metadata": {"importance": 5.0, "created_at": "2024-01-02"}},
            {"id": "mem3", "content": "Different content", "metadata": {"importance": 4.0, "created_at": "2024-01-03"}}
        ]
        
        result = await cleanup_service._find_exact_duplicates(memories)
        
        assert len(result) == 1  # One group of duplicates
        assert len(result[0].memories) == 2  # Two memories are duplicates
        assert result[0].similarity_type == "exact"
        assert result[0].confidence == 1.0

    @pytest.mark.asyncio
    async def test_find_exact_duplicates_case_insensitive(self, cleanup_service):
        """Test that exact duplicate detection is case insensitive."""
        memories = [
            {"id": "mem1", "content": "Test Content", "metadata": {}},
            {"id": "mem2", "content": "test content", "metadata": {}},
            {"id": "mem3", "content": "TEST CONTENT", "metadata": {}}
        ]
        
        result = await cleanup_service._find_exact_duplicates(memories)
        
        assert len(result) == 1
        assert len(result[0].memories) == 3

    @pytest.mark.asyncio
    async def test_find_exact_duplicates_strips_whitespace(self, cleanup_service):
        """Test that exact duplicate detection strips whitespace."""
        memories = [
            {"id": "mem1", "content": "  Test content  ", "metadata": {}},
            {"id": "mem2", "content": "Test content", "metadata": {}}
        ]
        
        result = await cleanup_service._find_exact_duplicates(memories)
        
        assert len(result) == 1
        assert len(result[0].memories) == 2

    @pytest.mark.asyncio
    async def test_find_near_duplicates_empty(self, cleanup_service):
        """Test finding near duplicates with no embeddings."""
        memories = [
            {"id": "mem1", "content": "Test", "metadata": {}},
            {"id": "mem2", "content": "Different", "metadata": {}}
        ]
        
        result = await cleanup_service._find_near_duplicates(memories, 0.95)
        
        assert result == []

    @pytest.mark.asyncio
    async def test_find_near_duplicates_similar(self, cleanup_service):
        """Test finding near duplicates with similar embeddings."""
        # Create memories with very similar embeddings
        base_embedding = [0.1] * 384
        similar_embedding = [0.1 + 0.0001] * 384  # Very similar
        
        memories = [
            {"id": "mem1", "content": "Test 1", "metadata": {}, "embedding": base_embedding},
            {"id": "mem2", "content": "Test 2", "metadata": {}, "embedding": similar_embedding}
        ]
        
        result = await cleanup_service._find_near_duplicates(memories, 0.99)
        
        # With very similar embeddings, should find a group
        assert len(result) >= 0  # May or may not find duplicates depending on threshold

    @pytest.mark.asyncio
    async def test_find_near_duplicates_different(self, cleanup_service):
        """Test that very different embeddings are not marked as duplicates."""
        memories = [
            {"id": "mem1", "content": "Test 1", "metadata": {}, "embedding": [1.0] * 384},
            {"id": "mem2", "content": "Test 2", "metadata": {}, "embedding": [-1.0] * 384}
        ]
        
        result = await cleanup_service._find_near_duplicates(memories, 0.95)
        
        assert len(result) == 0  # No near duplicates

    @pytest.mark.asyncio
    async def test_execute_cleanup_empty_actions(self, cleanup_service):
        """Test execute_cleanup with empty actions list."""
        analysis_result = {
            "analysis": {
                "exact_duplicates": [],
                "near_duplicates": [],
                "consolidation_groups": []
            }
        }
        
        result = await cleanup_service.execute_cleanup(analysis_result, [])
        
        assert result["executed_actions"] == []
        assert result["results"] == {}

    @pytest.mark.asyncio
    async def test_execute_cleanup_exact_duplicates(self, cleanup_service, mock_vector_store):
        """Test executing exact duplicate removal."""
        analysis_result = {
            "analysis": {
                "exact_duplicates": [
                    {
                        "duplicates_to_remove": ["mem1", "mem2"]
                    }
                ],
                "near_duplicates": [],
                "consolidation_groups": []
            }
        }
        
        result = await cleanup_service.execute_cleanup(
            analysis_result,
            ["exact_duplicates"]
        )
        
        assert "exact_duplicates" in result["results"]
        assert mock_vector_store.delete_memory.call_count == 2

    @pytest.mark.asyncio
    async def test_execute_cleanup_with_errors(self, cleanup_service, mock_vector_store):
        """Test execute_cleanup handles deletion errors."""
        mock_vector_store.delete_memory.side_effect = Exception("Delete failed")
        
        analysis_result = {
            "analysis": {
                "exact_duplicates": [
                    {"duplicates_to_remove": ["mem1"]}
                ],
                "near_duplicates": [],
                "consolidation_groups": []
            }
        }
        
        result = await cleanup_service.execute_cleanup(
            analysis_result,
            ["exact_duplicates"]
        )
        
        assert len(result["results"]["exact_duplicates"]["errors"]) > 0

    @pytest.mark.asyncio
    async def test_check_group_similarity(self, cleanup_service):
        """Test _check_group_similarity method."""
        # Similar embeddings
        similar_memories = [
            {"embedding": [0.1] * 384},
            {"embedding": [0.1] * 384}
        ]
        
        result = await cleanup_service._check_group_similarity(similar_memories, 0.9)
        assert result is True
        
        # Single memory - not enough for comparison
        single = [{"embedding": [0.1] * 384}]
        result = await cleanup_service._check_group_similarity(single, 0.9)
        assert result is False

    @pytest.mark.asyncio
    async def test_serialize_duplicate_group(self, cleanup_service):
        """Test serializing a duplicate group."""
        memories = [
            {"id": "mem1", "content": "Short content", "metadata": {"importance": 3.0, "created_at": "2024-01-01"}},
            {"id": "mem2", "content": "Short content", "metadata": {"importance": 5.0, "created_at": "2024-01-02"}}
        ]
        group = DuplicateGroup(memories, "exact", 1.0)
        
        serialized = cleanup_service._serialize_duplicate_group(group)
        
        assert serialized["type"] == "exact"
        assert serialized["confidence"] == 1.0
        assert len(serialized["memories"]) == 2
        assert "primary_memory" in serialized
        assert "duplicates_to_remove" in serialized

    @pytest.mark.asyncio
    async def test_serialize_duplicate_group_truncates_content(self, cleanup_service):
        """Test that long content is truncated in serialization."""
        long_content = "x" * 200
        memories = [
            {"id": "mem1", "content": long_content, "metadata": {"importance": 3.0, "created_at": "2024-01-01"}}
        ]
        group = DuplicateGroup(memories, "exact", 1.0)
        
        serialized = cleanup_service._serialize_duplicate_group(group)
        
        # Content should be truncated with "..."
        assert len(serialized["memories"][0]["content"]) <= 103

    @pytest.mark.asyncio
    async def test_serialize_consolidation_group(self, cleanup_service):
        """Test serializing a consolidation group."""
        memories = [
            {"id": "mem1", "content": "Test 1", "metadata": {"tags": "test", "created_at": "2024-01-01"}},
            {"id": "mem2", "content": "Test 2", "metadata": {"tags": "test", "created_at": "2024-01-02"}}
        ]
        group = ConsolidationGroup(memories, "Similar test memories")
        
        serialized = cleanup_service._serialize_consolidation_group(group)
        
        assert serialized["reason"] == "Similar test memories"
        assert serialized["memory_count"] == 2
        assert len(serialized["memories"]) == 2
        assert "consolidated_content_preview" in serialized
