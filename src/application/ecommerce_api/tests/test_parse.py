from typing import Dict
import os
import json

from application.models import Product
from application.ecommerce_api.moltin_api.parse import (
    parse_product_response,
    parse_products_list_response,
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
    assert formatted_price == product.formatted_price
