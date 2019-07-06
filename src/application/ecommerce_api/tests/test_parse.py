import os
import json

from application.ecommerce_api.models import Product
from application.ecommerce_api.motlin_api.parse import parse_get_products_response


class TestParseMotlinResponse:
    def test_get_products_response_parsed_properly(self):
        filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'get_products_response.json')
        with open(filepath, 'r') as f:
            json_content = f.read()
            data = json.loads(json_content)
            products = parse_get_products_response(data)
            assert isinstance(products, list)
            assert len(products) == 1
            assert isinstance(products[0], Product)
            assert data['data'][0]['name'] == products[0].name
            assert data['data'][0]['slug'] == products[0].slug
            assert data['data'][0]['sku'] == products[0].sku
            assert data['data'][0]['description'] == products[0].description
