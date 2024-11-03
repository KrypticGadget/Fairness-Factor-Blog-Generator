# tests/test_mongodb.py
import pytest
from unittest.mock import Mock, patch
import os
from datetime import datetime
from bson import ObjectId
from database.mongo_manager import AsyncMongoManager, get_db_session
from utils.data_handlers import AsyncBlogContentHandler

@pytest.fixture
def mock_mongo_client():
    with patch('motor.motor_asyncio.AsyncIOMotorClient') as mock_client:
        mock_db = Mock()
        mock_fs = Mock()
        mock_client.return_value.fairness_factor_blog = mock_db
        mock_client.return_value.admin.command = Mock()
        yield mock_client, mock_db, mock_fs

@pytest.fixture
def mock_db_context(mock_mongo_client):
    mock_client, mock_db, mock_fs = mock_mongo_client
    with patch('database.mongo_manager.AsyncMongoManager') as mock_manager:
        mock_manager.return_value.get_connection.return_value = (mock_client, mock_db, mock_fs)
        yield mock_db

class TestAsyncMongoManager:
    def test_singleton_instance(self):
        manager1 = AsyncMongoManager()
        manager2 = AsyncMongoManager()
        assert manager1 is manager2

    def test_connection_error_handling(self, mock_mongo_client):
        mock_client, _, _ = mock_mongo_client
        mock_client.side_effect = Exception("Connection failed")
        
        with pytest.raises(Exception) as exc_info:
            AsyncMongoManager()
        assert "Connection failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_initialize(self, mock_db_context):
        manager = AsyncMongoManager()
        client, db = await manager.initialize()
        assert client is not None
        assert db is not None

    @pytest.mark.asyncio
    async def test_create_indexes(self, mock_db_context):
        manager = AsyncMongoManager()
        await manager.initialize()
        await manager._create_indexes()
        assert mock_db_context.users.create_index.called
        assert mock_db_context.sessions.create_index.called
        assert mock_db_context.audit_logs.create_index.called

class TestAsyncBlogContentHandler:
    @pytest.fixture
    def blog_handler(self, mock_db_context):
        return AsyncBlogContentHandler(mock_db_context)

    @pytest.mark.asyncio
    async def test_save_research(self, blog_handler, mock_db_context):
        mock_db_context.blog_content.insert_one.return_value = Mock(inserted_id=ObjectId())
        
        result = await blog_handler.save_content(
            user_email="test@fairnessfactor.com",
            content_type="research",
            content="test content",
            metadata={"analysis": "test analysis"}
        )
        
        assert isinstance(result, str)
        assert mock_db_context.blog_content.insert_one.called

    @pytest.mark.asyncio
    async def test_get_user_content(self, blog_handler, mock_db_context):
        expected_content = [{"_id": ObjectId(), "content": "test"}]
        mock_db_context.blog_content.find.return_value.sort.return_value = expected_content
        
        result = await blog_handler.get_user_content("test@fairnessfactor.com")
        
        assert result == expected_content
        assert mock_db_context.blog_content.find.called

# Add more test classes and methods as needed
