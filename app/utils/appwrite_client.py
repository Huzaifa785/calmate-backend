# app/utils/appwrite_client.py
from appwrite.client import Client
from app.config import settings

def get_client() -> Client:
    client = Client()
    client.set_endpoint(settings.APPWRITE_ENDPOINT)
    client.set_project(settings.APPWRITE_PROJECT_ID)
    client.set_key(settings.APPWRITE_API_KEY)
    return client
