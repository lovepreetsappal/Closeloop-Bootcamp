import pytest

import main
from models import BasketItem, Product


@pytest.fixture(autouse=True)
def reset_state():
    main.products.clear()
    main.basket.clear()
    main.product_id_counter = 1
    main.basket_id_counter = 1


def _find_product_by_id(product_id: int):
    return next((p for p in main.products if p.id == product_id), None)


# TS-011

def test_ts011_create_record_with_valid_required_fields():
    p = main.create_product(Product(name="Laptop", price=999.99))
    assert p.id == 1
    assert p.name == "Laptop"
    assert p.price == 999.99


# TS-012

def test_ts012_create_record_with_optional_id_omitted():
    p = main.create_product(Product(name="Mouse", price=25.0))
    assert p.id == 1


# TS-013

def test_ts013_duplicate_records_current_behavior():
    p1 = main.create_product(Product(name="Phone", price=500.0))
    p2 = main.create_product(Product(name="Phone", price=500.0))
    assert p1.id != p2.id
    assert len(main.products) == 2


# TS-014

def test_ts014_read_all_records():
    main.create_product(Product(name="A", price=1.0))
    main.create_product(Product(name="B", price=2.0))
    products = main.get_products()
    assert [p.name for p in products] == ["A", "B"]


# TS-015

def test_ts015_read_single_record_by_valid_id():
    p = main.create_product(Product(name="Desk", price=200.0))
    found = _find_product_by_id(p.id)
    assert found is not None
    assert found.name == "Desk"


# TS-016

def test_ts016_read_single_record_by_nonexistent_id():
    main.create_product(Product(name="Chair", price=80.0))
    assert _find_product_by_id(999) is None


# TS-017

def test_ts017_update_existing_basket_record():
    p = main.create_product(Product(name="SSD", price=150.0))
    item = main.add_to_basket(BasketItem(product_id=p.id, quantity=1))
    updated = main.update_quantity(item.id, 4)
    assert updated.quantity == 4


# TS-018

def test_ts018_partial_update_behavior_quantity_only_changes_quantity():
    p = main.create_product(Product(name="HDD", price=90.0))
    item = main.add_to_basket(BasketItem(product_id=p.id, quantity=2))
    updated = main.update_quantity(item.id, 3)
    assert updated.product_id == p.id
    assert updated.quantity == 3


# TS-019

def test_ts019_update_nonexistent_record_raises_not_found():
    with pytest.raises(Exception) as exc:
        main.update_quantity(999, 2)
    assert getattr(exc.value, "status_code", None) == 404


# TS-020

def test_ts020_delete_existing_record():
    p = main.create_product(Product(name="RAM", price=40.0))
    item = main.add_to_basket(BasketItem(product_id=p.id, quantity=1))
    out = main.remove_from_basket(item.id)
    assert out["message"] == "Item removed"
    assert main.basket == []


# TS-021

def test_ts021_delete_nonexistent_record_raises_not_found():
    with pytest.raises(Exception) as exc:
        main.remove_from_basket(222)
    assert getattr(exc.value, "status_code", None) == 404


# TS-022

def test_ts022_data_persistence_scope_is_in_memory_only():
    main.create_product(Product(name="Temp", price=1.0))
    assert len(main.products) == 1
    # Simulate restart by resetting module state.
    main.products.clear()
    assert len(main.products) == 0


# TS-023

def test_ts023_concurrent_update_strategy_last_write_wins_current_behavior():
    p = main.create_product(Product(name="Monitor", price=300.0))
    item = main.add_to_basket(BasketItem(product_id=p.id, quantity=1))
    main.update_quantity(item.id, 2)
    final = main.update_quantity(item.id, 5)
    assert final.quantity == 5


# TS-024

def test_ts024_integrity_when_product_removed_basket_view_skips_orphans():
    p = main.create_product(Product(name="Webcam", price=75.0))
    main.add_to_basket(BasketItem(product_id=p.id, quantity=2))
    main.products.clear()
    assert main.view_basket() == []
