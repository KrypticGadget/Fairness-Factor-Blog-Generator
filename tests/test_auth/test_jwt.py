# tests/test_auth/test_jwt.py
import pytest
from datetime import datetime, timedelta
from auth.jwt_handler import JWTHandler
from config import settings

@pytest.fixture
async def jwt_handler(test_db):
    return JWTHandler(test_db)

@pytest.mark.asyncio
async def test_create_access_token(jwt_handler):
    user = {
        '_id': '123',
        'email': 'test@fairnessfactor.com',
        'role': 'user'
    }
    
    token = await jwt_handler.create_access_token(user)
    assert token is not None
    
    # Verify token
    payload = await jwt_handler.verify_access_token(token)
    assert payload is not None
    assert payload['user_id'] == '123'
    assert payload['email'] == 'test@fairnessfactor.com'
    assert payload['type'] == 'access'

@pytest.mark.asyncio
async def test_create_refresh_token(jwt_handler):
    user = {
        '_id': '123',
        'email': 'test@fairnessfactor.com',
        'role': 'user'
    }
    
    token = await jwt_handler.create_refresh_token(user)
    assert token is not None
    
    # Verify token
    payload = await jwt_handler.verify_refresh_token(token)
    assert payload is not None
    assert payload['user_id'] == '123'
    assert payload['type'] == 'refresh'

@pytest.mark.asyncio
async def test_verify_access_token(jwt_handler):
    user = {
        '_id': '123',
        'email': 'test@fairnessfactor.com',
        'role': 'user'
    }
    
    token = await jwt_handler.create_access_token(user)
    payload = await jwt_handler.verify_access_token(token)
    
    assert payload is not None
    assert payload['user_id'] == '123'
    assert payload['email'] == 'test@fairnessfactor.com'
    assert payload['type'] == 'access'

@pytest.mark.asyncio
async def test_verify_refresh_token(jwt_handler):
    user = {
        '_id': '123',
        'email': 'test@fairnessfactor.com',
        'role': 'user'
    }
    
    token = await jwt_handler.create_refresh_token(user)
    payload = await jwt_handler.verify_refresh_token(token)
    
    assert payload is not None
    assert payload['user_id'] == '123'
    assert payload['type'] == 'refresh'

@pytest.mark.asyncio
async def test_token_expiration(jwt_handler):
    user = {
        '_id': '123',
        'email': 'test@fairnessfactor.com',
        'role': 'user'
    }
    
    # Create token with short expiration
    jwt_handler.access_expire_minutes = 0
    token = await jwt_handler.create_access_token(user)
    
    # Wait for expiration
    await asyncio.sleep(1)
    
    # Verify expired token
    payload = await jwt_handler.verify_access_token(token)
    assert payload is None
