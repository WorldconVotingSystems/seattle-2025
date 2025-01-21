import base64

import pytest


# Use the `client` fixture provided by pytest-django to test views
@pytest.mark.django_db
def test_valid_params(client):
    # Mock valid base64-encoded IV and ciphertext
    iv = base64.b64encode(b"1234567890123456").decode("utf-8")  # Example 16-byte IV
    ciphertext = base64.b64encode(b"encrypted-data").decode("utf-8")

    response = client.get(
        "/controll-redirect/",
        {"iv": iv, "r": ciphertext},
    )

    assert response.status_code == 200
    assert (
        "You're at the Seattle 2025 app controll redirect."
        in response.content.decode("utf-8")
    )


@pytest.mark.django_db
def test_missing_iv(client):
    ciphertext = base64.b64encode(b"encrypted-data").decode("utf-8")  # Valid ciphertext

    response = client.get("/controll-redirect/", {"r": ciphertext})

    assert response.status_code == 400
    assert "Missing iv parameter" in response.content.decode("utf-8")


@pytest.mark.django_db
def test_invalid_base64_iv(client):
    iv = "not-a-base64-string"  # Invalid base64
    ciphertext = base64.b64encode(b"encrypted-data").decode("utf-8")  # Valid ciphertext

    response = client.get(
        "/controll-redirect/",
        {"iv": iv, "r": ciphertext},
    )

    assert response.status_code == 400
    assert "Invalid base64 encoding" in response.content.decode("utf-8")


@pytest.mark.django_db
def test_invalid_iv_length(client):
    iv = base64.b64encode(b"short-iv").decode("utf-8")  # Invalid IV length
    ciphertext = base64.b64encode(b"encrypted-data").decode("utf-8")  # Valid ciphertext

    response = client.get(
        "/controll-redirect/",
        {"iv": iv, "r": ciphertext},
    )

    assert response.status_code == 400
    assert "Invalid IV length" in response.content.decode("utf-8")
