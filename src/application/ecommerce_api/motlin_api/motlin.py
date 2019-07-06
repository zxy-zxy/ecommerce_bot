from typing import List
import functools
import time

import requests
from requests import Session

from application.ecommerce_api.models import Product
from application.ecommerce_api.motlin_api.exceptions import MotlinApiError, MotlinUnavailable
from application.ecommerce_api.motlin_api.parse import parse_get_products_response


def access_token_required(func):
    @functools.wraps(func)
    def wrapped(self, *args, **kwargs):
        if (self.access_token is None
                or self.access_token_expires_in is None
                or self.access_token_expires_in < time.time() - 10):
            self._update_access_token()
        return func(self, *args, **kwargs)

    return wrapped


class MotlinApiSession(Session):
    oauth_url = 'oauth/access_token'

    def __init__(self, root_url: str, client_id: str, client_secret: str):
        super(MotlinApiSession, self).__init__()
        self.root_url = root_url.rstrip('/')
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.access_token_expires_in = None

    @access_token_required
    def get(self, url, **kwargs):
        url = '{}/{}'.format(self.root_url, url.lstrip('/'))
        try:
            response = super(MotlinApiSession, self).get(url, **kwargs)
            response.raise_for_status()
        except (requests.ConnectionError, requests.Timeout) as e:
            raise MotlinUnavailable() from e
        except requests.HTTPError as e:
            response_dict = response.json()
            raise MotlinApiError(
                response_dict['errors'][0]['status'],
                response_dict['errors'][0]['title'],
                response.url
            ) from e
        return response

    @access_token_required
    def post(self, url, data=None, json=None, **kwargs):
        url = '{}/{}'.format(self.root_url, url.lstrip('/'))
        try:
            response = super(MotlinApiSession, self).post(url, data, json, **kwargs)
            response.raise_for_status()
        except (requests.ConnectionError, requests.Timeout) as e:
            raise MotlinUnavailable() from e
        except requests.HTTPError as e:
            response_dict = response.json()
            raise MotlinApiError(
                response_dict['errors'][0]['status'],
                response_dict['errors'][0]['title'],
                response.url
            ) from e
        return response

    def _update_access_token(self):

        url = '{}/{}'.format(self.root_url, MotlinApiSession.oauth_url)

        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'client_credentials',
        }
        try:
            response = requests.post(url, data=data)
            response.raise_for_status()
        except (requests.ConnectionError, requests.Timeout) as e:
            raise MotlinUnavailable() from e
        except requests.HTTPError as e:
            response_dict = response.json()
            raise MotlinApiError(
                response_dict['errors'][0]['status'],
                response_dict['errors'][0]['title'],
                response.url
            )

        response_dict = response.json()
        self.access_token_expires_in = response_dict['expires']
        self.access_token = response_dict['access_token']
        self.headers.update({
            'Authorization': 'Bearer: {}'.format(self.access_token)
        })


class MotlinApi:
    products_list_url = 'v2/products'
    get_cart_url = 'v2/carts/{}'
    add_product_to_cart_url = 'v2/carts/{}/items'

    def __init__(self, session: MotlinApiSession):
        self.session = session

    def get_products(self, limit=100) -> List[Product]:
        params = {
            'page[limit]': limit
        }

        response = self.session.get(MotlinApi.products_list_url, params=params)
        return parse_get_products_response(response.json())

    def get_cart(self, cart_reference: str):
        url = MotlinApi.get_cart_url.format(cart_reference)
        response = self.session.get(url)
        return response.json()

    def add_product_to_cart(self, cart_reference: str, product_id: str, quantity: int):
        url = MotlinApi.add_product_to_cart_url.format(cart_reference)
        response = self.session.post(url, json={
            'quantity': quantity,
            'type': 'cart_item',
            'id': product_id
        })
        return response.json()
