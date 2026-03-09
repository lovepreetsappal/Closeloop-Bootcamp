# Shopping Cart API

A simple REST API for managing a shopping cart built with FastAPI and Python.

## Features

- Create and list products
- Add products to shopping basket
- View basket contents with product details
- Update item quantities in basket
- Remove items from basket

## Installation

1. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```

## Running the API

Start the server with:
```
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`

Visit `http://127.0.0.1:8000/docs` for interactive API documentation.

## API Endpoints

### Products
- `POST /products` - Create a new product
  - Body: `{"name": "string", "price": number}`
- `GET /products` - List all products

### Basket
- `POST /basket` - Add item to basket
  - Body: `{"product_id": number, "quantity": number}`
- `GET /basket` - View basket contents
- `PUT /basket/{item_id}?quantity={new_quantity}` - Update item quantity
- `DELETE /basket/{item_id}` - Remove item from basket

## Example Usage

1. Create a product:
   ```bash
   curl -X POST "http://127.0.0.1:8000/products" -H "Content-Type: application/json" -d '{"name": "Laptop", "price": 999.99}'
   ```

2. Add to basket:
   ```bash
   curl -X POST "http://127.0.0.1:8000/basket" -H "Content-Type: application/json" -d '{"product_id": 1, "quantity": 1}'
   ```

3. View basket:
   ```bash
   curl "http://127.0.0.1:8000/basket"
   ```