from pydantic import BaseModel

class Product(BaseModel):
    id: int | None = None
    name: str
    price: float

class BasketItem(BaseModel):
    id: int | None = None
    product_id: int
    quantity: int