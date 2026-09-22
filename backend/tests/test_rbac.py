import uuid


# ============================================================
# REGISTER VIEWER
# ============================================================

def test_register_viewer(client):

    unique_id = uuid.uuid4().hex[:8]

    response = client.post(
        "/auth/register",
        json={
            "username": f"viewer_{unique_id}",
            "email": f"viewer_{unique_id}@example.com",
            "password": "password123",
            "role": "viewer"
        }
    )

    assert response.status_code == 200

    body = response.json()

    assert body["role"] == "viewer"


# ============================================================
# LOGIN
# ============================================================

def test_login_returns_token(client):

    unique_id = uuid.uuid4().hex[:8]

    username = f"loginuser_{unique_id}"
    email = f"login_{unique_id}@example.com"

    register_response = client.post(
        "/auth/register",
        json={
            "username": username,
            "email": email,
            "password": "password123",
            "role": "viewer"
        }
    )

    assert register_response.status_code == 200

    response = client.post(
        "/auth/login",
        data={
            "username": username,
            "password": "password123"
        }
    )

    assert response.status_code == 200

    body = response.json()

    assert body["token_type"] == "bearer"

    assert body["access_token"]

    assert body["user"]["role"] == "viewer"


# ============================================================
# /AUTH/ME REQUIRES AUTHENTICATION
# ============================================================

def test_me_requires_authentication(client):

    from auth.dependencies import get_current_user

    # Remove test authentication override.
    client.app.dependency_overrides.pop(
        get_current_user,
        None
    )

    response = client.get(
        "/auth/me"
    )

    assert response.status_code == 401


# ============================================================
# VIEWER CAN READ TICKETS
# ============================================================

def test_viewer_can_read_tickets(client):

    unique_id = uuid.uuid4().hex[:8]

    username = f"reader_{unique_id}"
    email = f"reader_{unique_id}@example.com"

    register_response = client.post(
        "/auth/register",
        json={
            "username": username,
            "email": email,
            "password": "password123",
            "role": "viewer"
        }
    )

    assert register_response.status_code == 200

    login = client.post(
        "/auth/login",
        data={
            "username": username,
            "password": "password123"
        }
    )

    assert login.status_code == 200

    token = login.json()["access_token"]

    response = client.get(
        "/tickets",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200


# ============================================================
# VIEWER CANNOT INVESTIGATE
# ============================================================

def test_viewer_cannot_investigate(client):

    from auth.dependencies import get_current_user

    class ViewerUser:
        id = 1000
        username = "test_viewer"
        email = "viewer@test.com"
        role = "viewer"
        is_active = True

    # --------------------------------------------------------
    # IMPORTANT
    # --------------------------------------------------------
    # Force the authentication dependency to return
    # a viewer.
    #
    # The /investigate endpoint must then reject the
    # request with HTTP 403.
    # --------------------------------------------------------

    client.app.dependency_overrides[
        get_current_user
    ] = lambda: ViewerUser()

    response = client.post(
        "/tickets/1/investigate"
    )

    assert response.status_code == 403

    assert response.json()["detail"] == (
        "You do not have permission to perform this action"
    )