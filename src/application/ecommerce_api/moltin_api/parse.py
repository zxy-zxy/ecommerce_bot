from typing import List, Union, Dict

from application.models import Product, File, ProductInCart


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
    except KeyError:
        formatted_price = None

    try:
        currency = product_meta['display_price']['with_tax']['currency']
    except KeyError:
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


def parse_file_response(dct: Dict) -> File:
    return File(
        id=dct['id'],
        link=dct['link']['href'],
        type=dct['type'],
        file_name=dct['file_name']
    )


def parse_add_product_to_cart_response(dct: Dict) -> ProductInCart:
    return ProductInCart(
        cart_id=dct['id'],
        product_id=dct['product_id'],
        quantity=dct['quantity']
    )
