"""
Server launcher with automatic port fallback for local development.

Features:
    - Reads PORT/HOST from environment for cloud deployments
    - Falls back to 8000+N if preferred port is occupied locally
    - Prints startup URL for easy browser access

Usage:
    python scripts/start_server.py
    PORT=9000 python scripts/start_server.py
"""

import os
import socket

import uvicorn


def _is_port_free(host: str, port: int) -> bool:
    """
    Check if a port is available for binding.
    
    Args:
        host: Network interface to check (e.g., "127.0.0.1").
        port: TCP port number to test.
        
    Returns:
        True if the port can be bound, False if already in use.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
            return True
        except OSError:
            return False


def choose_port(preferred_port: int, host: str = "127.0.0.1", max_tries: int = 50) -> int:
    """
    Find the first available port starting from the preferred port.
    
    Iterates from preferred_port to preferred_port + max_tries,
    returning the first port that can be bound.
    
    Args:
        preferred_port: Starting port number to try.
        host: Network interface to bind on.
        max_tries: Maximum number of consecutive ports to check.
        
    Returns:
        First available port number.
        
    Raises:
        RuntimeError: If no port is available in the range.
    """
    for offset in range(max_tries + 1):
        port = preferred_port + offset
        if _is_port_free(host, port):
            return port
    raise RuntimeError("No available port found in the allowed range")


def main() -> None:
    """
    Start the Uvicorn server with appropriate port selection.
    
    Cloud deployments: Uses PORT env var directly (required by Cloud Run).
    Local development: Auto-selects next free port if 8000 is busy.
    """
    preferred_port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")

    # Cloud platforms set PORT explicitly; honor it without fallback
    if "PORT" in os.environ:
        port = preferred_port
    else:
        # Local dev: find available port to avoid "address in use" errors
        port = choose_port(preferred_port)

    print(f"Starting server on http://127.0.0.1:{port}")
    uvicorn.run("pragna.api.app:app", host=host, port=port)


if __name__ == "__main__":
    main()
