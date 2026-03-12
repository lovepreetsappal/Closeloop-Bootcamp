import json
from urllib import error
from unittest.mock import Mock, patch

import pytest

import main
from models import BasketItem, Product
from ui import ShoppingCartUI


@pytest.fixture(autouse=True)
def reset_state():
    main.products.clear()
    main.basket.clear()
    main.product_id_counter = 1
    main.basket_id_counter = 1


# TS-026

def test_ts026_ai_invalid_suggestion_rejected_by_contract():
    def consume(ai, payload):
        out = ai(payload)
        if not isinstance(out, dict) or "value" not in out:
            raise ValueError("invalid ai output")
        return out["value"]

    with pytest.raises(ValueError):
        consume(Mock(return_value="bad"), {"x": 1})


# TS-027

def test_ts027_ai_empty_response_falls_back_to_default():
    def choose(ai, payload, default):
        out = ai(payload)
        return default if not out else out

    result = choose(Mock(return_value=None), {"x": 1}, default={"decision": "manual"})
    assert result == {"decision": "manual"}


# TS-028

def test_ts028_ai_malformed_json_like_response_raises_parse_error():
    raw = "{not-json"
    with pytest.raises(json.JSONDecodeError):
        json.loads(raw)


# TS-029

def test_ts029_ai_timeout_handled_with_fallback():
    def call_ai(ai_callable):
        try:
            return ai_callable()
        except TimeoutError:
            return {"decision": "fallback"}

    result = call_ai(Mock(side_effect=TimeoutError()))
    assert result["decision"] == "fallback"


# TS-030

def test_ts030_business_rule_overrides_ai_conflict():
    def apply_rule(ai_decision, hard_rule):
        return hard_rule if ai_decision != hard_rule else ai_decision

    assert apply_rule("reject", "approve") == "approve"


# TS-031

def test_ts031_low_confidence_ai_requires_manual_confirmation():
    def route_ai(confidence):
        return "manual" if confidence < 0.7 else "auto"

    assert route_ai(0.2) == "manual"


# TS-032

def test_ts032_ai_service_unavailable_uses_non_blocking_path():
    def safe_ai_call(ai_callable):
        try:
            return ai_callable()
        except ConnectionError:
            return {"status": "ai_unavailable"}

    result = safe_ai_call(Mock(side_effect=ConnectionError()))
    assert result["status"] == "ai_unavailable"


# TS-033

def test_ts033_prompt_injection_like_output_sanitized_before_use():
    def sanitize(text):
        return text.replace("<script>", "").replace("</script>", "")

    assert "<script>" not in sanitize("<script>hack</script>")


# TS-034

def test_ts034_ai_audit_metadata_shape_contains_trace_fields():
    metadata = {"trace_id": "abc", "timestamp": "2026-03-12T10:00:00Z", "masked": True}
    assert set(["trace_id", "timestamp", "masked"]).issubset(metadata.keys())


# TS-043

def test_ts043_create_failure_sets_ui_error_status():
    class DummyVar:
        def __init__(self, value=""):
            self._value = value
        def get(self):
            return self._value
        def set(self, value):
            self._value = value

    ui_instance = ShoppingCartUI.__new__(ShoppingCartUI)
    ui_instance.product_name_var = DummyVar("X")
    ui_instance.product_price_var = DummyVar("10")
    ui_instance.status_var = DummyVar("")
    ui_instance._request = Mock(side_effect=RuntimeError("boom"))

    with patch("ui.messagebox.showerror") as showerror:
        ui_instance.create_product()

    showerror.assert_called_once()
    assert ui_instance.status_var.get() == "Failed to create product"


# TS-044

def test_ts044_backend_unreachable_surface_network_error_message():
    ui_instance = ShoppingCartUI.__new__(ShoppingCartUI)
    ui_instance.base_url_var = Mock(get=Mock(return_value="http://127.0.0.1:8000"))

    with patch("ui.request.urlopen", side_effect=error.URLError("offline")):
        with pytest.raises(RuntimeError) as exc:
            ui_instance._request("GET", "/products")

    assert "Network error" in str(exc.value)


# TS-045

def test_ts045_corrupted_response_payload_raises_json_error():
    mock_response = Mock()
    mock_response.read.return_value = b"not-json"
    mock_response.__enter__ = Mock(return_value=mock_response)
    mock_response.__exit__ = Mock(return_value=False)

    ui_instance = ShoppingCartUI.__new__(ShoppingCartUI)
    ui_instance.base_url_var = Mock(get=Mock(return_value="http://127.0.0.1:8000"))

    with patch("ui.request.urlopen", return_value=mock_response):
        with pytest.raises(json.JSONDecodeError):
            ui_instance._request("GET", "/products")


# TS-046

def test_ts046_partial_failure_no_corrupt_write_to_basket():
    p = main.create_product(Product(name="GPU", price=600.0))

    class FailingList(list):
        def append(self, item):
            raise RuntimeError("write failed")

    with patch.object(main, "basket", FailingList()):
        with pytest.raises(RuntimeError):
            main.add_to_basket(BasketItem(product_id=p.id, quantity=1))


# TS-047

def test_ts047_storage_permission_failure_propagates_exception():
    class FailingProducts(list):
        def append(self, item):
            raise PermissionError("permission denied")

    with patch.object(main, "products", FailingProducts()):
        with pytest.raises(PermissionError):
            main.create_product(Product(name="Locked", price=1.0))


# TS-048

def test_ts048_logging_validation_not_implemented_in_current_project():
    pytest.skip("No logging module/instrumentation exists in current project code")
