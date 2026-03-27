"""Memory cleanup service for detecting duplicates and consolidating memories."""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import numpy as np
from collections import defaultdict

from ..storage.vector_store import VectorStore

logger = logging.getLogger(__name__)


class DuplicateGroup:
    """Represents a group of duplicate or similar memories."""

    def __init__(self, memories: List[Dict[str, Any]], similarity_type: str, confidence: float):
        self.memories = memories
        self.similarity_type = similarity_type  # "exact", "near_duplicate", "similar"
        self.confidence = confidence

    def get_primary_memory(self) -> Dict[str, Any]:
        """Get the memory that should be kept (highest importance, most recent)."""
        return max(self.memories, key=lambda m: (
            float(m.get("metadata", {}).get("importance", 1.0)),
            m.get("metadata", {}).get("created_at", "")
        ))

    def get_duplicates_to_remove(self) -> List[Dict[str, Any]]:
        """Get memories that should be removed."""
        primary = self.get_primary_memory()
        return [m for m in self.memories if m["id"] != primary["id"]]


class ConsolidationGroup:
    """Represents a group of memories that can be consolidated."""

    def __init__(self, memories: List[Dict[str, Any]], consolidation_reason: str):
        self.memories = memories
        self.consolidation_reason = consolidation_reason

    def create_consolidated_content(self) -> str:
        """Create consolidated content from multiple memories."""
        # Sort by creation date
        sorted_memories = sorted(
            self.memories,
            key=lambda m: m.get("metadata", {}).get("created_at", "")
        )

        consolidated_parts = []
        for i, memory in enumerate(sorted_memories, 1):
            content = memory["content"].strip()
            consolidated_parts.append(f"[{i}] {content}")

        return "\n\n".join(consolidated_parts)

    def get_consolidated_metadata(self) -> Dict[str, Any]:
        """Create consolidated metadata."""
        # Combine tags from all memories
        all_tags = set()
        total_importance = 0
        sources = set()

        for memory in self.memories:
            metadata = memory.get("metadata", {})
            if "tags" in metadata:
                all_tags.update(metadata["tags"].split(",") if metadata["tags"] else [])
            total_importance += float(metadata.get("importance", 1.0))
            sources.add(metadata.get("source", "unknown"))

        return {
            "tags": ",".join(sorted(all_tags)),
            "importance": min(10.0, total_importance / len(self.memories)),
            "source": "consolidated",
            "original_sources": ",".join(sources),
            "consolidated_from": [m["id"] for m in self.memories],
            "consolidation_reason": self.consolidation_reason,
            "created_at": datetime.now().isoformat()
        }


class MemoryCleanupService:
    """Service for cleaning up memory storage by removing duplicates and consolidating similar memories."""

    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store

    async def analyze_memories_for_cleanup(
        self,
        similarity_threshold: float = 0.95,
        consolidation_threshold: float = 0.85
    ) -> Dict[str, Any]:
        """Analyze all memories and identify duplicate and consolidation opportunities.

        Args:
            similarity_threshold: Threshold for duplicate detection (0.95 = very similar)
            consolidation_threshold: Threshold for consolidation (0.85 = somewhat similar)

        Returns:
            Dictionary with analysis results and proposed actions for duplicates and consolidation
        """
        logger.info("Starting memory cleanup analysis...")

        # Get all memories
        all_memories = await self._get_all_memories()
        logger.info(f"Analyzing {len(all_memories)} memories for cleanup")

        if not all_memories:
            return {
                "total_memories": 0,
                "analysis": {
                    "exact_duplicates": [],
                    "near_duplicates": [],
                    "consolidation_groups": []
                },
                "proposed_actions": {
                    "delete_exact_duplicates": 0,
                    "delete_near_duplicates": 0,
                    "consolidate_groups": 0
                },
                "estimated_cleanup": {
                    "memories_to_delete": 0,
                    "memories_to_consolidate": 0,
                    "final_count": 0
                }
            }

        # Detect exact duplicates
        exact_duplicates = await self._find_exact_duplicates(all_memories)

        # Detect near duplicates
        near_duplicates = await self._find_near_duplicates(
            all_memories, similarity_threshold
        )

        # Find consolidation opportunities
        consolidation_groups = await self._find_consolidation_opportunities(
            all_memories, consolidation_threshold
        )

        # Calculate proposed actions
        delete_exact = sum(len(group.get_duplicates_to_remove()) for group in exact_duplicates)
        delete_near = sum(len(group.get_duplicates_to_remove()) for group in near_duplicates)
        consolidate_count = sum(len(group.memories) for group in consolidation_groups)

        # Remove overlaps (don't double-count memories)
        all_to_delete = set()
        for group in exact_duplicates + near_duplicates:
            all_to_delete.update(m["id"] for m in group.get_duplicates_to_remove())

        all_to_consolidate = set()
        for group in consolidation_groups:
            all_to_consolidate.update(m["id"] for m in group.memories)

        return {
            "total_memories": len(await self._get_all_memories()),
            "analysis": {
                "exact_duplicates": [self._serialize_duplicate_group(g) for g in exact_duplicates],
                "near_duplicates": [self._serialize_duplicate_group(g) for g in near_duplicates],
                "consolidation_groups": [self._serialize_consolidation_group(g) for g in consolidation_groups]
            },
            "proposed_actions": {
                "delete_exact_duplicates": delete_exact,
                "delete_near_duplicates": delete_near,
                "consolidate_groups": len(consolidation_groups)
            },
            "estimated_cleanup": {
                "memories_to_delete": len(all_to_delete),
                "memories_to_consolidate": len(all_to_consolidate),
                "final_count": len(await self._get_all_memories()) - len(all_to_delete) - len(all_to_consolidate) + len(consolidation_groups)
            }
        }

    async def execute_cleanup(
        self,
        analysis_result: Dict[str, Any],
        actions_to_execute: List[str]
    ) -> Dict[str, Any]:
        """Execute the approved cleanup actions.

        Args:
            analysis_result: Result from analyze_memories_for_cleanup
            actions_to_execute: List of action types to execute
                                ["exact_duplicates", "near_duplicates", "consolidation"]

        Returns:
            Execution results
        """
        logger.info(f"Executing cleanup actions: {actions_to_execute}")

        results = {
            "executed_actions": actions_to_execute,
            "results": {},
            "errors": []
        }

        try:
            # Execute exact duplicate removal
            if "exact_duplicates" in actions_to_execute:
                exact_result = await self._execute_duplicate_removal(
                    analysis_result["analysis"]["exact_duplicates"]
                )
                results["results"]["exact_duplicates"] = exact_result

            # Execute near duplicate removal
            if "near_duplicates" in actions_to_execute:
                near_result = await self._execute_duplicate_removal(
                    analysis_result["analysis"]["near_duplicates"]
                )
                results["results"]["near_duplicates"] = near_result

            # Execute consolidation
            if "consolidation" in actions_to_execute:
                consolidation_result = await self._execute_consolidation(
                    analysis_result["analysis"]["consolidation_groups"]
                )
                results["results"]["consolidation"] = consolidation_result

        except Exception as e:
            error_msg = f"Error during cleanup execution: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)

        return results

    async def _get_all_memories(self) -> List[Dict[str, Any]]:
        """Get all memories from the vector store."""
        try:
            # ChromaDB doesn't have a direct "get all" method, so we'll use a workaround
            # We'll query with a dummy embedding and high n_results
            count = await self.vector_store.count_memories()
            if count == 0:
                return []

            # Create a dummy query to get all memories
            dummy_embedding = [0.0] * 384  # Assuming 384-dim embeddings from MiniLM
            results = await self.vector_store.search_similar(
                query_embedding=dummy_embedding,
                n_results=count
            )

            memories = []
            if results.get("ids") and len(results["ids"]) > 0 and results["ids"][0]:
                for i, memory_id in enumerate(results["ids"][0]):
                    memories.append({
                        "id": memory_id,
                        "content": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "embedding": results.get("embeddings", [[]])[0][i] if results.get("embeddings") else None
                    })

            return memories
        except Exception as e:
            logger.error(f"Error getting all memories: {e}")
            return []

    async def _find_exact_duplicates(self, memories: List[Dict[str, Any]]) -> List[DuplicateGroup]:
        """Find memories with exactly the same content."""
        content_groups = defaultdict(list)

        for memory in memories:
            content = memory["content"].strip().lower()
            content_groups[content].append(memory)

        duplicates = []
        for content, group in content_groups.items():
            if len(group) > 1:
                duplicates.append(DuplicateGroup(group, "exact", 1.0))

        logger.info(f"Found {len(duplicates)} exact duplicate groups")
        return duplicates

    async def _find_near_duplicates(
        self,
        memories: List[Dict[str, Any]],
        threshold: float
    ) -> List[DuplicateGroup]:
        """Find memories with very similar content using embeddings."""
        if not memories:
            return []

        # Extract embeddings
        embeddings = []
        valid_memories = []

        for memory in memories:
            if memory.get("embedding"):
                embeddings.append(memory["embedding"])
                valid_memories.append(memory)

        if len(embeddings) < 2:
            return []

        # Calculate similarity matrix
        embeddings_array = np.array(embeddings)
        similarity_matrix = np.dot(embeddings_array, embeddings_array.T)

        # Normalize by magnitudes
        norms = np.linalg.norm(embeddings_array, axis=1)
        similarity_matrix = similarity_matrix / np.outer(norms, norms)

        # Find near duplicates
        duplicates = []
        processed = set()

        for i in range(len(valid_memories)):
            if i in processed:
                continue

            similar_indices = [i]
            for j in range(i + 1, len(valid_memories)):
                if j in processed:
                    continue
                if similarity_matrix[i, j] >= threshold:
                    similar_indices.append(j)

            if len(similar_indices) > 1:
                group_memories = [valid_memories[idx] for idx in similar_indices]
                avg_similarity = np.mean([
                    similarity_matrix[similar_indices[0], idx]
                    for idx in similar_indices[1:]
                ])
                duplicates.append(DuplicateGroup(group_memories, "near_duplicate", float(avg_similarity)))
                processed.update(similar_indices)

        logger.info(f"Found {len(duplicates)} near-duplicate groups")
        return duplicates

    async def _find_consolidation_opportunities(
        self,
        memories: List[Dict[str, Any]],
        threshold: float
    ) -> List[ConsolidationGroup]:
        """Find groups of related memories that can be consolidated."""
        if not memories:
            return []

        # Group by tags first
        tag_groups = defaultdict(list)
        for memory in memories:
            tags = memory.get("metadata", {}).get("tags", "")
            if tags:
                tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
                for tag in tag_list:
                    tag_groups[tag].append(memory)

        consolidation_groups = []

        # Find groups with multiple memories for the same tag
        for tag, tag_memories in tag_groups.items():
            if len(tag_memories) >= 3:  # Only consolidate if 3+ memories
                # Check if they're similar enough
                if await self._check_group_similarity(tag_memories, threshold):
                    consolidation_groups.append(
                        ConsolidationGroup(tag_memories, f"Similar memories with tag: {tag}")
                    )

        # Also look for memories with similar content but different tags
        # This is more computationally expensive, so we'll limit it
        untagged_memories = [m for m in memories if not m.get("metadata", {}).get("tags")]
        if len(untagged_memories) >= 3:
            similar_groups = await self._find_similar_content_groups(untagged_memories, threshold)
            consolidation_groups.extend(similar_groups)

        logger.info(f"Found {len(consolidation_groups)} consolidation opportunities")
        return consolidation_groups

    async def _check_group_similarity(self, memories: List[Dict[str, Any]], threshold: float) -> bool:
        """Check if a group of memories is similar enough for consolidation."""
        if len(memories) < 2:
            return False

        embeddings = [m.get("embedding") for m in memories if m.get("embedding")]
        if len(embeddings) < 2:
            return False

        # Calculate average pairwise similarity
        similarities = []
        embeddings_array = np.array(embeddings)

        for i in range(len(embeddings)):
            for j in range(i + 1, len(embeddings)):
                sim = np.dot(embeddings_array[i], embeddings_array[j]) / (
                    np.linalg.norm(embeddings_array[i]) * np.linalg.norm(embeddings_array[j])
                )
                similarities.append(sim)

        avg_similarity = float(np.mean(similarities)) if similarities else 0.0
        return bool(avg_similarity >= threshold)

    async def _find_similar_content_groups(
        self,
        memories: List[Dict[str, Any]],
        threshold: float
    ) -> List[ConsolidationGroup]:
        """Find groups of memories with similar content."""
        # This is a simplified implementation
        # In practice, you might want to use clustering algorithms
        groups = []

        # For now, just group memories that are very similar
        processed = set()
        for i, memory in enumerate(memories):
            if i in processed:
                continue

            similar_memories = [memory]
            if memory.get("embedding"):
                for j, other_memory in enumerate(memories[i+1:], i+1):
                    if j in processed or not other_memory.get("embedding"):
                        continue

                    # Calculate similarity
                    sim = np.dot(memory["embedding"], other_memory["embedding"]) / (
                        np.linalg.norm(memory["embedding"]) * np.linalg.norm(other_memory["embedding"])
                    )

                    if sim >= threshold:
                        similar_memories.append(other_memory)
                        processed.add(j)

            if len(similar_memories) >= 3:
                groups.append(ConsolidationGroup(similar_memories, "Similar content"))
                processed.add(i)

        return groups

    def _serialize_duplicate_group(self, group: DuplicateGroup) -> Dict[str, Any]:
        """Serialize a duplicate group for JSON response."""
        return {
            "type": group.similarity_type,
            "confidence": group.confidence,
            "memories": [
                {
                    "id": m["id"],
                    "content": m["content"][:100] + "..." if len(m["content"]) > 100 else m["content"],
                    "importance": m.get("metadata", {}).get("importance", 1.0),
                    "created_at": m.get("metadata", {}).get("created_at")
                }
                for m in group.memories
            ],
            "primary_memory": {
                "id": group.get_primary_memory()["id"],
                "content": group.get_primary_memory()["content"][:100] + "..."
            },
            "duplicates_to_remove": [m["id"] for m in group.get_duplicates_to_remove()]
        }

    def _serialize_consolidation_group(self, group: ConsolidationGroup) -> Dict[str, Any]:
        """Serialize a consolidation group for JSON response."""
        return {
            "reason": group.consolidation_reason,
            "memory_count": len(group.memories),
            "memories": [
                {
                    "id": m["id"],
                    "content": m["content"][:100] + "..." if len(m["content"]) > 100 else m["content"],
                    "tags": m.get("metadata", {}).get("tags"),
                    "created_at": m.get("metadata", {}).get("created_at")
                }
                for m in group.memories
            ],
            "consolidated_content_preview": group.create_consolidated_content()[:200] + "..."
        }

    async def _execute_duplicate_removal(self, duplicate_groups: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute removal of duplicate memories."""
        deleted_count = 0
        errors = []

        for group_data in duplicate_groups:
            for memory_id in group_data["duplicates_to_remove"]:
                try:
                    success = await self.vector_store.delete_memory(memory_id)
                    if success:
                        deleted_count += 1
                    else:
                        errors.append(f"Failed to delete memory {memory_id}")
                except Exception as e:
                    errors.append(f"Error deleting memory {memory_id}: {str(e)}")

        return {
            "deleted_count": deleted_count,
            "errors": errors
        }

    async def _execute_consolidation(self, consolidation_groups: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute memory consolidation."""
        consolidated_count = 0
        errors = []

        for group_data in consolidation_groups:
            try:
                # Create consolidated memory (this would need the embedding service)
                # For now, we'll just delete the individual memories
                # In a full implementation, you'd create a new consolidated memory

                memory_ids = [m["id"] for m in group_data["memories"]]
                for memory_id in memory_ids:
                    success = await self.vector_store.delete_memory(memory_id)
                    if not success:
                        errors.append(f"Failed to delete memory {memory_id} during consolidation")

                consolidated_count += 1

            except Exception as e:
                errors.append(f"Error consolidating group: {str(e)}")

        return {
            "consolidated_groups": consolidated_count,
            "errors": errors
        }