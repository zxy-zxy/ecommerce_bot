from dataclasses import dataclass
from decimal import Decimal
import re


@dataclass
class Product:
    id: str
    type: str
    name: str
    description: str
    formatted_price: str
    currency: str
    slug: str
    sku: str

    @property
    def price(self) -> Decimal:
        return Decimal(re.sub('[^\d\.]', '', self.formatted_price))


@dataclass
class AddProductToCart:
    id: str
