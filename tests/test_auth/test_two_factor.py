import pytest
from unittest.mock import AsyncMock, patch
from auth.two_factor import TwoFactorAuth

@pytest.fixture
def mock_db():
    return AsyncMock()

@pytest.fixture
def two_factor_auth(mock_db):
    return TwoFactorAuth(mock_db)

@pytest.mark.asyncio
async def test_enable_2fa(two_factor_auth):
    user_id = "test_user_id"
    with patch.object(two_factor_auth, 'generate_secret', return_value="test_secret"):
        with patch.object(two_factor_auth, 'encrypt_secret', return_value="encrypted_secret"):
            result = await two_factor_auth.enable_2fa(user_id)
            assert result['secret'] == "test_secret"
            assert "qr_code" in result

@pytest.mark.asyncio
async def test_verify_2fa(two_factor_auth):
    user_id = "test_user_id"
    token = "123456"
    with patch.object(two_factor_auth, 'decrypt_secret', return_value="test_secret"):
        with patch("pyotp.TOTP.verify", return_value=True):
            result = await two_factor_auth.verify_2fa(user_id, token)
            assert result is True

@pytest.mark.asyncio
async def test_disable_2fa(two_factor_auth):
    user_id = "test_user_id"
    result = await two_factor_auth.disable_2fa(user_id)
    assert result is True
