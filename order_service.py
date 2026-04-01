# order_service.py - Order data and order-related actions
# Simulates a database of orders and provides functions to
# retrieve order status and initiate returns.

# Simulated order database (in production, this would query a real database)
ORDERS = {
    "ORD123": {
        "status": "Delayed",
        "expected_delivery": "Tomorrow"
    }
}


def get_order_status(order_id: str) -> str:
    """Look up an order by ID and return its current status."""
    order = ORDERS.get(order_id)
    if not order:
        return "Order not found."

    return (
        f"Order status: {order['status']}. "
        f"Expected delivery: {order['expected_delivery']}."
    )


def initiate_return(order_id: str) -> str:
    """Initiate a return for the given order ID."""
    if order_id not in ORDERS:
        return "Order not found. Cannot initiate return."

    return f"Return successfully initiated for order {order_id}."