import uuid


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_create_link(client, user_id):
    res = client.post(
        "/api/links",
        json={"original_url": "https://example.com/some/page", "user_id": user_id},
    )
    assert res.status_code == 201
    body = res.json()
    assert body["short_code"]
    assert body["is_active"] is True
    assert body["user_id"] == user_id


def test_create_link_unknown_user_returns_404(client):
    res = client.post(
        "/api/links",
        json={"original_url": "https://example.com", "user_id": str(uuid.uuid4())},
    )
    assert res.status_code == 404


def test_create_link_invalid_url_returns_422(client, user_id):
    res = client.post(
        "/api/links",
        json={"original_url": "not-a-valid-url", "user_id": user_id},
    )
    assert res.status_code == 422


def test_redirect_records_a_click(client, user_id):
    # Create a link
    created = client.post(
        "/api/links",
        json={"original_url": "https://example.com/target", "user_id": user_id},
    ).json()
    code = created["short_code"]

    # Hit the short link without following the redirect
    redirect = client.get(f"/{code}", follow_redirects=False)
    assert redirect.status_code == 307
    assert redirect.headers["location"] == "https://example.com/target"

    # Analytics should now show exactly one click
    analytics = client.get(f"/api/analytics/{code}").json()
    assert analytics["total_clicks"] == 1
    assert analytics["clicks_today"] == 1


def test_analytics_unknown_code_returns_404(client):
    res = client.get("/api/analytics/does-not-exist")
    assert res.status_code == 404


def test_create_link_with_custom_slug(client, user_id):
    res = client.post(
        "/api/links",
        json={
            "original_url": "https://example.com",
            "user_id": user_id,
            "custom_slug": "My-Cool-Link",  # mixed case -> sanitized to lowercase
        },
    )
    assert res.status_code == 201
    assert res.json()["custom_slug"] == "my-cool-link"


def test_duplicate_custom_slug_returns_409(client, user_id):
    slug = "unique-demo-slug"
    first = client.post(
        "/api/links",
        json={"original_url": "https://example.com", "user_id": user_id, "custom_slug": slug},
    )
    assert first.status_code == 201
    second = client.post(
        "/api/links",
        json={"original_url": "https://example.org", "user_id": user_id, "custom_slug": slug},
    )
    assert second.status_code == 409
    assert second.json()["detail"] == "Slug already taken."


def test_invalid_custom_slug_returns_422(client, user_id):
    res = client.post(
        "/api/links",
        json={"original_url": "https://example.com", "user_id": user_id, "custom_slug": "bad slug!"},
    )
    assert res.status_code == 422


def test_redirect_works_via_custom_slug(client, user_id):
    slug = "go-home-page"
    client.post(
        "/api/links",
        json={"original_url": "https://example.com/home", "user_id": user_id, "custom_slug": slug},
    )
    redirect = client.get(f"/{slug}", follow_redirects=False)
    assert redirect.status_code == 307
    assert redirect.headers["location"] == "https://example.com/home"
