# tests/test_mongodb.py
import pytest
from unittest.mock import Mock, patch
import os
from datetime import datetime
from bson import ObjectId
from utils.mongo_manager import MongoManager, get_db_context
from utils.data_handlers import BlogContentHandler, FileHandler, SessionHandler, AnalyticsHandler

@pytest.fixture
def mock_mongo_client():
    with patch('pymongo.MongoClient') as mock_client:
        mock_db = Mock()
        mock_fs = Mock()
        mock_client.return_value.fairness_factor_blog = mock_db
        mock_client.return_value.admin.command = Mock()
        yield mock_client, mock_db, mock_fs

@pytest.fixture
def mock_db_context(mock_mongo_client):
    mock_client, mock_db, mock_fs = mock_mongo_client
    with patch('utils.mongo_manager.MongoManager') as mock_manager:
        mock_manager.return_value.get_connection.return_value = (mock_client, mock_db, mock_fs)
        yield mock_db

class TestMongoManager:
    def test_singleton_instance(self):
        manager1 = MongoManager()
        manager2 = MongoManager()
        assert manager1 is manager2

    def test_connection_error_handling(self, mock_mongo_client):
        mock_client, _, _ = mock_mongo_client
        mock_client.side_effect = Exception("Connection failed")
        
        with pytest.raises(Exception) as exc_info:
            MongoManager()
        assert "Connection failed" in str(exc_info.value)

class TestBlogContentHandler:
    @pytest.fixture
    def blog_handler(self, mock_db_context):
        return BlogContentHandler(mock_db_context)

    def test_save_research(self, blog_handler, mock_db_context):
        mock_db_context.blog_content.insert_one.return_value = Mock(inserted_id=ObjectId())
        
        result = blog_handler.save_research(
            user_email="test@fairnessfactor.com",
            document_contents=["test content"],
            analysis="test analysis"
        )
        
        assert isinstance(result, str)
        assert mock_db_context.blog_content.insert_one.called

    def test_get_user_content(self, blog_handler, mock_db_context):
        expected_content = [{"_id": ObjectId(), "content": "test"}]
        mock_db_context.blog_content.find.return_value.sort.return_value = expected_content
        
        result = blog_handler.get_user_content("test@fairnessfactor.com")
        
        assert result == expected_content
        assert mock_db_context.blog_content.find.called

# Add more test classes and methods as needed