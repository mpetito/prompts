from dataclasses import dataclass
from decimal import Decimal

TAX_RATE = Decimal("0.08")

PRODUCTS = {
    "widget": Decimal("4.50"),
    "gadget": Decimal("12.00"),
    "gizmo": Decimal("27.25"),
}


@dataclass(frozen=True)
class LineItem:
    sku: str
    quantity: int


@dataclass(frozen=True)
class Order:
    customer_id: str
    items: list[LineItem]
    loyalty_years: int


class InvalidRequest(Exception):
    pass


def parse_order(body: dict) -> Order:
    customer_id = body.get("customer_id")
    if not isinstance(customer_id, str) or not customer_id:
        raise InvalidRequest("customer_id must be a non-empty string")

    raw_items = body.get("items")
    if not isinstance(raw_items, list) or not raw_items:
        raise InvalidRequest("items must be a non-empty list")

    items = []
    for raw in raw_items:
        sku = raw.get("sku") if isinstance(raw, dict) else None
        quantity = raw.get("quantity") if isinstance(raw, dict) else None
        if sku not in PRODUCTS:
            raise InvalidRequest(f"unknown sku: {sku!r}")
        if not isinstance(quantity, int) or quantity < 1:
            raise InvalidRequest(f"quantity for {sku} must be a positive integer")
        items.append(LineItem(sku=sku, quantity=quantity))

    loyalty_years = body.get("loyalty_years", 0)
    if not isinstance(loyalty_years, int) or loyalty_years < 0:
        raise InvalidRequest("loyalty_years must be a non-negative integer")

    return Order(customer_id=customer_id, items=items, loyalty_years=loyalty_years)


def _subtotal(items: list[LineItem]) -> Decimal:
    return sum((PRODUCTS[item.sku] * item.quantity for item in items), Decimal("0"))


def _discount_rate(subtotal: Decimal, loyalty_years: int) -> Decimal:
    rate = Decimal("0")
    if subtotal >= Decimal("100"):
        rate = Decimal("0.05")
    if subtotal >= Decimal("250"):
        rate = Decimal("0.10")
    if loyalty_years >= 3:
        rate += Decimal("0.02")
    return rate


def _round(amount: Decimal) -> Decimal:
    return amount.quantize(Decimal("0.01"))


def _summarize(order: Order) -> dict:
    subtotal = _subtotal(order.items)
    rate = _discount_rate(subtotal, order.loyalty_years)
    discount = _round(subtotal * rate)
    taxable = subtotal - discount
    tax = _round(taxable * TAX_RATE)
    return {
        "customer_id": order.customer_id,
        "item_count": sum(item.quantity for item in order.items),
        "subtotal": str(_round(subtotal)),
        "discount_rate": str(rate),
        "discount": str(discount),
        "tax": str(tax),
        "total": str(_round(taxable + tax)),
    }


def price_order(body: dict) -> dict:
    """Public entry point: validate the request body, then price it."""
    order = parse_order(body)
    return _summarize(order)
