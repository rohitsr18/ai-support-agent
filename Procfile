web: PYTHONPATH=src gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 pragna.api.app:app -k uvicorn.workers.UvicornWorker
