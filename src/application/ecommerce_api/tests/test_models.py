import uuid
import decimal

from application.ecommerce_api.models import Product


class TestProductModel:
    def test_formatted_price_field_converted_properly(self):
        product = Product(
            id=str(uuid.uuid4()),
            formatted_price='$243.50',
            name='New product',
            type='product type',
            description='New product',
            currency='USD',
            slug='new-product',
            sku='new-product'
        )
        print(product)
        assert product.price == decimal.Decimal(243.50)
