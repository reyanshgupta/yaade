"""Integration tests for MCP tools in main.py."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

# Import the module to test - we'll need to mock the global context
from app.models.memory import MemoryType, MemorySource


class TestHealthCheckTool:
    """Tests for the health_check MCP tool."""

    @pytest.mark.asyncio
    async def test_health_check_not_initialized(self):
        """Test health_check when server is not initialized."""
        with patch('app.main._app_context', None):
            from app.main import health_check
            
            result = await health_check()
            
            assert result["status"] == "unhealthy"
            assert "not initialized" in result["error"]

    @pytest.mark.asyncio
    async def test_health_check_success(self, mock_vector_store, mock_embedding_service):
        """Test health_check when server is healthy."""
        mock_context = MagicMock()
        mock_context.vector_store = mock_vector_store
        mock_context.config.embedding_model_name = "test-model"
        mock_context.config.data_dir = "/test/data"
        mock_vector_store.count_memories.return_value = 42
        
        with patch('app.main._app_context', mock_context):
            from app.main import health_check
            
            result = await health_check()
            
            assert result["status"] == "healthy"
            assert result["total_memories"] == 42
            assert result["embedding_model"] == "test-model"

    @pytest.mark.asyncio
    async def test_health_check_error(self, mock_vector_store):
        """Test health_check when an error occurs."""
        mock_context = MagicMock()
        mock_context.vector_store = mock_vector_store
        mock_vector_store.count_memories.side_effect = Exception("Database error")
        
        with patch('app.main._app_context', mock_context):
            from app.main import health_check
            
            result = await health_check()
            
            assert result["status"] == "unhealthy"
            assert "error" in result


class TestAddMemoryTool:
    """Tests for the add_memory MCP tool."""

    @pytest.mark.asyncio
    async def test_add_memory_not_initialized(self):
        """Test add_memory when server is not initialized."""
        with patch('app.main._app_context', None):
            from app.main import add_memory
            
            result = await add_memory(content="Test")
            
            assert result["status"] == "failed"
            assert "not initialized" in result["error"]

    @pytest.mark.asyncio
    async def test_add_memory_success(self, mock_vector_store, mock_embedding_service):
        """Test successfully adding a memory."""
        mock_context = MagicMock()
        mock_context.vector_store = mock_vector_store
        mock_context.embedding_service = mock_embedding_service
        
        with patch('app.main._app_context', mock_context):
            from app.main import add_memory
            
            result = await add_memory(
                content="Test memory content",
                memory_type="text",
                source="api",
                tags=["test"],
                importance=5.0
            )
            
            assert result["status"] == "added"
            assert "memory_id" in result
            assert "timestamp" in result
            mock_vector_store.add_memory.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_memory_invalid_type_defaults_to_text(self, mock_vector_store, mock_embedding_service):
        """Test that invalid memory_type defaults to TEXT."""
        mock_context = MagicMock()
        mock_context.vector_store = mock_vector_store
        mock_context.embedding_service = mock_embedding_service
        
        with patch('app.main._app_context', mock_context):
            from app.main import add_memory
            
            result = await add_memory(
                content="Test",
                memory_type="invalid_type"
            )
            
            assert result["status"] == "added"
            # The memory should still be added with default type

    @pytest.mark.asyncio
    async def test_add_memory_invalid_source_defaults_to_api(self, mock_vector_store, mock_embedding_service):
        """Test that invalid source defaults to API."""
        mock_context = MagicMock()
        mock_context.vector_store = mock_vector_store
        mock_context.embedding_service = mock_embedding_service
        
        with patch('app.main._app_context', mock_context):
            from app.main import add_memory
            
            result = await add_memory(
                content="Test",
                source="invalid_source"
            )
            
            assert result["status"] == "added"

    @pytest.mark.asyncio
    async def test_add_memory_embedding_error(self, mock_vector_store, mock_embedding_service):
        """Test add_memory when embedding generation fails."""
        mock_context = MagicMock()
        mock_context.vector_store = mock_vector_store
        mock_context.embedding_service = mock_embedding_service
        mock_embedding_service.encode_text.side_effect = Exception("Embedding error")
        
        with patch('app.main._app_context', mock_context):
            from app.main import add_memory
            
            result = await add_memory(content="Test")
            
            assert result["status"] == "failed"
            assert "embedding" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_add_memory_storage_error(self, mock_vector_store, mock_embedding_service):
        """Test add_memory when storage fails."""
        mock_context = MagicMock()
        mock_context.vector_store = mock_vector_store
        mock_context.embedding_service = mock_embedding_service
        mock_vector_store.add_memory.side_effect = Exception("Storage error")
        
        with patch('app.main._app_context', mock_context):
            from app.main import add_memory
            
            result = await add_memory(content="Test")
            
            assert result["status"] == "failed"
            assert "store" in result["error"].lower()


class TestSearchMemoriesTool:
    """Tests for the search_memories MCP tool."""

    @pytest.mark.asyncio
    async def test_search_memories_not_initialized(self):
        """Test search_memories when server is not initialized."""
        with patch('app.main._app_context', None):
            from app.main import search_memories
            
            result = await search_memories(query="test")
            
            assert result == []

    @pytest.mark.asyncio
    async def test_search_memories_success(self, mock_vector_store, mock_embedding_service):
        """Test successful memory search."""
        mock_context = MagicMock()
        mock_context.vector_store = mock_vector_store
        mock_context.embedding_service = mock_embedding_service
        mock_vector_store.search_similar.return_value = {
            "ids": [["id1", "id2"]],
            "documents": [["content1", "content2"]],
            "metadatas": [[{"tags": "test"}, {"tags": "sample"}]],
            "distances": [[0.1, 0.2]]
        }
        
        with patch('app.main._app_context', mock_context):
            from app.main import search_memories
            
            result = await search_memories(query="test query", limit=5)
            
            assert len(result) == 2
            assert result[0]["memory_id"] == "id1"
            assert result[0]["content"] == "content1"
            assert "similarity_score" in result[0]

    @pytest.mark.asyncio
    async def test_search_memories_with_tags(self, mock_vector_store, mock_embedding_service):
        """Test search with tag filtering."""
        mock_context = MagicMock()
        mock_context.vector_store = mock_vector_store
        mock_context.embedding_service = mock_embedding_service
        mock_vector_store.search_similar.return_value = {
            "ids": [[]],
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]]
        }
        
        with patch('app.main._app_context', mock_context):
            from app.main import search_memories
            
            await search_memories(query="test", filter_tags=["python"])
            
            # Verify filter was passed
            call_kwargs = mock_vector_store.search_similar.call_args[1]
            assert call_kwargs["filter_metadata"] is not None

    @pytest.mark.asyncio
    async def test_search_memories_error(self, mock_vector_store, mock_embedding_service):
        """Test search when error occurs."""
        mock_context = MagicMock()
        mock_context.vector_store = mock_vector_store
        mock_context.embedding_service = mock_embedding_service
        mock_embedding_service.encode_query.side_effect = Exception("Query error")
        
        with patch('app.main._app_context', mock_context):
            from app.main import search_memories
            
            result = await search_memories(query="test")
            
            assert result == []


class TestGetMemoryTool:
    """Tests for the get_memory MCP tool."""

    @pytest.mark.asyncio
    async def test_get_memory_not_initialized(self):
        """Test get_memory when server is not initialized."""
        with patch('app.main._app_context', None):
            from app.main import get_memory
            
            result = await get_memory(memory_id="test-id")
            
            assert result is None

    @pytest.mark.asyncio
    async def test_get_memory_success(self, mock_vector_store):
        """Test successfully getting a memory."""
        mock_context = MagicMock()
        mock_context.vector_store = mock_vector_store
        mock_vector_store.get_memory_by_id.return_value = {
            "id": "test-id",
            "content": "Test content",
            "metadata": {"tags": "test"}
        }
        
        with patch('app.main._app_context', mock_context):
            from app.main import get_memory
            
            result = await get_memory(memory_id="test-id")
            
            assert result is not None
            assert result["id"] == "test-id"

    @pytest.mark.asyncio
    async def test_get_memory_not_found(self, mock_vector_store):
        """Test get_memory when memory doesn't exist."""
        mock_context = MagicMock()
        mock_context.vector_store = mock_vector_store
        mock_vector_store.get_memory_by_id.return_value = None
        
        with patch('app.main._app_context', mock_context):
            from app.main import get_memory
            
            result = await get_memory(memory_id="nonexistent")
            
            assert result is None

    @pytest.mark.asyncio
    async def test_get_memory_error(self, mock_vector_store):
        """Test get_memory when error occurs."""
        mock_context = MagicMock()
        mock_context.vector_store = mock_vector_store
        mock_vector_store.get_memory_by_id.side_effect = Exception("Get error")
        
        with patch('app.main._app_context', mock_context):
            from app.main import get_memory
            
            result = await get_memory(memory_id="test-id")
            
            assert result is None


class TestDeleteMemoryTool:
    """Tests for the delete_memory MCP tool."""

    @pytest.mark.asyncio
    async def test_delete_memory_not_initialized(self):
        """Test delete_memory when server is not initialized."""
        with patch('app.main._app_context', None):
            from app.main import delete_memory
            
            result = await delete_memory(memory_id="test-id")
            
            assert result["status"] == "error"
            assert "not initialized" in result["error"]

    @pytest.mark.asyncio
    async def test_delete_memory_success(self, mock_vector_store):
        """Test successfully deleting a memory."""
        mock_context = MagicMock()
        mock_context.vector_store = mock_vector_store
        mock_vector_store.delete_memory.return_value = True
        
        with patch('app.main._app_context', mock_context):
            from app.main import delete_memory
            
            result = await delete_memory(memory_id="test-id")
            
            assert result["status"] == "deleted"
            assert result["memory_id"] == "test-id"
            assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_delete_memory_not_found(self, mock_vector_store):
        """Test deleting non-existent memory."""
        mock_context = MagicMock()
        mock_context.vector_store = mock_vector_store
        mock_vector_store.delete_memory.return_value = False
        
        with patch('app.main._app_context', mock_context):
            from app.main import delete_memory
            
            result = await delete_memory(memory_id="nonexistent")
            
            assert result["status"] == "not_found"

    @pytest.mark.asyncio
    async def test_delete_memory_error(self, mock_vector_store):
        """Test delete_memory when error occurs."""
        mock_context = MagicMock()
        mock_context.vector_store = mock_vector_store
        mock_vector_store.delete_memory.side_effect = Exception("Delete error")
        
        with patch('app.main._app_context', mock_context):
            from app.main import delete_memory
            
            result = await delete_memory(memory_id="test-id")
            
            assert result["status"] == "error"
            assert "error" in result


class TestAnalyzeMemoryCleanupTool:
    """Tests for the analyze_memory_cleanup MCP tool."""

    @pytest.mark.asyncio
    async def test_analyze_not_initialized(self):
        """Test analyze when server is not initialized."""
        with patch('app.main._app_context', None):
            from app.main import analyze_memory_cleanup
            
            result = await analyze_memory_cleanup()
            
            assert result["status"] == "failed"
            assert "not initialized" in result["error"]

    @pytest.mark.asyncio
    async def test_analyze_success(self, mock_vector_store):
        """Test successful cleanup analysis."""
        mock_cleanup_service = AsyncMock()
        mock_cleanup_service.analyze_memories_for_cleanup.return_value = {
            "total_memories": 10,
            "analysis": {
                "exact_duplicates": [],
                "near_duplicates": [],
                "consolidation_groups": []
            },
            "estimated_cleanup": {
                "memories_to_delete": 0
            }
        }
        
        mock_context = MagicMock()
        mock_context.cleanup_service = mock_cleanup_service
        
        with patch('app.main._app_context', mock_context):
            from app.main import analyze_memory_cleanup
            
            result = await analyze_memory_cleanup(
                similarity_threshold=0.9,
                consolidation_threshold=0.8
            )
            
            assert result["status"] == "analysis_complete"
            assert "analysis" in result
            assert "available_actions" in result


class TestExecuteMemoryCleanupTool:
    """Tests for the execute_memory_cleanup MCP tool."""

    @pytest.mark.asyncio
    async def test_execute_not_initialized(self):
        """Test execute when server is not initialized."""
        with patch('app.main._app_context', None):
            from app.main import execute_memory_cleanup
            
            result = await execute_memory_cleanup(
                actions_to_execute=["exact_duplicates"],
                confirm_deletion=True
            )
            
            assert result["status"] == "failed"

    @pytest.mark.asyncio
    async def test_execute_without_confirmation(self):
        """Test execute without confirmation flag."""
        mock_context = MagicMock()
        
        with patch('app.main._app_context', mock_context):
            from app.main import execute_memory_cleanup
            
            result = await execute_memory_cleanup(
                actions_to_execute=["exact_duplicates"],
                confirm_deletion=False
            )
            
            assert result["status"] == "confirmation_required"
            assert "warning" in result

    @pytest.mark.asyncio
    async def test_execute_empty_actions(self):
        """Test execute with empty actions list."""
        mock_context = MagicMock()
        
        with patch('app.main._app_context', mock_context):
            from app.main import execute_memory_cleanup
            
            result = await execute_memory_cleanup(
                actions_to_execute=[],
                confirm_deletion=True
            )
            
            assert result["status"] == "failed"
            assert "No actions" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_invalid_actions(self):
        """Test execute with invalid action types."""
        mock_context = MagicMock()
        
        with patch('app.main._app_context', mock_context):
            from app.main import execute_memory_cleanup
            
            result = await execute_memory_cleanup(
                actions_to_execute=["invalid_action"],
                confirm_deletion=True
            )
            
            assert result["status"] == "failed"
            assert "Invalid actions" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_success(self, mock_vector_store):
        """Test successful cleanup execution."""
        mock_cleanup_service = AsyncMock()
        mock_cleanup_service.analyze_memories_for_cleanup.return_value = {
            "analysis": {
                "exact_duplicates": [],
                "near_duplicates": [],
                "consolidation_groups": []
            }
        }
        mock_cleanup_service.execute_cleanup.return_value = {
            "executed_actions": ["exact_duplicates"],
            "results": {}
        }
        
        mock_context = MagicMock()
        mock_context.cleanup_service = mock_cleanup_service
        mock_context.vector_store = mock_vector_store
        mock_vector_store.count_memories.return_value = 5
        
        with patch('app.main._app_context', mock_context):
            from app.main import execute_memory_cleanup
            
            result = await execute_memory_cleanup(
                actions_to_execute=["exact_duplicates"],
                confirm_deletion=True
            )
            
            assert result["status"] == "cleanup_completed"
            assert "final_memory_count" in result
