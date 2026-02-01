"""Unit tests for EmbeddingService."""

import pytest
import numpy as np
from unittest.mock import Mock, MagicMock, patch, AsyncMock


class TestEmbeddingService:
    """Tests for EmbeddingService class."""

    @pytest.fixture
    def mock_sentence_transformer(self):
        """Create a mock SentenceTransformer model."""
        mock_model = MagicMock()
        mock_model.encode = MagicMock(return_value=np.array([0.1] * 384))
        mock_model.get_sentence_embedding_dimension = MagicMock(return_value=384)
        return mock_model

    @pytest.fixture
    def embedding_service(self, mock_sentence_transformer):
        """Create an EmbeddingService with mocked model."""
        with patch('app.search.embeddings.SentenceTransformer', return_value=mock_sentence_transformer):
            from app.search.embeddings import EmbeddingService
            service = EmbeddingService("test-model")
            return service

    def test_embedding_service_initialization(self, mock_sentence_transformer):
        """Test EmbeddingService initialization with lazy loading."""
        with patch('app.search.embeddings.SentenceTransformer') as mock_st:
            from app.search.embeddings import EmbeddingService
            service = EmbeddingService("all-MiniLM-L6-v2")
            
            assert service.model_name == "all-MiniLM-L6-v2"
            assert service.model is None  # Lazy loading - not loaded yet
            mock_st.assert_not_called()

    def test_ensure_model_loaded(self, mock_sentence_transformer):
        """Test that _ensure_model_loaded loads the model."""
        with patch('app.search.embeddings.SentenceTransformer', return_value=mock_sentence_transformer) as mock_st:
            from app.search.embeddings import EmbeddingService
            service = EmbeddingService("test-model")
            
            assert service.model is None
            model = service._ensure_model_loaded()
            
            assert model is not None
            mock_st.assert_called_once_with("test-model")
            assert service.model == mock_sentence_transformer

    def test_ensure_model_loaded_only_once(self, mock_sentence_transformer):
        """Test that model is only loaded once."""
        with patch('app.search.embeddings.SentenceTransformer', return_value=mock_sentence_transformer) as mock_st:
            from app.search.embeddings import EmbeddingService
            service = EmbeddingService("test-model")
            
            # Call multiple times
            service._ensure_model_loaded()
            service._ensure_model_loaded()
            service._ensure_model_loaded()
            
            # Model should only be loaded once
            mock_st.assert_called_once()

    @pytest.mark.asyncio
    async def test_encode_text_single_string(self, mock_sentence_transformer):
        """Test encoding a single text string."""
        mock_sentence_transformer.encode.return_value = np.array([0.1, 0.2, 0.3])
        
        with patch('app.search.embeddings.SentenceTransformer', return_value=mock_sentence_transformer):
            from app.search.embeddings import EmbeddingService
            service = EmbeddingService("test-model")
            
            result = await service.encode_text("Hello world")
            
            mock_sentence_transformer.encode.assert_called_once_with("Hello world")
            assert result == [0.1, 0.2, 0.3]
            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_encode_text_list_of_strings(self, mock_sentence_transformer):
        """Test encoding a list of text strings."""
        mock_sentence_transformer.encode.return_value = np.array([
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6]
        ])
        
        with patch('app.search.embeddings.SentenceTransformer', return_value=mock_sentence_transformer):
            from app.search.embeddings import EmbeddingService
            service = EmbeddingService("test-model")
            
            texts = ["Hello", "World"]
            result = await service.encode_text(texts)
            
            mock_sentence_transformer.encode.assert_called_once_with(texts)
            assert len(result) == 2
            assert result[0] == [0.1, 0.2, 0.3]
            assert result[1] == [0.4, 0.5, 0.6]

    @pytest.mark.asyncio
    async def test_encode_query(self, mock_sentence_transformer):
        """Test encoding a search query."""
        mock_sentence_transformer.encode.return_value = np.array([0.1] * 384)
        
        with patch('app.search.embeddings.SentenceTransformer', return_value=mock_sentence_transformer):
            from app.search.embeddings import EmbeddingService
            service = EmbeddingService("test-model")
            
            result = await service.encode_query("search query")
            
            assert isinstance(result, list)
            assert len(result) == 384

    def test_get_embedding_dimension(self, mock_sentence_transformer):
        """Test getting embedding dimension."""
        mock_sentence_transformer.get_sentence_embedding_dimension.return_value = 384
        
        with patch('app.search.embeddings.SentenceTransformer', return_value=mock_sentence_transformer):
            from app.search.embeddings import EmbeddingService
            service = EmbeddingService("test-model")
            
            dim = service.get_embedding_dimension()
            
            assert dim == 384
            mock_sentence_transformer.get_sentence_embedding_dimension.assert_called_once()

    def test_get_embedding_dimension_none_raises(self, mock_sentence_transformer):
        """Test that None dimension raises RuntimeError."""
        mock_sentence_transformer.get_sentence_embedding_dimension.return_value = None
        
        with patch('app.search.embeddings.SentenceTransformer', return_value=mock_sentence_transformer):
            from app.search.embeddings import EmbeddingService
            service = EmbeddingService("test-model")
            
            with pytest.raises(RuntimeError, match="Unable to determine embedding dimension"):
                service.get_embedding_dimension()

    @pytest.mark.asyncio
    async def test_encode_empty_string(self, mock_sentence_transformer):
        """Test encoding an empty string."""
        mock_sentence_transformer.encode.return_value = np.array([0.0] * 384)
        
        with patch('app.search.embeddings.SentenceTransformer', return_value=mock_sentence_transformer):
            from app.search.embeddings import EmbeddingService
            service = EmbeddingService("test-model")
            
            result = await service.encode_text("")
            
            assert isinstance(result, list)
            mock_sentence_transformer.encode.assert_called_once_with("")

    @pytest.mark.asyncio
    async def test_encode_long_text(self, mock_sentence_transformer):
        """Test encoding a very long text."""
        long_text = "word " * 1000
        mock_sentence_transformer.encode.return_value = np.array([0.1] * 384)
        
        with patch('app.search.embeddings.SentenceTransformer', return_value=mock_sentence_transformer):
            from app.search.embeddings import EmbeddingService
            service = EmbeddingService("test-model")
            
            result = await service.encode_text(long_text)
            
            assert isinstance(result, list)
            mock_sentence_transformer.encode.assert_called_once()

    def test_custom_model_name(self, mock_sentence_transformer):
        """Test using a custom model name."""
        with patch('app.search.embeddings.SentenceTransformer', return_value=mock_sentence_transformer) as mock_st:
            from app.search.embeddings import EmbeddingService
            service = EmbeddingService("custom-embeddings-model")
            service._ensure_model_loaded()
            
            mock_st.assert_called_once_with("custom-embeddings-model")

    def test_executor_cleanup(self, mock_sentence_transformer):
        """Test that executor is properly managed."""
        with patch('app.search.embeddings.SentenceTransformer', return_value=mock_sentence_transformer):
            from app.search.embeddings import EmbeddingService
            service = EmbeddingService("test-model")
            
            assert hasattr(service, 'executor')
            assert service.executor is not None

    @pytest.mark.asyncio
    async def test_encode_text_returns_list_not_numpy(self, mock_sentence_transformer):
        """Test that encode_text returns Python list, not numpy array."""
        mock_sentence_transformer.encode.return_value = np.array([0.1, 0.2, 0.3])
        
        with patch('app.search.embeddings.SentenceTransformer', return_value=mock_sentence_transformer):
            from app.search.embeddings import EmbeddingService
            service = EmbeddingService("test-model")
            
            result = await service.encode_text("test")
            
            assert isinstance(result, list)
            assert not isinstance(result, np.ndarray)

    @pytest.mark.asyncio  
    async def test_encode_batch_returns_list_of_lists(self, mock_sentence_transformer):
        """Test that batch encoding returns list of lists."""
        mock_sentence_transformer.encode.return_value = np.array([
            [0.1, 0.2],
            [0.3, 0.4]
        ])
        
        with patch('app.search.embeddings.SentenceTransformer', return_value=mock_sentence_transformer):
            from app.search.embeddings import EmbeddingService
            service = EmbeddingService("test-model")
            
            result = await service.encode_text(["text1", "text2"])
            
            assert isinstance(result, list)
            assert all(isinstance(item, list) for item in result)
