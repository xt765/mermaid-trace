import pytest
from logcapy.integrations.flask import LogCapyExtension
from flask import Flask, jsonify

app = Flask(__name__)
LogCapyExtension(app)

@app.route("/")
def index():
    return jsonify({"hello": "world"})

@app.route("/error")
def error():
    raise ValueError("Flask Boom")

@pytest.fixture
def client():
    return app.test_client()

def test_flask_extension_success(client, caplog):
    response = client.get("/")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert "GET /" in caplog.text

def test_flask_extension_error(client, caplog):
    # Flask propagates exceptions in testing mode by default, unless configured otherwise
    # But LogCapy catches unhandled exceptions in teardown_request which is called anyway?
    # Actually teardown_request is called after exception handling.
    # If Flask handles it (500), it might not reach teardown with exception unless we propagate?
    
    # We expect LogCapy to log the exception
    try:
        client.get("/error")
    except ValueError:
        pass
    
    assert "Flask Boom" in caplog.text
    assert "Unhandled exception" in caplog.text
