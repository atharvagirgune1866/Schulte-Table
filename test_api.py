import os, sys, tempfile
os.environ["SCHULTE_DB"] = os.path.join(tempfile.mkdtemp(), "test.db")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import app as schulte


@pytest.fixture
def client():
    return schulte.app.test_client()


GOOD = {"player": "Tester", "size": 5, "mode": "classic", "time": 30.0, "mistakes": 1, "splits": [1, 2]}


def test_pages_served(client):
    assert client.get("/").status_code == 200
    for f in ("style.css", "script.js", "api.js", "config.js"):
        assert client.get("/" + f).status_code == 200


def test_health(client):
    assert client.get("/api/health").get_json() == {"ok": True}


def test_submit_and_leaderboard(client):
    r = client.post("/api/scores", json=GOOD)
    assert r.status_code == 201 and r.get_json()["final_score"] == 32.0
    board = client.get("/api/leaderboard?size=5&mode=classic").get_json()
    assert board and board[0]["rank"] == 1


@pytest.mark.parametrize("patch", [{"time": 0.5}, {"size": 9}, {"mode": "x"}, {"mistakes": -1}])
def test_rejects_bad_input(client, patch):
    assert client.post("/api/scores", json={**GOOD, **patch}).status_code == 400


def test_name_is_trimmed(client):
    client.post("/api/scores", json={**GOOD, "player": "  " + "A" * 40})
    assert client.get("/api/stats?player=" + "A" * 20).get_json()["summary"]


def test_cors_header(client):
    assert "Access-Control-Allow-Origin" in client.get("/api/health").headers
