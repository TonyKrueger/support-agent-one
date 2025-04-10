import unittest
from unittest.mock import patch, MagicMock
import json

from app.services.search_utils import (
    get_embedding,
    search_documents,
    format_search_results,
    search_and_format_query,
    store_document
)

class TestSearchUtils(unittest.TestCase):
    def setUp(self):
        # Mock embedding vector for tests
        self.mock_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        # Sample documents for tests
        self.sample_documents = [
            {
                "id": "doc1",
                "content": "This is a test document about customer support",
                "metadata": {"source": "knowledge_base", "category": "support"},
                "similarity": 0.89
            },
            {
                "id": "doc2",
                "content": "How to reset your password in the application",
                "metadata": {"source": "faq", "category": "account"},
                "similarity": 0.78
            }
        ]

    @patch('app.services.search_utils.openai.embeddings.create')
    def test_get_embedding(self, mock_create):
        # Setup mock
        embedding_response = MagicMock()
        embedding_response.data = [MagicMock(embedding=self.mock_embedding)]
        mock_create.return_value = embedding_response
        
        # Call function
        result = get_embedding("Test query")
        
        # Assert
        mock_create.assert_called_once_with(
            model="text-embedding-3-small",
            input="Test query"
        )
        self.assertEqual(result, self.mock_embedding)

    @patch('app.services.search_utils.get_embedding')
    @patch('app.services.search_utils.supabase.rpc')
    def test_search_documents(self, mock_rpc, mock_get_embedding):
        # Setup mocks
        mock_get_embedding.return_value = self.mock_embedding
        
        mock_execute = MagicMock()
        mock_execute.execute.return_value = MagicMock(data=self.sample_documents)
        
        mock_eq = MagicMock(return_value=mock_execute)
        mock_rpc.return_value = MagicMock(eq=mock_eq)
        
        # Call function with filters
        query = "How to reset password"
        filters = {"type": "faq"}
        result = search_documents(query, filters, limit=2)
        
        # Assert
        mock_get_embedding.assert_called_once_with(query)
        mock_rpc.assert_called_once_with(
            "match_documents",
            {
                "query_embedding": self.mock_embedding,
                "match_threshold": 0.7,
                "match_count": 2
            }
        )
        self.assertEqual(result, self.sample_documents)

    def test_format_search_results(self):
        # Call function
        result = format_search_results(self.sample_documents, "test query")
        
        # Assert result contains document content
        self.assertIn("This is a test document about customer support", result)
        self.assertIn("How to reset your password", result)
        
        # Assert result contains metadata
        self.assertIn("source: knowledge_base", result)
        self.assertIn("category: support", result)
        self.assertIn("source: faq", result)
        self.assertIn("category: account", result)
        
        # Test with empty documents
        empty_result = format_search_results([], "empty query")
        self.assertEqual(empty_result, "No relevant documentation found.")

    @patch('app.services.search_utils.search_documents')
    @patch('app.services.search_utils.format_search_results')
    def test_search_and_format_query(self, mock_format, mock_search):
        # Setup mocks
        mock_search.return_value = self.sample_documents
        mock_format.return_value = "Formatted search results"
        
        # Call function
        result = search_and_format_query("test query", limit=2)
        
        # Assert
        mock_search.assert_called_once_with("test query", None, 2)
        mock_format.assert_called_once_with(self.sample_documents, "test query")
        self.assertEqual(result, "Formatted search results")
        
        # Test exception handling
        mock_search.side_effect = Exception("Test error")
        error_result = search_and_format_query("error query")
        self.assertIn("Error retrieving relevant information", error_result)
        self.assertIn("Test error", error_result)

    @patch('app.services.search_utils.get_embedding')
    @patch('app.services.search_utils.supabase.table')
    def test_store_document(self, mock_table, mock_get_embedding):
        # Setup mocks
        mock_get_embedding.return_value = self.mock_embedding
        
        mock_execute = MagicMock()
        mock_execute.execute.return_value = MagicMock(
            data=[{"id": "new_doc_id", "content": "Test content"}]
        )
        
        mock_insert = MagicMock(return_value=mock_execute)
        mock_table.return_value = MagicMock(insert=mock_insert)
        
        # Call function
        content = "Test content for document storage"
        metadata = {"source": "test", "category": "unit_test"}
        result = store_document(content, "test_doc", metadata)
        
        # Assert
        mock_get_embedding.assert_called_once_with(content)
        mock_table.assert_called_once_with("documents")
        mock_insert.assert_called_once_with({
            "content": content,
            "embedding": self.mock_embedding,
            "type": "test_doc",
            "metadata": metadata
        })
        self.assertEqual(result["id"], "new_doc_id")

if __name__ == "__main__":
    unittest.main() 