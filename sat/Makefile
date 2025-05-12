SHELL=/bin/bash

setup:
	python3 -m venv venv
	source venv/bin/activate && pip install -r requirements.txt

test:
	source venv/bin/activate && python -m unittest test_*.py

serve:
	source venv/bin/activate && uvicorn server:app --reload --host 0.0.0.0 --timeout-keep-alive 30 --port 80 >> log.dev 2>&1

serve-prod:
	source venv/bin/activate && uvicorn server:app --host 0.0.0.0 --timeout-keep-alive 600 --port 80 >> access.log

run:
	source venv/bin/activate && python main.py

clean:
	rm -fr 'venv'
	rm -fr '__pycache__'
