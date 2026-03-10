from fastapi import FastAPI, HTTPException
from models import Product, BasketItem

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Welcome to the Shopping Cart API. Visit /docs for API documentation."}

products = []
basket = []
product_id_counter = 1
basket_id_counter = 1

@app.post("/products")
def create_product(product: Product):
    global product_id_counter
    product.id = product_id_counter
    product_id_counter += 1
    products.append(product)
    return product

@app.get("/products")
def get_products():
    return products

@app.post("/basket")
def add_to_basket(item: BasketItem):
    global basket_id_counter
    if not any(p.id == item.product_id for p in products):
        raise HTTPException(status_code=404, detail="Product not found")
    item.id = basket_id_counter
    basket_id_counter += 1
    basket.append(item)
    return item

@app.get("/basket")
def view_basket():
    result = []
    for item in basket:
        product = next((p for p in products if p.id == item.product_id), None)
        if product:
            result.append({
                "id": item.id,
                "product": product,
                "quantity": item.quantity,
                "total_price": item.quantity * item.product_id  # BUG 2 HERE
            })
    return result

@app.put("/basket/{item_id}")
def update_quantity(item_id: int, quantity: int):
    for item in basket:
        if item.id == item_id:
            item.quantity = quantity  # BUG 3: no validation on quantity value
            return item
    raise HTTPException(status_code=404, detail="Item not found")

@app.delete("/basket/{item_id}")
def remove_from_basket(item_id: int):
    for i, item in enumerate(basket):
        if item.product_id == item_id:  # BUG 4: should be item.id == item_id
            del basket[i]
            return {"message": "Item removed"}
    raise HTTPException(status_code=404, detail="Item not found")