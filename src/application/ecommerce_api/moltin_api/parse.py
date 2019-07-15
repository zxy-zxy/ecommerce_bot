from typing import List, Union, Dict
from datetime import datetime

from application.models import (
    Product,
    File,
    NewProductInCart,
    CartHeader,
    CartContentProduct,
)


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
        formatted_price_with_tax = product_meta['display_price']['with_tax'][
            'formatted'
        ]
    except KeyError:
        formatted_price_with_tax = None

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
        formatted_price_with_tax=formatted_price_with_tax,
        currency=currency,
        main_image_id=main_image_id,
    )
    return product


def parse_file_response(dct: Dict) -> File:
    return File(
        id=dct['id'],
        link=dct['link']['href'],
        type=dct['type'],
        file_name=dct['file_name'],
    )


def parse_add_product_to_cart_response(dct: Dict) -> NewProductInCart:
    return NewProductInCart(
        cart_id=dct['id'], product_id=dct['product_id'], quantity=dct['quantity']
    )


def parse_cart_header_response(dct: Dict) -> CartHeader:
    meta = dct['meta']
    created_at_datetime_str = meta['timestamps']['created_at']
    try:
        created_at = datetime.strptime(created_at_datetime_str, '%Y-%m-%dT%H:%M:%S%z')
    except ValueError:
        created_at = None
    cart_header = CartHeader(
        id=dct['id'],
        formatted_price_with_tax=meta['display_price']['with_tax']['formatted'],
        currency=meta['display_price']['with_tax']['currency'],
        created_at=created_at,
    )
    return cart_header


def parse_cart_content_response(cart_content: List[Dict]) -> List[CartContentProduct]:
    result = []
    for product_in_cart_dct in cart_content:
        product_meta = product_in_cart_dct['meta']
        product_display_price = product_meta['display_price']
        value = product_in_cart_dct['value']['amount'] / 100
        formatted_price_with_tax = product_display_price['with_tax']['unit'][
            'formatted'
        ]
        formatted_value_with_tax = product_display_price['with_tax']['value'][
            'formatted'
        ]
        currency = product_display_price['with_tax']['unit']['currency']
        cart_content_product = CartContentProduct(
            id=product_in_cart_dct['id'],
            product_id=product_in_cart_dct['product_id'],
            quantity=product_in_cart_dct['quantity'],
            value=value,
            currency=currency,
            formatted_price_with_tax=formatted_price_with_tax,
            formatted_value_with_tax=formatted_value_with_tax,
            description=product_in_cart_dct['description'],
            sku=product_in_cart_dct['sku'],
            name=product_in_cart_dct['name'],
        )
        result.append(cart_content_product)
    return result
