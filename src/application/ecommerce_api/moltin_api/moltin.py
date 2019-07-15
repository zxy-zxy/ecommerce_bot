from typing import List, Dict
import functools
import time
import logging
from json import JSONDecodeError

import requests
from requests import Session

from application.models import (
    Product,
    NewProductInCart,
    File,
    CartHeader,
    CartContentProduct,
)
from application.ecommerce_api.moltin_api.exceptions import (
    MoltinApiError,
    MoltinUnexpectedFormatResponseError,
    MoltinUnavailable,
)
from application.ecommerce_api.moltin_api.parse import (
    parse_products_list_response,
    parse_product_response,
    parse_file_response,
    parse_add_product_to_cart_response,
    parse_cart_header_response,
    parse_cart_content_response,
)

logger = logging.getLogger(__name__)


def access_token_required(func):
    @functools.wraps(func)
    def wrapped(self, *args, **kwargs):
        if (self.access_token is None
                or self.access_token_expires_in is None
                or self.access_token_expires_in < time.time() - 10):
            self._update_access_token()
        return func(self, *args, **kwargs)

    return wrapped


class MoltinApiSession(Session):
    oauth_url = 'oauth/access_token'

    def __init__(self, root_url: str, client_id: str, client_secret: str):
        super(MoltinApiSession, self).__init__()
        self.root_url = root_url.rstrip('/')
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.access_token_expires_in = None

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        str_repr = (
            'client id: {}, client secret: {},'
            'access token: {},'
            'access_token_expires_in: {} '.format(
                self.client_id,
                self.client_secret,
                self.access_token,
                self.access_token_expires_in,
            )
        )
        return str_repr

    def get(self, url, **kwargs):
        return self._make_request('get', url, **kwargs)

    def post(self, url, data=None, json=None, **kwargs):
        return self._make_request('post', url, data=data, json=json, **kwargs)

    def delete(self, url, **kwargs):
        return self._make_request('delete', url, **kwargs)

    @access_token_required
    def _make_request(self, method, url, **kwargs):
        method = getattr(super(MoltinApiSession, self), method)

        url = '{}/{}'.format(self.root_url, url.lstrip('/'))

        try:
            response = method(url, **kwargs)
            response.raise_for_status()
        except (requests.ConnectionError, requests.Timeout) as e:
            raise MoltinUnavailable() from e
        except requests.HTTPError as e:
            response_dict = response.json()

            error = response_dict['errors'][0]
            error_status = error.get('status', None)
            error_title = error.get('title', None)
            error_detail = error.get('detail', None)

            logger.debug(
                'json response from {} with status code {} : {}'.format(
                    url, response.status_code, response_dict
                )
            )

            raise MoltinApiError(
                response.url, error_status, error_title, error_detail
            ) from e

        try:
            response_dict = response.json()
            logger.debug(
                'json response from {} with status code {} : {}'.format(
                    url, response.status_code, response_dict
                )
            )
            return response_dict
        except (JSONDecodeError, KeyError) as e:
            raise MoltinUnexpectedFormatResponseError(
                'error: {}, data: {}'.format(str(e), response)
            ) from e

    def _update_access_token(self):

        url = '{}/{}'.format(self.root_url, MoltinApiSession.oauth_url)

        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'client_credentials',
        }
        try:
            response = requests.post(url, data=data)
            response.raise_for_status()
        except (requests.ConnectionError, requests.Timeout) as e:
            raise MoltinUnavailable() from e
        except requests.HTTPError as e:
            response_dict = response.json()

            error = response_dict['errors'][0]
            error_status = error['status']
            error_title = error['title']
            error_detail = error['detail'] if 'detail' in error.keys() else None

            raise MoltinApiError(
                response.url, error_status, error_title, error_detail
            ) from e

        response_dict = response.json()
        self.access_token_expires_in = response_dict['expires']
        self.access_token = response_dict['access_token']
        self.headers.update({'Authorization': 'Bearer: {}'.format(self.access_token)})


class MoltinApi:
    get_products_list_url = 'v2/products'
    get_product_url = '/v2/products/{}'
    get_file_url = 'v2/files/{}'
    get_cart_url = 'v2/carts/{}'
    cart_products_url = 'v2/carts/{}/items'
    cart_product_url = 'v2/carts/{}/items/{}'
    flow_url = '/v2/flows'

    def __init__(self, session: MoltinApiSession):
        self.session = session

    def get_products(self, limit=100) -> List[Product]:
        params = {'page[limit]': limit}
        data_dct = self.session.get(MoltinApi.get_products_list_url, params=params)
        products_dct = data_dct['data']
        return parse_products_list_response(products_dct)

    def get_product_by_id(self, product_id: str) -> Product:
        url = MoltinApi.get_product_url.format(product_id)
        data_dct = self.session.get(url)
        product_dct = data_dct['data']
        return parse_product_response(product_dct)

    def get_file_by_id(self, file_id: str) -> File:
        url = MoltinApi.get_file_url.format(file_id)
        data_dct = self.session.get(url)
        file_dct = data_dct['data']
        return parse_file_response(file_dct)

    def get_cart(self, cart_reference: str) -> CartHeader:
        url = MoltinApi.get_cart_url.format(cart_reference)
        data_dct = self.session.get(url)
        cart_header_dct = data_dct['data']
        return parse_cart_header_response(cart_header_dct)

    def get_cart_products(self, cart_reference: str) -> List[CartContentProduct]:
        url = MoltinApi.cart_products_url.format(cart_reference)
        data_dct = self.session.get(url)
        cart_content = data_dct['data']
        return parse_cart_content_response(cart_content)

    def add_product_to_cart(
            self, cart_reference: str, product_id: str, quantity: int = 1
    ) -> NewProductInCart:
        url = MoltinApi.cart_products_url.format(cart_reference)
        data_dct = self.session.post(
            url,
            json={
                'data': {'quantity': quantity, 'type': 'cart_item', 'id': product_id}
            },
        )
        product_in_cart_dct = data_dct['data']
        return parse_add_product_to_cart_response(product_in_cart_dct[0])

    def remove_item_from_cart(self, cart_reference: str, item_id: str) -> bool:
        url = MoltinApi.cart_product_url.format(cart_reference, item_id)
        self.session.delete(url)
        return True

    def create_flow(self, data: Dict) -> bool:
        url = MoltinApi.flow_url
        self.session.post(url, json={'data': data})
        return True
