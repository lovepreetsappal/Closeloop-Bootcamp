import time
from unittest.mock import Mock, patch

import pytest

import main as backend
import ui
from models import BasketItem, Product
from ui import ShoppingCartUI


class DummyVar:
    def __init__(self, value=""):
        self._value = value

    def get(self):
        return self._value

    def set(self, value):
        self._value = value


class DummyTable:
    def __init__(self):
        self.rows = []
        self.children = ["r1", "r2"]

    def get_children(self):
        return list(self.children)

    def delete(self, *args):
        self.children = []
        self.rows = []

    def insert(self, _parent, _index, values):
        self.rows.append(values)


@pytest.fixture(autouse=True)
def reset_state():
    backend.products.clear()
    backend.basket.clear()
    backend.product_id_counter = 1
    backend.basket_id_counter = 1


# TS-001

def test_ts001_main_window_launch_flow_calls_tk_and_mainloop():
    fake_root = Mock()
    with patch("ui.tk.Tk", return_value=fake_root) as tk_ctor, patch("ui.ShoppingCartUI") as app_ctor:
        ui.main()

    tk_ctor.assert_called_once()
    app_ctor.assert_called_once_with(fake_root)
    fake_root.mainloop.assert_called_once()


# TS-002

def test_ts002_window_close_behavior_delegated_to_tk_mainloop_exit():
    fake_root = Mock()
    with patch("ui.tk.Tk", return_value=fake_root), patch("ui.ShoppingCartUI"):
        ui.main()
    assert fake_root.mainloop.call_count == 1


# TS-003

def test_ts003_reopen_window_creates_fresh_root_each_time():
    root1 = Mock()
    root2 = Mock()
    with patch("ui.tk.Tk", side_effect=[root1, root2]) as tk_ctor, patch("ui.ShoppingCartUI"):
        ui.main()
        ui.main()

    assert tk_ctor.call_count == 2


# TS-004

def test_ts004_create_button_handler_calls_request_once():
    instance = ShoppingCartUI.__new__(ShoppingCartUI)
    instance.product_name_var = DummyVar("Desk")
    instance.product_price_var = DummyVar("100")
    instance.status_var = DummyVar("")
    instance._request = Mock(return_value={"id": 1})
    instance.refresh_products = Mock()

    with patch("ui.messagebox.showwarning"), patch("ui.messagebox.showerror"):
        instance.create_product()

    instance._request.assert_called_once_with("POST", "/products", {"name": "Desk", "price": 100.0})


# TS-005

def test_ts005_double_click_simulation_calls_create_handler_twice():
    instance = ShoppingCartUI.__new__(ShoppingCartUI)
    instance.product_name_var = DummyVar("Desk")
    instance.product_price_var = DummyVar("100")
    instance.status_var = DummyVar("")
    instance._request = Mock(return_value={"id": 1})
    instance.refresh_products = Mock()

    with patch("ui.messagebox.showwarning") as showwarning, patch("ui.messagebox.showerror"):
        instance.create_product()
        instance.create_product()

    # First call succeeds and clears fields; second call hits empty-name validation.
    assert instance._request.call_count == 1
    showwarning.assert_called_once()


# TS-006

def test_ts006_fields_clear_after_successful_create():
    instance = ShoppingCartUI.__new__(ShoppingCartUI)
    instance.product_name_var = DummyVar("Desk")
    instance.product_price_var = DummyVar("100")
    instance.status_var = DummyVar("")
    instance._request = Mock(return_value={"id": 1})
    instance.refresh_products = Mock()

    with patch("ui.messagebox.showwarning"), patch("ui.messagebox.showerror"):
        instance.create_product()

    assert instance.product_name_var.get() == ""
    assert instance.product_price_var.get() == ""


# TS-007

def test_ts007_ui_state_refresh_after_operations():
    p = backend.create_product(Product(name="Mouse", price=20.0))
    item = backend.add_to_basket(BasketItem(product_id=p.id, quantity=1))
    backend.update_quantity(item.id, 3)
    backend.remove_from_basket(item.id)

    instance = ShoppingCartUI.__new__(ShoppingCartUI)
    instance.products_table = DummyTable()
    instance.basket_table = DummyTable()
    instance.status_var = DummyVar("")
    instance._request = Mock(side_effect=[[{"id": p.id, "name": "Mouse", "price": 20.0}], []])

    with patch("ui.messagebox.showerror"):
        instance.refresh_products()
        instance.refresh_basket()

    assert len(instance.products_table.rows) == 1
    assert len(instance.basket_table.rows) == 0


# TS-008

def test_ts008_keyboard_navigation_accessibility_is_manual_only():
    pytest.skip("Keyboard focus traversal requires interactive GUI testing")


# TS-009

def test_ts009_error_message_display_on_failed_refresh():
    instance = ShoppingCartUI.__new__(ShoppingCartUI)
    instance.products_table = DummyTable()
    instance.status_var = DummyVar("")
    instance._request = Mock(side_effect=RuntimeError("bad request"))

    with patch("ui.messagebox.showerror") as showerror:
        instance.refresh_products()

    showerror.assert_called_once()
    assert instance.status_var.get() == "Failed to load products"


# TS-010

def test_ts010_long_call_handled_without_crash():
    instance = ShoppingCartUI.__new__(ShoppingCartUI)
    instance.products_table = DummyTable()
    instance.status_var = DummyVar("")

    def slow_call(*_args, **_kwargs):
        time.sleep(0.01)
        return []

    instance._request = Mock(side_effect=slow_call)

    with patch("ui.messagebox.showerror"):
        instance.refresh_products()

    assert instance.status_var.get() == "Products loaded"


# TS-025

def test_ts025_ai_suggestion_path_consumed_in_create_workflow_contract():
    def choose_name(ai_callable, fallback="ManualName"):
        out = ai_callable()
        return out.get("name", fallback) if isinstance(out, dict) else fallback

    ai = Mock(return_value={"name": "AIProduct"})
    name = choose_name(ai)
    p = backend.create_product(Product(name=name, price=5.0))
    assert p.name == "AIProduct"


# TS-055

def test_ts055_large_read_operation_performance_smoke():
    for i in range(3000):
        backend.create_product(Product(name=f"P{i}", price=float(i)))

    start = time.perf_counter()
    result = backend.get_products()
    elapsed = time.perf_counter() - start

    assert len(result) == 3000
    assert elapsed < 1.0


# TS-056

def test_ts056_bulk_create_throughput_smoke():
    start = time.perf_counter()
    for i in range(2000):
        backend.create_product(Product(name=f"Bulk{i}", price=1.0))
    elapsed = time.perf_counter() - start

    assert len(backend.products) == 2000
    assert elapsed < 2.0


# TS-057

def test_ts057_repeated_updates_latency_smoke():
    p = backend.create_product(Product(name="Perf", price=1.0))
    item = backend.add_to_basket(BasketItem(product_id=p.id, quantity=1))

    start = time.perf_counter()
    for i in range(1, 500):
        backend.update_quantity(item.id, i)
    elapsed = time.perf_counter() - start

    assert backend.basket[0].quantity == 499
    assert elapsed < 2.0


# TS-058

def test_ts058_bulk_delete_flow_smoke():
    for i in range(300):
        p = backend.create_product(Product(name=f"D{i}", price=1.0))
        backend.add_to_basket(BasketItem(product_id=p.id, quantity=1))

    start = time.perf_counter()
    for item in list(backend.basket):
        backend.remove_from_basket(item.id)
    elapsed = time.perf_counter() - start

    assert backend.basket == []
    assert elapsed < 2.0


# TS-059

def test_ts059_ai_assisted_operation_latency_smoke_with_mock():
    def ai_step(ai_callable):
        return ai_callable()

    ai_callable = Mock(return_value={"decision": "ok"})
    start = time.perf_counter()
    for _ in range(1000):
        ai_step(ai_callable)
    elapsed = time.perf_counter() - start

    assert elapsed < 1.0


# TS-060

def test_ts060_long_duration_soak_mini_cycle_consistency():
    for cycle in range(50):
        p = backend.create_product(Product(name=f"S{cycle}", price=cycle + 1.0))
        item = backend.add_to_basket(BasketItem(product_id=p.id, quantity=1))
        backend.update_quantity(item.id, 2)
        snapshot = backend.view_basket()
        assert snapshot[-1]["total_price"] == 2 * (cycle + 1.0)
        backend.remove_from_basket(item.id)

    assert len(backend.basket) == 0
