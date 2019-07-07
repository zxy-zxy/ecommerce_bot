from typing import List, Union, Dict

from application.models import Product


def parse_products_list_response(list_of_products_dicts: List[Dict]) -> List[Product]:
    result = []

    for product_obj in list_of_products_dicts:

        product = parse_product_response(product_obj)
        if product is None:
            continue
        result.append(product)

    return result


def parse_product_response(dct: Dict) -> Union[None, Product]:
    product_live_status = 'live'

    if dct['status'] != product_live_status:
        return None

    product_meta = dct['meta']
    try:
        formatted_price = product_meta['display_price']['with_tax']['formatted']
        currency = product_meta['display_price']['with_tax']['currency']
    except KeyError:
        formatted_price = None
        currency = None

    product_relationships = dct['relationships']
    try:
        main_image_id = product_relationships['main_image']['data']['id']
    except KeyError:
        main_image_id = None

    product = Product(
        description=dct['description'],
        id=dct['id'],
        type=dct['type'],
        name=dct['name'],
        sku=dct['sku'],
        slug=dct['slug'],
        formatted_price=formatted_price,
        currency=currency,
        main_image_id=main_image_id
    )
    return product
