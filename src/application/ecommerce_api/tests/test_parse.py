import os
import json

from application.models import Product
from application.ecommerce_api.moltin_api.parse import (
    parse_product_response,
    parse_products_list_response
)


class TestParseMotlinResponse:
    def test_product_parsed_propely(self):
        filepath = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'data',
            'product_response.json'
        )
        with open(filepath, 'r') as f:
            json_content = f.read()
            data = json.loads(json_content)
            data = data['data']
            product = parse_product_response(data)
            assert isinstance(product, Product)
            assert data['type'] == product.type
            assert data['id'] == product.id
            assert data['slug'] == product.slug

    def test_products_list_parsed_properly(self):
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
                assert isinstance(product, Product)
                assert product_dict['name'] == product.name
                assert product_dict['slug'] == product.slug
                assert product_dict['sku'] == product.sku
                assert product_dict['description'] == product.description
