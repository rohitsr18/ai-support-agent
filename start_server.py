import os
import socket

import uvicorn


def _is_port_free(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
            return True
        except OSError:
            return False


def choose_port(preferred_port: int, host: str = "127.0.0.1", max_tries: int = 50) -> int:
    for offset in range(max_tries + 1):
        port = preferred_port + offset
        if _is_port_free(host, port):
            return port
    raise RuntimeError("No available port found in the allowed range")


def main() -> None:
    # Respect PORT if provided (Cloud Run), otherwise start at 8000 and auto-fallback.
    preferred_port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")

    # For local runs without PORT, auto-pick next available if 8000 is busy.
    if "PORT" in os.environ:
        port = preferred_port
    else:
        port = choose_port(preferred_port)

    print(f"Starting server on http://127.0.0.1:{port}")
    uvicorn.run("app:app", host=host, port=port)


if __name__ == "__main__":
    main()
