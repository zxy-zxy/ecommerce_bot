class MotlinError(Exception):
    pass


class MotlinUnavailable(MotlinError):
    pass


class MotlinApiError(MotlinError):
    def __init__(self, status, message, url):
        self.code = status
        self.message = message
        self.url = url

    def __str__(self):
        return '{} with code {} from {}'.format(
            self.message, self.code, self.url)
