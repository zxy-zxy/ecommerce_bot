from typing import Dict
from datetime import datetime
from decimal import Decimal
import os
import json
import re

from application.models import Product
from application.ecommerce_api.moltin_api.parse import (
    parse_product_response,
    parse_products_list_response,
    parse_add_product_to_cart_response,
    parse_cart_header_response,
)


def test_product_parsed_propely():
    filepath = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'data', 'product_response.json'
    )
    with open(filepath, 'r') as f:
        json_content = f.read()

    data = json.loads(json_content)
    data = data['data']
    product = parse_product_response(data)
    _compare_product_dict_and_product(data, product)


def test_products_list_parsed_properly():
    filepath = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'data',
        'products_list_response.json',
    )
    with open(filepath, 'r') as f:
        json_content = f.read()

    data = json.loads(json_content)
    data = data['data']
    products = parse_products_list_response(data)
    assert isinstance(products, list)
    assert len(products) == 1
    for product_dict, product in zip(data, products):
        _compare_product_dict_and_product(product_dict, product)


def _compare_product_dict_and_product(data: Dict, product: Product):
    assert isinstance(product, Product)

    relationships = data['relationships']
    meta = data['meta']

    assert data['name'] == product.name
    assert data['id'] == product.id
    assert data['slug'] == product.slug
    assert data['type'] == product.type
    assert data['sku'] == product.sku
    assert data['description'] == product.description

    main_image_id = relationships['main_image']['data']['id']
    assert main_image_id == product.main_image_id

    formatted_price = meta['display_price']['with_tax']['formatted']
    assert formatted_price == product.formatted_price_with_tax


def test_add_product_to_cart_parsed_properly():
    filepath = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'data',
        'add_product_to_cart_response.json',
    )
    with open(filepath, 'r') as f:
        json_content = f.read()

    data = json.loads(json_content)
    data = data['data'][0]
    product_in_cart = parse_add_product_to_cart_response(data)
    assert product_in_cart.cart_id == data['id']
    assert product_in_cart.product_id == data['product_id']
    assert product_in_cart.quantity == data['quantity']


def test_get_current_cart_condition_parsed_properly():
    filepath = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'data', 'cart_header_response.json'
    )
    with open(filepath, 'r') as f:
        json_content = f.read()

    data_from_file = json.loads(json_content)
    meta_from_file = data_from_file['data']['meta']
    formatted_price_from_file = meta_from_file['display_price']['with_tax']['formatted']
    id_from_file = data_from_file['data']['id']
    currency_from_file = meta_from_file['display_price']['with_tax']['currency']
    created_at_from_file = meta_from_file['timestamps']['created_at']
    created_at_from_file = datetime.strptime(
        created_at_from_file, '%Y-%m-%dT%H:%M:%S%z'
    )

    cart_header = parse_cart_header_response(data_from_file['data'])

    assert id_from_file == cart_header.id
    assert formatted_price_from_file == cart_header.formatted_price_with_tax
    assert currency_from_file == cart_header.currency
    assert created_at_from_file == cart_header.created_at
    price_from_file = Decimal(re.sub('[^\d\.]', '', formatted_price_from_file))
    assert price_from_file == cart_header.price


def test_get_cart_content_response():
    pass
