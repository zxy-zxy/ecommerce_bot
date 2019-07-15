import json
import os
import time

import pytest
import requests

from application.ecommerce_api.moltin_api.moltin import MoltinApiSession, MoltinApi
from application.ecommerce_api.moltin_api.parse import parse_products_list_response
from application.ecommerce_api.moltin_api.exceptions import MoltinApiError


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


def test_add_product_to_cart_successfully(mocker, monkeypatch, moltin_api_session):
    filepath = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'data',
        'add_product_to_cart_response.json',
    )
    with open(filepath, 'r') as f:
        json_content = f.read()

    product_in_cart_data = json.loads(json_content)

    def mock_post(*args, **kwargs):
        mock_response = mocker.MagicMock()
        mock_response.status_code = 201
        mock_response.json = mocker.MagicMock(return_value=product_in_cart_data)
        return mock_response

    product_id = product_in_cart_data['data'][0]['product_id']
    quantity = product_in_cart_data['data'][0]['quantity']
    cart_id = product_in_cart_data['data'][0]['id']

    monkeypatch.setattr('requests.Session.post', mock_post)
    moltin_api = MoltinApi(moltin_api_session)
    product_in_cart = moltin_api.add_product_to_cart(cart_id, product_id, quantity)

    assert product_in_cart.quantity == quantity
    assert product_in_cart.cart_id == cart_id
    assert product_in_cart.product_id == product_id


def test_add_product_to_cart_insufficient_stock(
    mocker, monkeypatch, moltin_api_session
):
    filepath = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'data',
        'add_product_to_cart_insufficient_stock.json',
    )
    with open(filepath, 'r') as f:
        json_content = f.read()

    add_product_to_cart_failed_data = json.loads(json_content)

    def mock_post(*args, **kwargs):
        mock_response = mocker.MagicMock()
        mock_response.status_code = 400
        mock_response.raise_for_status = mocker.MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError
        mock_response.json = mocker.MagicMock(
            return_value=add_product_to_cart_failed_data
        )
        return mock_response

    monkeypatch.setattr('requests.Session.post', mock_post)
    moltin_api = MoltinApi(moltin_api_session)
    cart_id = 'b295a019-0fb9-4460-9e6b-1ee8d1c5d7cd'
    product_id = '34274205-a329-432d-85fb-808eae5cb792'
    quantity = 1
    with pytest.raises(MoltinApiError):
        moltin_api.add_product_to_cart(cart_id, product_id, quantity)
