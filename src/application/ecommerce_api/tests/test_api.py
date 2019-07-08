import json
import os
import time

import pytest

from application.ecommerce_api.moltin_api.moltin import MoltinApiSession, MoltinApi
from application.ecommerce_api.moltin_api.parse import parse_products_list_response


@pytest.fixture
def moltin_api_session():
    root_url = 'http://fakeapi.com'
    client_id = 'fake client id'
    client_secret = 'fake client secret'
    access_token = 'access_token'
    access_token_expires_in = time.time() + 1000

    session = MoltinApiSession(root_url, client_id, client_secret)
    session.access_token = access_token
    session.access_token_expires_in = access_token_expires_in
    return session


def test_get_products_return_products(mocker, monkeypatch, moltin_api_session):
    filepath = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'data',
        'products_list_response.json',
    )
    with open(filepath, 'r') as f:
        json_content = f.read()

    data = json.loads(json_content)

    def mock_get(*args, **kwargs):
        mock_response = mocker.MagicMock()
        mock_response.status_code = 200
        mock_response.json = mocker.MagicMock(return_value=data)
        return mock_response

    products = parse_products_list_response(data['data'])

    monkeypatch.setattr('requests.Session.get', mock_get)
    moltin_api = MoltinApi(moltin_api_session)
    assert moltin_api.get_products() == products
