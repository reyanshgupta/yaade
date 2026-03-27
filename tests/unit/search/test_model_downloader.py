"""Unit tests for model_downloader (hub path resolution for all embedding models)."""

import pytest

from app.models.embedding_models import EMBEDDING_MODELS
from app.search.model_downloader import get_model_hub_path


class TestGetModelHubPath:
    """Verify get_model_hub_path returns correct HuggingFace org for every model."""

    @pytest.mark.parametrize("model", EMBEDDING_MODELS, ids=[m["id"] for m in EMBEDDING_MODELS])
    def test_every_embedding_model_has_correct_hub_path(self, model):
        """Each supported model must resolve to org/model_id with its declared hub_org."""
        model_id = model["id"]
        hub_org = model["hub_org"]
        expected = f"{hub_org}/{model_id}"
        assert get_model_hub_path(model_id) == expected, (
            f"{model_id} should load as {expected} (hub_org={hub_org})"
        )

    def test_bge_prefix_fallback_for_unknown_model(self):
        """Unknown model id starting with bge- falls back to BAAI."""
        assert get_model_hub_path("bge-custom-v1") == "BAAI/bge-custom-v1"

    def test_unknown_model_fallback_sentence_transformers(self):
        """Unknown model id without bge- falls back to sentence-transformers."""
        assert get_model_hub_path("some-other-model") == "sentence-transformers/some-other-model"

    def test_all_models_have_hub_org(self):
        """Every entry in EMBEDDING_MODELS must define hub_org for explicit resolution."""
        for model in EMBEDDING_MODELS:
            assert "hub_org" in model, f"Model {model['id']} missing hub_org"
            assert model["hub_org"] in ("sentence-transformers", "BAAI"), (
                f"Model {model['id']} has unexpected hub_org: {model['hub_org']}"
            )
