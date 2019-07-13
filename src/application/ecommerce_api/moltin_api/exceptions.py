class MoltinError(Exception):
    pass


class MoltinUnavailable(MoltinError):
    pass


class MoltinUnexpectedFormatResponseError(MoltinError):
    pass


class MoltinApiError(MoltinError):
    def __init__(self, url, status, title, detail):
        self.url = url
        self.code = status
        self.title = title
        self.detail = detail

    def __str__(self):
        return 'status: {}, title: {}, detail: {} from {}'.format(
            self.code, self.title, self.detail, self.url)
