import pytest
import unittest.mock as mock
from backend.core.client import get_cosmos_client, get_qdrant_client
from backend.services.llm_provider import _load_faq_text
from backend.schemas.chat import ChatRequest, ClientActionType

def test_global_client_caching():
    with mock.patch("backend.core.client.config") as mock_cfg:
        mock_cfg.COSMOS_ENDPOINT = "https://localhost:8081"
        mock_cfg.COSMOS_KEY = "dummy"
        mock_cfg.QDRANT_ENDPOINT = "http://localhost:6333"
        mock_cfg.QDRANT_KEY = "dummy"
        
        c1 = get_cosmos_client()
        c2 = get_cosmos_client()
        assert c1 is c2

        q1 = get_qdrant_client()
        q2 = get_qdrant_client()
        assert q1 is q2

def test_faq_text_caching():
    faq1 = _load_faq_text()
    faq2 = _load_faq_text()
    assert faq1 == faq2
