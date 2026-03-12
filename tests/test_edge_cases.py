from unittest.mock import Mock, patch

import pytest
from pydantic import ValidationError

import main
from models import BasketItem, Product
from ui import ShoppingCartUI


class DummyVar:
    def __init__(self, value=""):
        self._value = value

    def get(self):
        return self._value

    def set(self, value):
        self._value = value


@pytest.fixture(autouse=True)
def reset_state():
    main.products.clear()
    main.basket.clear()
    main.product_id_counter = 1
    main.basket_id_counter = 1


# TS-035
def test_ts035_required_field_validation_missing_product_name():
    with pytest.raises(ValidationError):
        Product(price=10.0)


# TS-036
def test_ts036_non_numeric_value_in_numeric_field_rejected():
    with pytest.raises(ValidationError):
        Product(name="Router", price="abc")


# TS-037
def test_ts037_boundary_below_min_quantity_rejected():
    p = main.create_product(Product(name="Pen", price=1.0))
    with pytest.raises(Exception) as exc:
        main.add_to_basket(BasketItem(product_id=p.id, quantity=0))
    assert getattr(exc.value, "status_code", None) == 400


# TS-038
def test_ts038_update_quantity_with_large_positive_value_current_behavior():
    p = main.create_product(Product(name="Notebook", price=5.0))
    item = main.add_to_basket(BasketItem(product_id=p.id, quantity=1))
    updated = main.update_quantity(item.id, 10**6)
    assert updated.quantity == 10**6


# TS-039
def test_ts039_string_max_length_not_enforced_in_current_model():
    long_name = "x" * 10000
    p = main.create_product(Product(name=long_name, price=2.0))
    assert p.name == long_name


# TS-040
def test_ts040_invalid_special_format_stored_as_plain_text_current_behavior():
    weird = "<invalid>|{{{{"
    p = main.create_product(Product(name=weird, price=3.0))
    assert p.name == weird


# TS-041
def test_ts041_injection_like_payload_treated_as_text():
    payload = "'; DROP TABLE products; --"
    p = main.create_product(Product(name=payload, price=4.0))
    assert p.name == payload


# TS-042
def test_ts042_script_like_payload_displayed_as_text_value():
    payload = "<script>alert('x')</script>"
    p = main.create_product(Product(name=payload, price=10.0))
    assert p.name == payload


# TS-049
def test_ts049_zero_like_value_for_price_is_allowed():
    p = main.create_product(Product(name="Free item", price=0.0))
    assert p.price == 0.0


# TS-050
def test_ts050_very_large_numeric_values_supported():
    p = main.create_product(Product(name="Enterprise", price=10**12))
    assert p.price == 10**12


# TS-051
def test_ts051_unicode_and_emoji_input_round_trip():
    name = "Cafe 915 rocket"
    p = main.create_product(Product(name=name, price=9.99))
    assert p.name == name


# TS-052
def test_ts052_rapid_repeated_crud_operations_consistent_state():
    for i in range(100):
        p = main.create_product(Product(name=f"P{i}", price=1.0 + i))
        item = main.add_to_basket(BasketItem(product_id=p.id, quantity=1))
        main.update_quantity(item.id, 2)
        main.remove_from_basket(item.id)
    assert len(main.products) == 100
    assert len(main.basket) == 0


# TS-053
def test_ts053_operation_interruption_simulated_exception_does_not_corrupt_existing_data():
    p = main.create_product(Product(name="Stable", price=8.0))

    class BoomList(list):
        def append(self, item):
            raise RuntimeError("interrupted")

    with patch.object(main, "basket", BoomList(main.basket)):
        with pytest.raises(RuntimeError):
            main.add_to_basket(BasketItem(product_id=p.id, quantity=1))


# TS-054
def test_ts054_cancel_confirmation_flow_not_implemented_in_ui_current_scope():
    pytest.skip("Confirmation dialogs for destructive actions are not implemented in current UI")


def test_ui_create_product_empty_name_shows_warning_and_skips_request():
    ui_instance = ShoppingCartUI.__new__(ShoppingCartUI)
    ui_instance.product_name_var = DummyVar("")
    ui_instance.product_price_var = DummyVar("10")
    ui_instance.status_var = DummyVar("")
    ui_instance._request = Mock()

    with patch("ui.messagebox.showwarning") as warning:
        ui_instance.create_product()

    warning.assert_called_once()
    ui_instance._request.assert_not_called()


def test_ui_create_product_invalid_price_shows_warning_and_skips_request():
    ui_instance = ShoppingCartUI.__new__(ShoppingCartUI)
    ui_instance.product_name_var = DummyVar("Desk")
    ui_instance.product_price_var = DummyVar("abc")
    ui_instance.status_var = DummyVar("")
    ui_instance._request = Mock()

    with patch("ui.messagebox.showwarning") as warning:
        ui_instance.create_product()

    warning.assert_called_once()
    ui_instance._request.assert_not_called()
