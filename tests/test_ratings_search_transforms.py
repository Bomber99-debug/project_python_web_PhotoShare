async def test_rating_rules_and_average(
    client,
    admin,
    admin_headers,
    user_headers,
    other_user_headers,
    create_photo,
):
    photo = await create_photo(
        client,
        admin_headers,
        description="Admin photo",
    )

    first = await client.post(
        f"/api/photos/{photo['id']}/ratings",
        headers=user_headers,
        json={
            "value": 5,
        },
    )

    assert first.status_code == 201
    assert first.json()["value"] == 5

    duplicate = await client.post(
        f"/api/photos/{photo['id']}/ratings",
        headers=user_headers,
        json={
            "value": 4,
        },
    )

    assert duplicate.status_code == 400
    assert duplicate.json()["detail"] == "You have already rated this photo"

    own_rating = await client.post(
        f"/api/photos/{photo['id']}/ratings",
        headers=admin_headers,
        json={
            "value": 5,
        },
    )

    assert own_rating.status_code == 400
    assert own_rating.json()["detail"] == "You cannot rate your own photo"

    second = await client.post(
        f"/api/photos/{photo['id']}/ratings",
        headers=other_user_headers,
        json={
            "value": 3,
        },
    )

    assert second.status_code == 201

    summary = await client.get(
        f"/api/photos/{photo['id']}/ratings",
    )

    assert summary.status_code == 200

    data = summary.json()

    assert data["average_rating"] == 4.0
    assert data["ratings_count"] == 2


async def test_rating_value_validation(
    client,
    admin_headers,
    user_headers,
    create_photo,
):
    photo = await create_photo(
        client,
        admin_headers,
    )

    too_low = await client.post(
        f"/api/photos/{photo['id']}/ratings",
        headers=user_headers,
        json={
            "value": 0,
        },
    )

    too_high = await client.post(
        f"/api/photos/{photo['id']}/ratings",
        headers=user_headers,
        json={
            "value": 6,
        },
    )

    assert too_low.status_code == 422
    assert too_high.status_code == 422


async def test_rating_for_missing_photo(
    client,
    user_headers,
):
    create = await client.post(
        "/api/photos/999999/ratings",
        headers=user_headers,
        json={
            "value": 5,
        },
    )

    summary = await client.get(
        "/api/photos/999999/ratings",
    )

    assert create.status_code == 404
    assert summary.status_code == 404


async def test_only_moderator_or_admin_can_view_rating_details(
    client,
    admin_headers,
    user_headers,
    moderator,
    create_photo,
):
    photo = await create_photo(
        client,
        admin_headers,
    )

    await client.post(
        f"/api/photos/{photo['id']}/ratings",
        headers=user_headers,
        json={
            "value": 5,
        },
    )

    normal_user = await client.get(
        f"/api/photos/{photo['id']}/ratings/details",
        headers=user_headers,
    )

    moderator_response = await client.get(
        f"/api/photos/{photo['id']}/ratings/details",
        headers=moderator["headers"],
    )

    admin_response = await client.get(
        f"/api/photos/{photo['id']}/ratings/details",
        headers=admin_headers,
    )

    assert normal_user.status_code == 403
    assert moderator_response.status_code == 200
    assert admin_response.status_code == 200

    assert len(admin_response.json()) == 1


async def test_admin_can_delete_rating(
    client,
    admin_headers,
    user_headers,
    create_photo,
):
    photo = await create_photo(
        client,
        admin_headers,
    )

    created = await client.post(
        f"/api/photos/{photo['id']}/ratings",
        headers=user_headers,
        json={
            "value": 5,
        },
    )

    rating = created.json()

    forbidden = await client.delete(
        f"/api/ratings/{rating['id']}",
        headers=user_headers,
    )

    assert forbidden.status_code == 403

    deleted = await client.delete(
        f"/api/ratings/{rating['id']}",
        headers=admin_headers,
    )

    assert deleted.status_code == 200
    assert deleted.json()["message"] == "Rating deleted successfully"

    missing = await client.delete(
        "/api/ratings/999999",
        headers=admin_headers,
    )

    assert missing.status_code == 404


async def test_search_by_keyword(
    client,
    admin_headers,
    create_photo,
):
    first = await create_photo(
        client,
        admin_headers,
        description="Beautiful sunset over the sea",
    )

    await create_photo(
        client,
        admin_headers,
        description="Night city",
    )

    response = await client.get(
        "/api/photos/search",
        params={
            "keyword": "sunset",
        },
    )

    assert response.status_code == 200

    result = response.json()

    assert len(result) == 1
    assert result[0]["id"] == first["id"]


async def test_search_by_tag(
    client,
    admin_headers,
    create_photo,
):
    first = await create_photo(
        client,
        admin_headers,
        description="Nature",
        tag="Nature",
    )

    await create_photo(
        client,
        admin_headers,
        description="City",
        tag="city",
    )

    response = await client.get(
        "/api/photos/search",
        params={
            "tag": " NATURE ",
        },
    )

    assert response.status_code == 200

    result = response.json()

    assert len(result) == 1
    assert result[0]["id"] == first["id"]


async def test_search_filter_and_sort_by_rating(
    client,
    admin_headers,
    user_headers,
    create_photo,
):
    rated = await create_photo(
        client,
        admin_headers,
        description="Rated",
    )

    unrated = await create_photo(
        client,
        admin_headers,
        description="Unrated",
    )

    rating = await client.post(
        f"/api/photos/{rated['id']}/ratings",
        headers=user_headers,
        json={
            "value": 5,
        },
    )

    assert rating.status_code == 201

    filtered = await client.get(
        "/api/photos/search",
        params={
            "min_rating": 4,
        },
    )

    assert filtered.status_code == 200

    filtered_ids = [
        photo["id"]
        for photo in filtered.json()
    ]

    assert rated["id"] in filtered_ids
    assert unrated["id"] not in filtered_ids

    sorted_response = await client.get(
        "/api/photos/search",
        params={
            "sort_by": "rating",
            "order": "desc",
        },
    )

    assert sorted_response.status_code == 200
    assert sorted_response.json()[0]["id"] == rated["id"]


async def test_search_by_date_range(
    client,
    admin_headers,
    create_photo,
):
    await create_photo(
        client,
        admin_headers,
    )

    response = await client.get(
        "/api/photos/search",
        params={
            "date_from": "2000-01-01T00:00:00Z",
            "date_to": "2100-01-01T00:00:00Z",
        },
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


async def test_search_user_filter_requires_moderator_or_admin(
    client,
    admin,
    admin_headers,
    user_headers,
    create_photo,
):
    photo = await create_photo(
        client,
        admin_headers,
    )

    anonymous = await client.get(
        "/api/photos/search",
        params={
            "user_id": admin["id"],
        },
    )

    normal_user = await client.get(
        "/api/photos/search",
        params={
            "user_id": admin["id"],
        },
        headers=user_headers,
    )

    administrator = await client.get(
        "/api/photos/search",
        params={
            "user_id": admin["id"],
        },
        headers=admin_headers,
    )

    assert anonymous.status_code == 403
    assert normal_user.status_code == 403
    assert administrator.status_code == 200

    assert [
        item["id"]
        for item in administrator.json()
    ] == [
        photo["id"],
    ]


async def test_search_invalid_parameters(
    client,
):
    invalid_sort = await client.get(
        "/api/photos/search",
        params={
            "sort_by": "something",
        },
    )

    invalid_order = await client.get(
        "/api/photos/search",
        params={
            "order": "something",
        },
    )

    invalid_dates = await client.get(
        "/api/photos/search",
        params={
            "date_from": "2030-01-01T00:00:00Z",
            "date_to": "2020-01-01T00:00:00Z",
        },
    )

    empty_tag = await client.get(
        "/api/photos/search",
        params={
            "tag": "   ",
        },
    )

    assert invalid_sort.status_code == 400
    assert invalid_order.status_code == 400
    assert invalid_dates.status_code == 400
    assert empty_tag.status_code == 400


async def test_search_treats_invalid_optional_token_as_anonymous(
    client,
):
    response = await client.get(
        "/api/photos/search",
        headers={
            "Authorization": "Bearer invalid-token",
        },
    )

    assert response.status_code == 200


async def test_create_and_read_transformation(
    client,
    user_headers,
    create_photo,
    monkeypatch,
):
    photo = await create_photo(
        client,
        user_headers,
    )

    def fake_transformed_url(public_id, data):
        return (
            f"https://example.com/transformed/"
            f"{public_id}.jpg"
        )

    async def fake_qr_code(url):
        return "https://example.com/qr.png"

    monkeypatch.setattr(
        "src.routes.transforms.transformed_url",
        fake_transformed_url,
    )

    monkeypatch.setattr(
        "src.routes.transforms.generate_qr_code",
        fake_qr_code,
    )

    response = await client.post(
        f"/api/photos/{photo['id']}/transform",
        headers=user_headers,
        json={
            "width": 300,
            "effect": "sepia",
        },
    )

    assert response.status_code == 201

    transformed = response.json()

    assert transformed["photo_id"] == photo["id"]
    assert transformed["transformed_url"].startswith(
        "https://example.com/transformed/"
    )
    assert transformed["qr_code_url"] == "https://example.com/qr.png"

    listing = await client.get(
        f"/api/photos/{photo['id']}/transforms",
    )

    assert listing.status_code == 200
    assert len(listing.json()) == 1

    by_id = await client.get(
        f"/api/transforms/{transformed['id']}",
    )

    assert by_id.status_code == 200
    assert by_id.json()["id"] == transformed["id"]


async def test_transformation_requires_at_least_one_option(
    client,
    user_headers,
    create_photo,
):
    photo = await create_photo(
        client,
        user_headers,
    )

    response = await client.post(
        f"/api/photos/{photo['id']}/transform",
        headers=user_headers,
        json={},
    )

    assert response.status_code == 400


async def test_invalid_transformation_effect(
    client,
    user_headers,
    create_photo,
):
    photo = await create_photo(
        client,
        user_headers,
    )

    response = await client.post(
        f"/api/photos/{photo['id']}/transform",
        headers=user_headers,
        json={
            "effect": "nuclear_explosion",
        },
    )

    assert response.status_code == 422


async def test_other_user_cannot_transform_photo(
    client,
    user_headers,
    other_user_headers,
    create_photo,
):
    photo = await create_photo(
        client,
        user_headers,
    )

    response = await client.post(
        f"/api/photos/{photo['id']}/transform",
        headers=other_user_headers,
        json={
            "width": 300,
        },
    )

    assert response.status_code == 403


async def test_transformation_not_found_cases(
    client,
    user_headers,
):
    create = await client.post(
        "/api/photos/999999/transform",
        headers=user_headers,
        json={
            "width": 300,
        },
    )

    listing = await client.get(
        "/api/photos/999999/transforms",
    )

    by_id = await client.get(
        "/api/transforms/999999",
    )

    assert create.status_code == 404
    assert listing.status_code == 404
    assert by_id.status_code == 404