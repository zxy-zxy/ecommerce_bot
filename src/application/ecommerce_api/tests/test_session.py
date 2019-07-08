import time
import pytest

import requests
import requests_mock

from application.ecommerce_api.moltin_api.moltin import MoltinApiSession
from application.ecommerce_api.moltin_api.exceptions import (
    MoltinApiError,
    MoltinUnavailable,
)


@pytest.fixture
def moltin_api_session():
    root_url = 'http://fakeapi.com'
    client_id = 'fake client id'
    client_secret = 'fake client secret'

    return MoltinApiSession(root_url, client_id, client_secret)


def test_access_token_updated_successfully(moltin_api_session):
    root_url = 'http://fakeapi.com'
    oath_url = '{}/{}'.format(root_url, MoltinApiSession.oauth_url)
    access_token = 'fake token'

    with requests_mock.Mocker() as m:
        expires = time.time()
        m.post(
            oath_url,
            status_code=200,
            json={'expires': expires, 'access_token': access_token},
        )

        moltin_api_session._update_access_token()
        assert moltin_api_session.access_token == access_token
        assert moltin_api_session.access_token_expires_in == expires


def test_negative_response_raises_api_error(moltin_api_session):
    root_url = 'http://fakeapi.com'
    oath_url = '{}/{}'.format(root_url, MoltinApiSession.oauth_url)
    with requests_mock.Mocker() as m:
        status_code = 401
        m.post(
            oath_url,
            status_code=status_code,
            json={
                'errors': [
                    {'status': status_code, 'title': 'Unable to validate access token'}
                ]
            },
        )
        with pytest.raises(MoltinApiError):
            moltin_api_session._update_access_token()


def test_requests_exception_raises_motlin_unavailable_error(moltin_api_session):
    root_url = 'http://fakeapi.com'
    oath_url = '{}/{}'.format(root_url, MoltinApiSession.oauth_url)
    with requests_mock.Mocker() as m:
        m.post(oath_url, exc=requests.ConnectionError)
        with pytest.raises(MoltinUnavailable):
            moltin_api_session._update_access_token()
