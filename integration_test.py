from server import app
from fastapi.testclient import TestClient

client = TestClient(app)

client.websocket_connect("/session")
