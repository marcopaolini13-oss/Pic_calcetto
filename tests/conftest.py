import pytest
import streamlit as st

def pytest_addoption(parser):
    parser.addoption('--postgres-container',default=None,help='Isolated PostgreSQL test container')

@pytest.fixture(autouse=True)
def isolate_local_credentials(monkeypatch):
    # Never use the organizer's local secrets file as test credentials.
    monkeypatch.setattr(st,'secrets',{})
