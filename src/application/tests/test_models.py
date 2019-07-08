import uuid
import decimal

import pytest

from application.models import Product


@pytest.fixture
def product():
    return Product(
        id=str(uuid.uuid4()),
        formatted_price='$243.50',
        name='New product',
        type='product type',
        description='New product',
        currency='USD',
        slug='new-product',
        sku='new-product',
    )


def test_formatted_price_field_converted_properly(product):
    assert product.price == decimal.Decimal(243.50)
