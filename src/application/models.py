from datetime import datetime
from typing import Union, List, Dict
from dataclasses import dataclass
from decimal import Decimal
import re

from application.database import RedisStorage


@dataclass
class RawData:
    data: Dict
    meta: Dict


@dataclass
class Product:
    id: str
    type: str
    name: str
    description: str
    slug: str
    sku: str
    currency: Union[str, None] = None
    formatted_price_with_tax: Union[str, None] = None
    main_image_id: Union[str, None] = None

    @property
    def price(self) -> Decimal:
        return Decimal(re.sub('[^\d\.]', '', self.formatted_price_with_tax))


@dataclass
class File:
    type: str
    id: str
    link: str
    file_name: str


@dataclass
class AddedProductToCart:
    cart_id: str
    product_id: str
    quantity: int


@dataclass
class CartHeader:
    id: str
    formatted_price_with_tax: str
    currency: str
    created_at: Union[datetime, None] = None

    @property
    def price(self) -> Decimal:
        return Decimal(re.sub('[^\d\.]', '', self.formatted_price_with_tax))


@dataclass
class ProductInCart:
    cart_id: str
    product_id: str
    quantity: int
    value: Decimal
    formatted_price_with_tax: str
    currency: str


class User:
    def __init__(self, user_id: str):
        self.user_id = user_id

    def save_state_to_db(self, state):
        return RedisStorage.set(self.user_id, state)

    def get_state_from_db(self):
        return RedisStorage.get(self.user_id)
