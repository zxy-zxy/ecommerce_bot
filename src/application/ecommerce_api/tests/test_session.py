import time
import pytest

import requests
import requests_mock

from application.ecommerce_api.moltin_api.moltin import MoltinApiSession
from application.ecommerce_api.moltin_api.exceptions import (
    MoltinApiError,
    MoltinUnavailable,
)


class TestMotlinApiSession:
    def setup(self):
        self.root_url = 'http://fakeapi.com'
        self.oath_url = '{}/{}'.format(self.root_url, MoltinApiSession.oauth_url)
        self.access_token = 'fake token'
        self.client_id = 'fake client id'
        self.client_secret = 'fake client secret'

    def test_access_token_updated_successfully(self):
        with requests_mock.Mocker() as m:
            expires = time.time()
            m.post(
                self.oath_url,
                status_code=200,
                json={'expires': expires, 'access_token': self.access_token},
            )
            motlin_api_session = MoltinApiSession(
                self.root_url, self.client_id, self.client_secret
            )
            motlin_api_session._update_access_token()
            assert motlin_api_session.access_token == self.access_token
            assert motlin_api_session.access_token_expires_in == expires

    def test_negative_response_raises_api_error(self):
        with requests_mock.Mocker() as m:
            status_code = 401
            m.post(
                self.oath_url,
                status_code=status_code,
                json={
                    'errors': [
                        {
                            'status': status_code,
                            'title': 'Unable to validate access token',
                        }
                    ]
                },
            )
            motlin_api_session = MoltinApiSession(
                self.root_url, self.client_id, self.client_secret
            )
            with pytest.raises(MoltinApiError):
                motlin_api_session._update_access_token()

    def test_requests_exception_raises_motlin_unavailable_error(self):
        with requests_mock.Mocker() as m:
            m.post(self.oath_url, exc=requests.ConnectionError)
            motlin_api_session = MoltinApiSession(
                self.root_url, self.client_id, self.client_secret
            )
            with pytest.raises(MoltinUnavailable):
                motlin_api_session._update_access_token()
