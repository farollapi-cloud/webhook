import uuid
from urllib.parse import urlparse

from fastapi.testclient import TestClient


def _path(url: str) -> str:
    return urlparse(url).path


def test_health(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_company_phone_webhook_flow(client: TestClient, auth_headers: dict[str, str]) -> None:
    # empresa
    r = client.post(
        "/api/v1/companies",
        json={
            "legal_name": "ACME LTDA",
            "contact_name": "João",
            "email": "joao@acme.com",
            "phone": "+5511988887777",
            "status": "active",
        },
        headers=auth_headers,
    )
    assert r.status_code == 201
    company_id = r.json()["id"]

    # número + webhook
    r2 = client.post(
        f"/api/v1/companies/{company_id}/phone-numbers",
        json={
            "label": "Vendas",
            "phone_e164": "+5511999999999",
            "uazapi_base_url": "https://uazapi.example.com/instance",
            "uazapi_instance_token": "secret-token-uazapi",
            "connection_status": "active",
        },
        headers=auth_headers,
    )
    assert r2.status_code == 201
    body = r2.json()
    phone_id = body["id"]
    assert body["webhook_url"] is not None
    assert "http://test.example/api/v1/webhooks/whatsapp/" in body["webhook_url"]
    assert body["webhook_url_prefix"].endswith(f"{company_id}/{phone_id}/")

    # estabilidade: GET não muda URL
    r3 = client.get(f"/api/v1/companies/{company_id}/phone-numbers/{phone_id}", headers=auth_headers)
    assert r3.status_code == 200
    assert r3.json()["webhook_url"] is None
    assert r3.json()["webhook_url_prefix"] == body["webhook_url_prefix"]

    # POST inbound
    webhook_url = body["webhook_url"]
    token = webhook_url.rstrip("/").split("/")[-1]
    r4 = client.post(_path(webhook_url), json={"event": "test", "id": "evt-1"})
    assert r4.status_code == 200
    assert r4.json()["received"] is True

    # token inválido → 404
    bad = webhook_url.replace(token, "x" * len(token))
    r5 = client.post(_path(bad), json={})
    assert r5.status_code == 404

    # regenerar
    r6 = client.post(
        f"/api/v1/companies/{company_id}/phone-numbers/{phone_id}/webhook/regenerate",
        headers=auth_headers,
    )
    assert r6.status_code == 200
    new_url = r6.json()["webhook_url"]
    assert new_url != webhook_url

    r7 = client.post(_path(webhook_url), json={"event": "old"})
    assert r7.status_code == 404

    r8 = client.post(_path(new_url), json={"event": "new"})
    assert r8.status_code == 200


def test_multi_tenant_isolation(client: TestClient, auth_headers: dict[str, str]) -> None:
    r = client.post(
        "/api/v1/companies",
        json={
            "legal_name": "B",
            "contact_name": "B",
            "email": "b@b.com",
            "phone": "+5511000000001",
        },
        headers=auth_headers,
    )
    cid = r.json()["id"]
    r2 = client.post(
        f"/api/v1/companies/{cid}/phone-numbers",
        json={
            "label": "x",
            "phone_e164": "+5511888888888",
            "uazapi_base_url": "https://uazapi.example.com/instance",
            "uazapi_instance_token": "t",
        },
        headers=auth_headers,
    )
    pid = r2.json()["id"]
    url = r2.json()["webhook_url"]
    fake_company = uuid.uuid4()
    wrong = url.replace(str(cid), str(fake_company))
    assert client.post(_path(wrong), json={}).status_code == 404
