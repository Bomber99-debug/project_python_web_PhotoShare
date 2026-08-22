from tests.conftest import TEST_PASSWORD


async def test_first_registered_user_is_admin_and_next_is_user(
    client,
    register_user,
):
    first = await register_user(
        client,
        username="first",
        email="first@example.com",
    )

    second = await register_user(
        client,
        username="second",
        email="second@example.com",
    )

    assert first.status_code == 201
    assert second.status_code == 201

    assert first.json()["role"] == "admin"
    assert second.json()["role"] == "user"


async def test_register_duplicate_email(
    client,
    register_user,
):
    first = await register_user(
        client,
        username="first",
        email="same@example.com",
    )

    duplicate = await register_user(
        client,
        username="second",
        email="same@example.com",
    )

    assert first.status_code == 201
    assert duplicate.status_code == 400
    assert duplicate.json()["detail"] == "Email already registered"


async def test_register_duplicate_username(
    client,
    register_user,
):
    first = await register_user(
        client,
        username="same",
        email="first@example.com",
    )

    duplicate = await register_user(
        client,
        username="same",
        email="second@example.com",
    )

    assert first.status_code == 201
    assert duplicate.status_code == 400
    assert duplicate.json()["detail"] == "Username already taken"


async def test_login_by_username_and_email(
    client,
    register_user,
    login_user,
):
    await register_user(
        client,
        username="john",
        email="john@example.com",
    )

    by_username = await login_user(
        client,
        identity="john",
    )

    by_email = await login_user(
        client,
        identity="john@example.com",
    )

    assert by_username.status_code == 200
    assert by_email.status_code == 200

    assert "access_token" in by_username.json()
    assert "access_token" in by_email.json()

    assert by_username.json()["token_type"] == "bearer"


async def test_login_wrong_password(
    client,
    register_user,
    login_user,
):
    await register_user(
        client,
        username="john",
        email="john@example.com",
    )

    response = await login_user(
        client,
        identity="john",
        password="WrongPassword123!",
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username/email or password"


async def test_login_unknown_user(
    client,
    login_user,
):
    response = await login_user(
        client,
        identity="missing",
    )

    assert response.status_code == 401


async def test_get_current_user(
    client,
    user,
    user_headers,
):
    response = await client.get(
        "/api/users/me",
        headers=user_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == user["id"]
    assert data["username"] == user["username"]
    assert data["email"] == user["email"]
    assert data["role"] == "user"
    assert data["is_active"] is True


async def test_invalid_access_token(
    client,
):
    response = await client.get(
        "/api/users/me",
        headers={
            "Authorization": "Bearer definitely-not-a-jwt",
        },
    )

    assert response.status_code == 401


async def test_logout_blacklists_access_token(
    client,
    user_headers,
):
    before_logout = await client.get(
        "/api/users/me",
        headers=user_headers,
    )

    assert before_logout.status_code == 200

    logout = await client.post(
        "/api/auth/logout",
        headers=user_headers,
    )

    assert logout.status_code == 204

    after_logout = await client.get(
        "/api/users/me",
        headers=user_headers,
    )

    assert after_logout.status_code == 401


async def test_update_own_profile(
    client,
    user_headers,
):
    response = await client.put(
        "/api/users/me",
        headers=user_headers,
        json={
            "username": "renamed",
            "email": "renamed@example.com",
            "avatar_url": "https://example.com/avatar.jpg",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["username"] == "renamed"
    assert data["email"] == "renamed@example.com"
    assert data["avatar_url"] == "https://example.com/avatar.jpg"


async def test_update_password(
    client,
    user,
    user_headers,
    login_user,
):
    new_password = "NewPassword123!"

    response = await client.put(
        "/api/users/me",
        headers=user_headers,
        json={
            "password": new_password,
        },
    )

    assert response.status_code == 200

    old_login = await login_user(
        client,
        identity=user["username"],
        password=TEST_PASSWORD,
    )

    new_login = await login_user(
        client,
        identity=user["username"],
        password=new_password,
    )

    assert old_login.status_code == 401
    assert new_login.status_code == 200


async def test_update_profile_without_changes(
    client,
    user_headers,
):
    response = await client.put(
        "/api/users/me",
        headers=user_headers,
        json={},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "No fields to update"


async def test_update_profile_duplicate_email(
    client,
    admin,
    user_headers,
):
    response = await client.put(
        "/api/users/me",
        headers=user_headers,
        json={
            "email": admin["email"],
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


async def test_update_profile_duplicate_username(
    client,
    admin,
    user_headers,
):
    response = await client.put(
        "/api/users/me",
        headers=user_headers,
        json={
            "username": admin["username"],
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Username already taken"


async def test_public_profile(
    client,
    user,
):
    response = await client.get(
        f"/api/users/{user['username']}",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == user["id"]
    assert data["username"] == user["username"]
    assert data["uploaded_photos_count"] == 0


async def test_public_profile_contains_photo_count(
    client,
    user,
    user_headers,
    create_photo,
):
    await create_photo(
        client,
        user_headers,
        description="First",
    )

    await create_photo(
        client,
        user_headers,
        description="Second",
    )

    response = await client.get(
        f"/api/users/{user['username']}",
    )

    assert response.status_code == 200
    assert response.json()["uploaded_photos_count"] == 2


async def test_public_profile_not_found(
    client,
):
    response = await client.get(
        "/api/users/does-not-exist",
    )

    assert response.status_code == 404


async def test_admin_can_ban_and_unban_user(
    client,
    user,
    user_headers,
    admin_headers,
    login_user,
):
    ban = await client.patch(
        f"/api/users/{user['id']}/ban",
        headers=admin_headers,
    )

    assert ban.status_code == 200
    assert ban.json()["is_active"] is False

    old_token_request = await client.get(
        "/api/users/me",
        headers=user_headers,
    )

    assert old_token_request.status_code == 401

    login_while_banned = await login_user(
        client,
        identity=user["username"],
    )

    assert login_while_banned.status_code == 401
    assert login_while_banned.json()["detail"] == "Inactive user account"

    unban = await client.patch(
        f"/api/users/{user['id']}/unban",
        headers=admin_headers,
    )

    assert unban.status_code == 200
    assert unban.json()["is_active"] is True

    login_after_unban = await login_user(
        client,
        identity=user["username"],
    )

    assert login_after_unban.status_code == 200


async def test_admin_can_change_role(
    client,
    user,
    admin_headers,
):
    response = await client.patch(
        f"/api/users/{user['id']}/role",
        headers=admin_headers,
        json={
            "role": "moderator",
        },
    )

    assert response.status_code == 200
    assert response.json()["role"] == "moderator"


async def test_normal_user_cannot_ban_users(
    client,
    admin,
    user_headers,
):
    response = await client.patch(
        f"/api/users/{admin['id']}/ban",
        headers=user_headers,
    )

    assert response.status_code == 403


async def test_admin_actions_for_missing_user(
    client,
    admin_headers,
):
    ban = await client.patch(
        "/api/users/999999/ban",
        headers=admin_headers,
    )

    unban = await client.patch(
        "/api/users/999999/unban",
        headers=admin_headers,
    )

    role = await client.patch(
        "/api/users/999999/role",
        headers=admin_headers,
        json={
            "role": "moderator",
        },
    )

    assert ban.status_code == 404
    assert unban.status_code == 404
    assert role.status_code == 404