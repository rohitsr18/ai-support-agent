"""
Order management service.

Provides business logic for:
- Order status lookup by ID
- Return initiation workflow

Uses repository pattern for data access, allowing easy swap
between in-memory (demo) and database (production) backends.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict


class Order:
    """
    Order data model.
    
    Attributes:
        order_id: Unique identifier (e.g., 'ORD123')
        status: Current state ('Delivered', 'Delayed', etc.)
        expected_delivery: ETA string for customer display
    """

    def __init__(self, order_id: str, status: str, expected_delivery: str):
        self.order_id = order_id
        self.status = status
        self.expected_delivery = expected_delivery


class OrderRepository(ABC):
    """
    Abstract data access interface for orders.
    
    Implement this to connect to real databases (PostgreSQL, DynamoDB, etc.)
    while keeping the OrderService unchanged.
    """

    @abstractmethod
    def get_order(self, order_id: str) -> Optional[Order]:
        """Fetch an order by ID or return None."""
        pass
    
    @abstractmethod
    def save_return(self, order_id: str) -> bool:
        """Record a return request for an order."""
        pass


class SimulatedOrderRepository(OrderRepository):
    """
    In-memory mock repository for development and demos.
    
    Pre-seeded with sample order ORD123 for walkthrough testing.
    All data resets when the server restarts.
    """

    def __init__(self):
        # Sample order for demo/testing purposes
        self._orders: Dict[str, Order] = {
            "ORD123": Order(
                order_id="ORD123",
                status="Delayed",
                expected_delivery="Tomorrow"
            )
        }
        # Tracks which orders have return requests this session
        self._returns: set[str] = set()
    
    def get_order(self, order_id: str) -> Optional[Order]:
        return self._orders.get(order_id)
    
    def save_return(self, order_id: str) -> bool:
        if order_id in self._orders:
            self._returns.add(order_id)
            return True
        return False


class OrderService:
    """
    Business logic layer for order operations.
    
    Accepts a repository for data access. Defaults to SimulatedOrderRepository
    if none provided (useful for local dev without database setup).
    """

    def __init__(self, repository: Optional[OrderRepository] = None):
        # Use mock repo by default; inject real repo in production
        self.repository = repository or SimulatedOrderRepository()
    
    def get_status(self, order_id: str) -> str:
        """Return human-readable status text for an order."""
        order = self.repository.get_order(order_id)
        
        if not order:
            return "Order not found."
        
        return (
            f"Order status: {order.status}. "
            f"Expected delivery: {order.expected_delivery}."
        )
    
    def initiate_return(self, order_id: str) -> str:
        """Start return workflow for a known order."""
        order = self.repository.get_order(order_id)
        
        if not order:
            return "Order not found. Cannot initiate return."
        
        success = self.repository.save_return(order_id)
        
        if success:
            return f"Return successfully initiated for order {order_id}."
        else:
            return f"Failed to initiate return for order {order_id}."


def get_order_status(order_id: str) -> str:
    """Backward-compatible function wrapper for status lookup."""
    service = OrderService()
    return service.get_status(order_id)


def initiate_return(order_id: str) -> str:
    """Backward-compatible function wrapper for return initiation."""
    service = OrderService()
    return service.initiate_return(order_id)
