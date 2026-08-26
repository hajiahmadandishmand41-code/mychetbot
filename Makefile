install:
	pip install -r requirements.txt
run:
	python -m interfaces.cli
api:
	uvicorn interfaces.api_server:app --host 127.0.0.1 --port 8765
test:
	pytest -q
