import uuid


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


# ---------------- Auth ----------------

def test_register_and_login_flow(client):
    email = f"u-{uuid.uuid4().hex[:10]}@example.com"
    reg = client.post("/api/register", json={"email": email, "password": "pw12345"})
    assert reg.status_code == 201
    assert reg.json()["email"] == email

    tok = client.post("/api/token", data={"username": email, "password": "pw12345"})
    assert tok.status_code == 200
    assert tok.json()["token_type"] == "bearer"
    assert tok.json()["access_token"]


def test_duplicate_email_rejected(client):
    email = f"dup-{uuid.uuid4().hex[:10]}@example.com"
    client.post("/api/register", json={"email": email, "password": "pw12345"})
    again = client.post("/api/register", json={"email": email, "password": "pw12345"})
    assert again.status_code == 400


def test_login_wrong_password_401(client):
    email = f"wp-{uuid.uuid4().hex[:10]}@example.com"
    client.post("/api/register", json={"email": email, "password": "correct-pw"})
    bad = client.post("/api/token", data={"username": email, "password": "wrong-pw"})
    assert bad.status_code == 401


# ---------------- Protected link endpoints ----------------

def test_create_link_requires_auth(client):
    res = client.post("/api/links", json={"original_url": "https://example.com"})
    assert res.status_code == 401


def test_list_links_requires_auth(client):
    res = client.get("/api/links")
    assert res.status_code == 401


def test_create_and_list_links_authenticated(auth_client):
    created = auth_client.post(
        "/api/links", json={"original_url": "https://example.com/page"}
    )
    assert created.status_code == 201
    assert created.json()["short_code"]

    links = auth_client.get("/api/links")
    assert links.status_code == 200
    assert any(l["short_code"] == created.json()["short_code"] for l in links.json())


def test_users_only_see_their_own_links(auth_client):
    # First user creates a link.
    mine = auth_client.post(
        "/api/links", json={"original_url": "https://example.com/mine"}
    ).json()
    # A second, separate authenticated client.
    from fastapi.testclient import TestClient
    from main import app
    other = TestClient(app)
    email = f"other-{uuid.uuid4().hex[:10]}@example.com"
    other.post("/api/register", json={"email": email, "password": "pw12345"})
    tok = other.post("/api/token", data={"username": email, "password": "pw12345"})
    other.headers.update({"Authorization": f"Bearer {tok.json()['access_token']}"})

    codes = [l["short_code"] for l in other.get("/api/links").json()]
    assert mine["short_code"] not in codes  # isolation between users


def test_create_link_invalid_url_returns_422(auth_client):
    res = auth_client.post("/api/links", json={"original_url": "not-a-valid-url"})
    assert res.status_code == 422


# ---------------- Custom slug ----------------

def test_create_link_with_custom_slug(auth_client):
    suffix = uuid.uuid4().hex[:8]
    res = auth_client.post(
        "/api/links",
        json={"original_url": "https://example.com", "custom_slug": f"My-Cool-{suffix}"},
    )
    assert res.status_code == 201
    assert res.json()["custom_slug"] == f"my-cool-{suffix}"


def test_duplicate_custom_slug_returns_409(auth_client):
    slug = "dup-" + uuid.uuid4().hex[:8]
    first = auth_client.post(
        "/api/links", json={"original_url": "https://example.com", "custom_slug": slug}
    )
    assert first.status_code == 201
    second = auth_client.post(
        "/api/links", json={"original_url": "https://example.org", "custom_slug": slug}
    )
    assert second.status_code == 409
    assert second.json()["detail"] == "Slug already taken."


# ---------------- Redirect + analytics (public) ----------------

def test_redirect_records_a_click(auth_client, client):
    created = auth_client.post(
        "/api/links", json={"original_url": "https://example.com/target"}
    ).json()
    code = created["short_code"]

    redirect = client.get(f"/{code}", follow_redirects=False)
    assert redirect.status_code == 307
    assert redirect.headers["location"] == "https://example.com/target"

    analytics = client.get(f"/api/analytics/{code}").json()
    assert analytics["total_clicks"] == 1


def test_redirect_works_via_custom_slug(auth_client, client):
    slug = "go-" + uuid.uuid4().hex[:8]
    auth_client.post(
        "/api/links", json={"original_url": "https://example.com/home", "custom_slug": slug}
    )
    redirect = client.get(f"/{slug}", follow_redirects=False)
    assert redirect.status_code == 307
    assert redirect.headers["location"] == "https://example.com/home"


def test_analytics_unknown_code_returns_404(client):
    res = client.get("/api/analytics/does-not-exist")
    assert res.status_code == 404


# ---------------- Open Graph preview for bots ----------------

def test_social_bot_gets_og_preview_not_redirect(auth_client, client):
    created = auth_client.post(
        "/api/links", json={"original_url": "https://example.com/article"}
    ).json()
    code = created["short_code"]

    res = client.get(
        f"/{code}",
        headers={"User-Agent": "WhatsApp/2.23 facebookexternalhit/1.1"},
        follow_redirects=False,
    )
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
    assert 'property="og:title"' in res.text
    assert "Syed Sulaiman Usman" in res.text

    analytics = client.get(f"/api/analytics/{code}").json()
    assert analytics["total_clicks"] == 0


def test_normal_browser_still_redirects(auth_client, client):
    created = auth_client.post(
        "/api/links", json={"original_url": "https://example.com/page2"}
    ).json()
    code = created["short_code"]
    res = client.get(
        f"/{code}",
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
        follow_redirects=False,
    )
    assert res.status_code == 307
    assert res.headers["location"] == "https://example.com/page2"
