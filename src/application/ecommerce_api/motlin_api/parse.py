from typing import List

from application.ecommerce_api.models import Product


def parse_get_products_response(dct) -> List[Product]:
    product_live_status = 'live'

    result = []

    for product_obj in dct['data']:
        if product_obj['status'] != product_live_status:
            continue

        product_meta = product_obj['meta']
        try:
            formatted_price = product_meta['display_price']['with_tax']['formatted']
            currency = product_meta['display_price']['with_tax']['currency']
        except KeyError:
            formatted_price = None
            currency = None

        product = Product(
            description=product_obj['description'],
            id=product_obj['id'],
            type=product_obj['type'],
            name=product_obj['name'],
            sku=product_obj['sku'],
            slug=product_obj['slug'],
            formatted_price=formatted_price,
            currency=currency
        )
        result.append(product)

    return result
