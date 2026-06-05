import pytest
from unittest.mock import patch, MagicMock
from app.core.emailUtils import generateVerificationToken, sendVerificationEmail
from app.core.config import settingsInstance

@pytest.mark.smtp
def test_generate_verification_token():
    email = "test@example.com"
    token = generateVerificationToken(email)
    assert token is not None
    assert isinstance(token, str)
    from jose import jwt
    payload = jwt.decode(token, settingsInstance.secretKey, algorithms=[settingsInstance.algorithm])
    assert payload["sub"] == email
    assert payload["type"] == "verification"
    assert "exp" in payload

@pytest.mark.smtp
@patch("smtplib.SMTP_SSL")
def test_send_verification_email_success(mock_smtp_ssl):
    mock_server = MagicMock()
    mock_smtp_ssl.return_value.__enter__.return_value = mock_server
    settingsInstance.smtpHost = "smtp.mail.ru"
    settingsInstance.smtpPort = 465
    settingsInstance.smtpUser = "test@mail.ru"
    settingsInstance.smtpPassword = "testpass"
    try:
        sendVerificationEmail("recipient@example.com", "test-token", "http://localhost")
        mock_server.login.assert_called_once_with("test@mail.ru", "testpass")
        mock_server.send_message.assert_called_once()
    finally:
        settingsInstance.smtpHost = ""
        settingsInstance.smtpPort = 0
        settingsInstance.smtpUser = ""
        settingsInstance.smtpPassword = ""

@pytest.mark.smtp
def test_send_verification_email_no_smtp_config(capsys):
    settingsInstance.smtpHost = ""
    settingsInstance.smtpUser = ""
    sendVerificationEmail("test@example.com", "test-token", "http://localhost")
    captured = capsys.readouterr()
    assert "SMTP not configured" in captured.out