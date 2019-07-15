from typing import Iterable


def chunks(l: Iterable, n: int):
    for i in range(0, len(l), n):
        yield l[i:i + n]
