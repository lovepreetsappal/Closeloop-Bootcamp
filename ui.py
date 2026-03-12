import json
import tkinter as tk
from tkinter import messagebox, ttk
from urllib import error, parse, request


class ShoppingCartUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Shopping Cart UI")
        self.root.geometry("980x640")

        self.base_url_var = tk.StringVar(value="http://127.0.0.1:8000")
        self.product_name_var = tk.StringVar()
        self.product_price_var = tk.StringVar()
        self.basket_product_id_var = tk.StringVar()
        self.basket_quantity_var = tk.StringVar()
        self.update_item_id_var = tk.StringVar()
        self.update_quantity_var = tk.StringVar()
        self.delete_item_id_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready")

        self._build_ui()
        self.refresh_products()
        self.refresh_basket()

    def _build_ui(self) -> None:
        root_frame = ttk.Frame(self.root, padding=12)
        root_frame.pack(fill=tk.BOTH, expand=True)

        header = ttk.Frame(root_frame)
        header.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(header, text="API Base URL:").pack(side=tk.LEFT)
        ttk.Entry(header, textvariable=self.base_url_var, width=40).pack(side=tk.LEFT, padx=8)
        ttk.Button(header, text="Refresh All", command=self.refresh_all).pack(side=tk.LEFT)

        body = ttk.Frame(root_frame)
        body.pack(fill=tk.BOTH, expand=True)

        self._build_products_panel(body)
        self._build_basket_panel(body)

        status_bar = ttk.Label(root_frame, textvariable=self.status_var, anchor=tk.W)
        status_bar.pack(fill=tk.X, pady=(8, 0))

    def _build_products_panel(self, parent: ttk.Frame) -> None:
        panel = ttk.LabelFrame(parent, text="Products", padding=10)
        panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 6))

        form = ttk.Frame(panel)
        form.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(form, text="Name").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(form, textvariable=self.product_name_var, width=18).grid(row=0, column=1, padx=5)
        ttk.Label(form, text="Price").grid(row=0, column=2, sticky=tk.W)
        ttk.Entry(form, textvariable=self.product_price_var, width=10).grid(row=0, column=3, padx=5)
        ttk.Button(form, text="Create Product", command=self.create_product).grid(row=0, column=4, padx=5)
        ttk.Button(form, text="Refresh", command=self.refresh_products).grid(row=0, column=5, padx=5)

        self.products_table = ttk.Treeview(panel, columns=("id", "name", "price"), show="headings", height=20)
        self.products_table.heading("id", text="ID")
        self.products_table.heading("name", text="Name")
        self.products_table.heading("price", text="Price")
        self.products_table.column("id", width=60, anchor=tk.CENTER)
        self.products_table.column("name", width=220)
        self.products_table.column("price", width=120, anchor=tk.E)
        self.products_table.pack(fill=tk.BOTH, expand=True)

    def _build_basket_panel(self, parent: ttk.Frame) -> None:
        panel = ttk.LabelFrame(parent, text="Basket", padding=10)
        panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(6, 0))

        add_form = ttk.Frame(panel)
        add_form.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(add_form, text="Product ID").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(add_form, textvariable=self.basket_product_id_var, width=10).grid(row=0, column=1, padx=5)
        ttk.Label(add_form, text="Qty").grid(row=0, column=2, sticky=tk.W)
        ttk.Entry(add_form, textvariable=self.basket_quantity_var, width=10).grid(row=0, column=3, padx=5)
        ttk.Button(add_form, text="Add to Basket", command=self.add_to_basket).grid(row=0, column=4, padx=5)
        ttk.Button(add_form, text="Refresh", command=self.refresh_basket).grid(row=0, column=5, padx=5)

        manage_form = ttk.Frame(panel)
        manage_form.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(manage_form, text="Item ID").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(manage_form, textvariable=self.update_item_id_var, width=10).grid(row=0, column=1, padx=5)
        ttk.Label(manage_form, text="New Qty").grid(row=0, column=2, sticky=tk.W)
        ttk.Entry(manage_form, textvariable=self.update_quantity_var, width=10).grid(row=0, column=3, padx=5)
        ttk.Button(manage_form, text="Update Qty", command=self.update_quantity).grid(row=0, column=4, padx=5)

        delete_form = ttk.Frame(panel)
        delete_form.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(delete_form, text="Item ID").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(delete_form, textvariable=self.delete_item_id_var, width=10).grid(row=0, column=1, padx=5)
        ttk.Button(delete_form, text="Remove Item", command=self.remove_item).grid(row=0, column=2, padx=5)

        self.basket_table = ttk.Treeview(
            panel,
            columns=("id", "product", "price", "quantity", "total"),
            show="headings",
            height=20,
        )
        self.basket_table.heading("id", text="Item ID")
        self.basket_table.heading("product", text="Product")
        self.basket_table.heading("price", text="Price")
        self.basket_table.heading("quantity", text="Qty")
        self.basket_table.heading("total", text="Total")
        self.basket_table.column("id", width=70, anchor=tk.CENTER)
        self.basket_table.column("product", width=180)
        self.basket_table.column("price", width=100, anchor=tk.E)
        self.basket_table.column("quantity", width=80, anchor=tk.CENTER)
        self.basket_table.column("total", width=110, anchor=tk.E)
        self.basket_table.pack(fill=tk.BOTH, expand=True)

    def _base(self) -> str:
        return self.base_url_var.get().rstrip("/")

    def _request(self, method: str, path: str, payload: dict | None = None) -> dict | list:
        url = f"{self._base()}{path}"
        data = None
        headers = {"Content-Type": "application/json"}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")

        req = request.Request(url, method=method, data=data, headers=headers)
        try:
            with request.urlopen(req, timeout=10) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            try:
                parsed = json.loads(body)
                detail = parsed.get("detail", body)
            except json.JSONDecodeError:
                detail = body or str(e)
            raise RuntimeError(f"HTTP {e.code}: {detail}") from e
        except error.URLError as e:
            raise RuntimeError(f"Network error: {e.reason}") from e

    def refresh_all(self) -> None:
        self.refresh_products()
        self.refresh_basket()

    def refresh_products(self) -> None:
        try:
            products = self._request("GET", "/products")
            self.products_table.delete(*self.products_table.get_children())
            for p in products:
                self.products_table.insert("", tk.END, values=(p["id"], p["name"], f'{p["price"]:.2f}'))
            self.status_var.set("Products loaded")
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.status_var.set("Failed to load products")

    def create_product(self) -> None:
        name = self.product_name_var.get().strip()
        price_text = self.product_price_var.get().strip()
        if not name:
            messagebox.showwarning("Validation", "Product name is required")
            return
        try:
            price = float(price_text)
        except ValueError:
            messagebox.showwarning("Validation", "Price must be a number")
            return
        try:
            self._request("POST", "/products", {"name": name, "price": price})
            self.product_name_var.set("")
            self.product_price_var.set("")
            self.refresh_products()
            self.status_var.set("Product created")
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.status_var.set("Failed to create product")

    def refresh_basket(self) -> None:
        try:
            basket = self._request("GET", "/basket")
            self.basket_table.delete(*self.basket_table.get_children())
            for item in basket:
                product = item["product"]
                self.basket_table.insert(
                    "",
                    tk.END,
                    values=(
                        item["id"],
                        product["name"],
                        f'{product["price"]:.2f}',
                        item["quantity"],
                        f'{item["total_price"]:.2f}',
                    ),
                )
            self.status_var.set("Basket loaded")
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.status_var.set("Failed to load basket")

    def add_to_basket(self) -> None:
        try:
            product_id = int(self.basket_product_id_var.get().strip())
            quantity = int(self.basket_quantity_var.get().strip())
        except ValueError:
            messagebox.showwarning("Validation", "Product ID and quantity must be integers")
            return
        try:
            self._request("POST", "/basket", {"product_id": product_id, "quantity": quantity})
            self.basket_product_id_var.set("")
            self.basket_quantity_var.set("")
            self.refresh_basket()
            self.status_var.set("Basket item added")
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.status_var.set("Failed to add basket item")

    def update_quantity(self) -> None:
        try:
            item_id = int(self.update_item_id_var.get().strip())
            quantity = int(self.update_quantity_var.get().strip())
        except ValueError:
            messagebox.showwarning("Validation", "Item ID and quantity must be integers")
            return
        try:
            query = parse.urlencode({"quantity": quantity})
            self._request("PUT", f"/basket/{item_id}?{query}")
            self.update_item_id_var.set("")
            self.update_quantity_var.set("")
            self.refresh_basket()
            self.status_var.set("Basket quantity updated")
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.status_var.set("Failed to update quantity")

    def remove_item(self) -> None:
        try:
            item_id = int(self.delete_item_id_var.get().strip())
        except ValueError:
            messagebox.showwarning("Validation", "Item ID must be an integer")
            return
        try:
            self._request("DELETE", f"/basket/{item_id}")
            self.delete_item_id_var.set("")
            self.refresh_basket()
            self.status_var.set("Basket item removed")
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.status_var.set("Failed to remove basket item")


def main() -> None:
    root = tk.Tk()
    app = ShoppingCartUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
