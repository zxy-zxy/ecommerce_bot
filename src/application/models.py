from typing import Union
from dataclasses import dataclass
from decimal import Decimal
import re

from application.database import RedisStorage


@dataclass
class Product:
    id: str
    type: str
    name: str
    description: str
    slug: str
    sku: str
    currency: Union[str, None] = None
    formatted_price: Union[str, None] = None
    main_image_id: Union[str, None] = None

    @property
    def price(self) -> Decimal:
        return Decimal(re.sub('[^\d\.]', '', self.formatted_price))


@dataclass
class AddProductToCart:
    id: str


class User:
    def __init__(self, user_id: str):
        self.user_id = user_id

    def save_state_to_db(self, state):
        return RedisStorage.set(self.user_id, state)

    def get_state_from_db(self):
        return RedisStorage.get(self.user_id)
