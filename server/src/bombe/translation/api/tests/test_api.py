from starlette.testclient import TestClient
from bombe.translation.api import app


def test_docs_redirect():
    client = TestClient(app)
    response = client.get("/")
    assert response.history[0].status_code == 302
    assert response.status_code == 200
    assert response.url == "http://testserver/docs"


def test_api():
    client = TestClient(app)

    text = """The doctor said I was fine, but ensure to rest."""

    request_data = dict(text=text, language='en')
    response = client.post("/translate", json=request_data)
    assert response.status_code == 200

    translated = response.json()
    assert translated['text'] == ("Dweddodd y doctor fod fi'n iawn, "
                                  'ond i sicrahau i ymlacio.')
    assert translated['language'] == 'cy'
