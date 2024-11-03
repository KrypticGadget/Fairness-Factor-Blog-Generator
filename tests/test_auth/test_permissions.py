# tests/test_auth/test_permissions.py
import pytest
from auth.permissions import PermissionHandler

@pytest.fixture
async def permission_handler(test_db):
    return PermissionHandler(test_db)

@pytest.mark.asyncio
async def test_user_permissions(permission_handler):
    # Test default user permissions
    permissions = await permission_handler.get_user_permissions('user_id')
    assert 'read:content' in permissions
    assert 'write:content' in permissions
    
    # Test admin permissions
    admin_permissions = await permission_handler.get_user_permissions('admin_id')
    assert '*' in admin_permissions

@pytest.mark.asyncio
async def test_permission_checks(permission_handler):
    # Add test permission
    await permission_handler.add_permission('user_id', 'test:permission')
    
    # Check permission
    has_permission = await permission_handler.check_permission('user_id', 'test:permission')
    assert has_permission is True
    
    # Remove permission
    await permission_handler.remove_permission('user_id', 'test:permission')
    
    # Check removed permission
    has_permission = await permission_handler.check_permission('user_id', 'test:permission')
    assert has_permission is False