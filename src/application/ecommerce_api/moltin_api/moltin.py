from typing import List
import functools
import time
from json import JSONDecodeError

import requests
from requests import Session

from application.models import Product
from application.ecommerce_api.moltin_api.exceptions import (
    MoltinApiError,
    MoltinUnexpectedFormatResponseError,
    MoltinUnavailable,
)
from application.ecommerce_api.moltin_api.parse import (
    parse_products_list_response,
    parse_product_response
)


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

    def get(self, url, **kwargs):
        return self._make_request('get', url, **kwargs)

    def post(self, url, data=None, json=None, **kwargs):
        return self._make_request('post', url, data=data, json=json, **kwargs)

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
            raise MoltinApiError(
                response_dict['errors'][0]['status'],
                response_dict['errors'][0]['title'],
                response.url,
            ) from e

        try:
            response = response.json()
            return response['data']
        except (JSONDecodeError, KeyError) as e:
            raise MoltinUnexpectedFormatResponseError(str(e)) from e

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
        except requests.HTTPError:
            response_dict = response.json()
            raise MoltinApiError(
                response_dict['errors'][0]['status'],
                response_dict['errors'][0]['title'],
                response.url,
            )

        response_dict = response.json()
        self.access_token_expires_in = response_dict['expires']
        self.access_token = response_dict['access_token']
        self.headers.update({'Authorization': 'Bearer: {}'.format(self.access_token)})


class MoltinApi:
    get_products_list_url = 'v 2/products'
    get_product_url = '/v2/products/{}'
    get_file_url = 'v2/files/{}'
    get_cart_url = 'v2/carts/{}'
    add_product_to_cart_url = 'v2/carts/{}/items'

    def __init__(self, session: MoltinApiSession):
        self.session = session

    def get_products(self, limit=100) -> List[Product]:
        params = {'page[limit]': limit}

        data = self.session.get(MoltinApi.get_products_list_url, params=params)
        return parse_products_list_response(data)

    def get_product(self, product_id: str) -> Product:
        url = MoltinApi.get_product_url.format(product_id)
        data = self.session.get(url)
        return parse_product_response(data)

    def get_file(self, file_id: str):
        url = MoltinApi.get_file_url.format(file_id)
        response = self.session.get(url)

    def get_cart(self, cart_reference: str):
        url = MoltinApi.get_cart_url.format(cart_reference)
        data = self.session.get(url)
        return data

    def add_product_to_cart(self, cart_reference: str, product_id: str, quantity: int):
        url = MoltinApi.add_product_to_cart_url.format(cart_reference)
        data = self.session.post(
            url, json={'quantity': quantity, 'type': 'cart_item', 'id': product_id}
        )
        return data
