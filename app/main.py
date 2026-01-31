"""Main FastMCP server implementation for Yaade."""

from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from contextlib import asynccontextmanager
from typing import AsyncIterator, List, Dict, Any, Optional, cast
import asyncio
import logging
from pathlib import Path
from datetime import datetime
import uuid

from .models.config import ServerConfig
from .models.memory import Memory, MemoryType, MemorySource
from .storage.vector_store import VectorStore
from .search.embeddings import EmbeddingService
from .services.memory_cleanup import MemoryCleanupService

# Global app context for accessing services
_app_context: Optional['AppContext'] = None

# Configure logging to stderr only (not stdout, which interferes with MCP stdio)
import sys
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr
)
logger = logging.getLogger(__name__)


class AppContext:
    """Application context with initialized services."""

    def __init__(self, config: ServerConfig, vector_store: VectorStore, embedding_service: EmbeddingService):
        self.config = config
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.cleanup_service = MemoryCleanupService(vector_store)


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle and service initialization."""
    global _app_context
    
    # Load configuration
    config = ServerConfig()
    logger.info("Configuration loaded")
    
    # Ensure data directory exists
    config.data_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Data directory: {config.data_dir}")
    
    # Initialize services
    logger.info("Initializing embedding service...")
    embedding_service = EmbeddingService(config.embedding_model_name)
    
    logger.info("Initializing vector store...")
    chroma_path = config.chroma_path
    vector_store = VectorStore(str(chroma_path))
    
    context = AppContext(
        config=config,
        vector_store=vector_store,
        embedding_service=embedding_service
    )
    
    # Set global context
    _app_context = context
    
    logger.info("Memory server initialized successfully")
    
    try:
        yield context
    finally:
        logger.info("Shutting down Yaade...")
        _app_context = None
        # Cleanup resources if needed


# Initialize FastMCP server with lifespan management
mcp = FastMCP("Yaade", lifespan=app_lifespan)


@mcp.tool()
async def health_check() -> dict:
    """Check server health and status.
    
    Returns:
        Dictionary with server health information
    """
    try:
        if _app_context is None:
            return {
                "status": "unhealthy",
                "error": "Server not initialized"
            }
        
        # Get memory count
        total_memories = await _app_context.vector_store.count_memories()
        
        return {
            "status": "healthy",
            "version": "0.1.0",
            "total_memories": total_memories,
            "embedding_model": _app_context.config.embedding_model_name,
            "data_directory": str(_app_context.config.data_dir)
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@mcp.tool()
async def add_memory(
    content: str,
    memory_type: str = "text",
    source: str = "api",
    tags: Optional[List[str]] = None,
    importance: float = 1.0,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Add a new memory to the server.
    
    Args:
        content: The memory content to store
        memory_type: Type of memory (text, image, document, conversation, code)
        source: Source of the memory (claude, chatgpt, browser, api, manual)
        tags: Optional list of tags for categorization
        importance: Importance score from 0.0 to 10.0
        metadata: Optional additional metadata
        
    Returns:
        Dictionary with memory_id, status, and timestamp
    """
    if _app_context is None:
        return {
            "error": "Server not initialized",
            "status": "failed"
        }
    
    logger.info(f"Adding new memory: {content[:50]}...")
    
    # Validate and convert enum values
    try:
        memory_type_enum = MemoryType(memory_type.lower())
    except ValueError:
        memory_type_enum = MemoryType.TEXT
        
    try:
        source_enum = MemorySource(source.lower())
    except ValueError:
        source_enum = MemorySource.API
    
    # Set defaults
    if tags is None:
        tags = []
    if metadata is None:
        metadata = {}
    
    # Generate embedding
    try:
        embedding = await _app_context.embedding_service.encode_text(content)
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        return {
            "error": f"Failed to generate embedding: {str(e)}",
            "status": "failed"
        }
    
    # Create memory object
    # Since we're passing a single string to encode_text, we get List[float]
    memory = Memory(
        id=str(uuid.uuid4()),
        content=content,
        type=memory_type_enum,
        source=source_enum,
        tags=tags,
        importance=importance,
        metadata=metadata,
        embedding=cast(List[float], embedding),
        updated_at=None
    )
    
    # Store in vector database
    try:
        await _app_context.vector_store.add_memory(memory)
    except Exception as e:
        logger.error(f"Failed to store memory: {e}")
        return {
            "error": f"Failed to store memory: {str(e)}",
            "status": "failed"
        }
    
    logger.info(f"Memory added with ID: {memory.id}")
        
    return {
        "memory_id": memory.id,
        "status": "added",
        "timestamp": memory.created_at.isoformat()
    }


@mcp.tool()
async def search_memories(
    query: str,
    limit: int = 10,
    filter_tags: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """Search for memories using semantic similarity.
    
    Args:
        query: Search query text
        limit: Maximum number of results to return
        filter_tags: Optional list of tags to filter by
        
    Returns:
        List of matching memories with similarity scores
    """
    if _app_context is None:
        return []
    
    logger.info(f"Searching memories: {query}")
    
    # Generate query embedding
    try:
        query_embedding = await _app_context.embedding_service.encode_query(query)
    except Exception as e:
        logger.error(f"Failed to generate query embedding: {e}")
        return []
    
    # Build filter criteria
    filter_metadata = None
    if filter_tags:
        # ChromaDB filter syntax for tags
        filter_metadata = {"tags": {"$contains": filter_tags[0]}}
    
    # Search vector store
    try:
        results = await _app_context.vector_store.search_similar(
            query_embedding=query_embedding,
            n_results=limit,
            filter_metadata=filter_metadata
        )
    except Exception as e:
        logger.error(f"Failed to search memories: {e}")
        return []
    
    # Format results
    formatted_results = []
    if results.get("ids") and results["ids"][0]:
        for i, memory_id in enumerate(results["ids"][0]):
            formatted_results.append({
                "memory_id": memory_id,
                "content": results["documents"][0][i],
                "similarity_score": 1.0 - results["distances"][0][i],  # Convert distance to similarity
                "metadata": results["metadatas"][0][i]
            })
    
    logger.info(f"Found {len(formatted_results)} results")
    
    return formatted_results


@mcp.tool()
async def get_memory(
    memory_id: str
) -> Optional[Dict[str, Any]]:
    """Retrieve a specific memory by ID.
    
    Args:
        memory_id: Unique memory identifier
        
    Returns:
        Memory data if found, None otherwise
    """
    if _app_context is None:
        return None
    
    logger.info(f"Retrieving memory: {memory_id}")
    
    try:
        memory_data = await _app_context.vector_store.get_memory_by_id(memory_id)
        return memory_data
    except Exception as e:
        logger.error(f"Failed to retrieve memory {memory_id}: {e}")
        return None


@mcp.tool()
async def delete_memory(
    memory_id: str
) -> Dict[str, Any]:
    """Delete a memory from the server.
    
    Args:
        memory_id: Memory identifier to delete
        
    Returns:
        Status information
    """
    if _app_context is None:
        return {
            "memory_id": memory_id,
            "status": "error",
            "error": "Server not initialized",
            "timestamp": datetime.now().isoformat()
        }
    
    logger.info(f"Deleting memory: {memory_id}")
    
    try:
        success = await _app_context.vector_store.delete_memory(memory_id)
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
        logger.error(f"Failed to delete memory {memory_id}: {e}")
        return {
            "memory_id": memory_id,
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@mcp.tool()
async def analyze_memory_cleanup(
    similarity_threshold: float = 0.85,
    consolidation_threshold: float = 0.70
) -> Dict[str, Any]:
    """Analyze memories for duplicate detection and consolidation opportunities.

    This tool identifies exact duplicates, near-duplicates, and memories that can be
    consolidated, but does not make any changes. Use this to preview cleanup actions.

    Args:
        similarity_threshold: Threshold for duplicate detection (0.95 = very similar, 0.8 = somewhat similar)
        consolidation_threshold: Threshold for consolidation (0.85 = can be merged, 0.7 = loosely related)

    Returns:
        Analysis results showing duplicate and consolidation opportunities for user review
    """
    if _app_context is None:
        return {
            "error": "Server not initialized",
            "status": "failed"
        }

    logger.info(f"Analyzing memories for cleanup - similarity:{similarity_threshold}, consolidation:{consolidation_threshold}")

    try:
        analysis = await _app_context.cleanup_service.analyze_memories_for_cleanup(
            similarity_threshold=similarity_threshold,
            consolidation_threshold=consolidation_threshold
        )

        logger.info(f"Cleanup analysis complete - found {analysis['estimated_cleanup']['memories_to_delete']} memories to potentially delete")

        return {
            "status": "analysis_complete",
            "analysis": analysis,
            "next_steps": "Review the proposed actions and use execute_memory_cleanup to apply specific cleanup operations.",
            "available_actions": [
                "exact_duplicates",
                "near_duplicates",
                "consolidation"
            ]
        }

    except Exception as e:
        logger.error(f"Memory cleanup analysis failed: {e}")
        return {
            "error": f"Analysis failed: {str(e)}",
            "status": "failed"
        }


@mcp.tool()
async def execute_memory_cleanup(
    actions_to_execute: List[str],
    analysis_id: Optional[str] = None,
    confirm_deletion: bool = False
) -> Dict[str, Any]:
    """Execute approved memory cleanup actions for duplicates and consolidation.

    IMPORTANT: This tool will permanently delete or modify memories. Always run analyze_memory_cleanup
    first to review what will be changed, then call this tool with confirm_deletion=True to proceed.

    Args:
        actions_to_execute: List of cleanup actions to perform:
                           - "exact_duplicates": Remove memories with identical content
                           - "near_duplicates": Remove memories with very similar content
                           - "consolidation": Merge related memories into single entries
        analysis_id: Optional reference to previous analysis (for audit trail)
        confirm_deletion: Must be True to confirm you want to permanently delete/modify memories

    Returns:
        Results of cleanup execution with counts of deleted/consolidated memories
    """
    if _app_context is None:
        return {
            "error": "Server not initialized",
            "status": "failed"
        }

    if not confirm_deletion:
        return {
            "error": "Cleanup not executed - must set confirm_deletion=True to proceed with permanent changes",
            "status": "confirmation_required",
            "warning": "This operation will permanently delete duplicates or consolidate memories in your database"
        }

    if not actions_to_execute:
        return {
            "error": "No actions specified to execute",
            "status": "failed"
        }

    # Validate action types
    valid_actions = ["exact_duplicates", "near_duplicates", "consolidation"]
    invalid_actions = [action for action in actions_to_execute if action not in valid_actions]
    if invalid_actions:
        return {
            "error": f"Invalid actions: {invalid_actions}. Valid actions are: {valid_actions}",
            "status": "failed"
        }

    logger.info(f"Executing memory cleanup with actions: {actions_to_execute}")

    try:
        # First run analysis to get current state
        analysis = await _app_context.cleanup_service.analyze_memories_for_cleanup()

        # Execute the requested cleanup actions
        results = await _app_context.cleanup_service.execute_cleanup(
            analysis_result=analysis,
            actions_to_execute=actions_to_execute
        )

        # Get final memory count
        final_count = await _app_context.vector_store.count_memories()

        logger.info(f"Memory cleanup completed - final memory count: {final_count}")

        return {
            "status": "cleanup_completed",
            "execution_results": results,
            "final_memory_count": final_count,
            "analysis_reference": analysis_id,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Memory cleanup execution failed: {e}")
        return {
            "error": f"Cleanup execution failed: {str(e)}",
            "status": "failed"
        }


def main():
    """Main entry point for the Yaade MCP server."""
    # Log startup info to stderr (stdout is reserved for MCP JSON-RPC)
    logger.info("Starting Yaade...")
    logger.info("Server Information:")
    logger.info("   - Name: Yaade")
    logger.info("   - Version: 0.1.0")
    logger.info("   - Protocol: MCP (Model Context Protocol)")
    logger.info("   - Transport: stdio (Claude Desktop compatible)")
    logger.info("Available Tools:")
    logger.info("   - health_check - Check server status")
    logger.info("   - add_memory - Store new memory with embedding")
    logger.info("   - search_memories - Semantic search across memories")
    logger.info("   - get_memory - Retrieve specific memory by ID")
    logger.info("   - delete_memory - Remove memory from storage")
    logger.info("   - analyze_memory_cleanup - Analyze memories for cleanup opportunities")
    logger.info("   - execute_memory_cleanup - Execute cleanup actions with confirmation")
    logger.info("Storage Backend:")
    logger.info("   - Vector Store: ChromaDB (semantic search)")
    logger.info("   - Embeddings: sentence-transformers (all-MiniLM-L6-v2)")
    logger.info("   - Data Location: .yaade/")
    logger.info("Yaade ready for MCP connections!")
    
    # Run the server
    mcp.run()


if __name__ == "__main__":
    main()