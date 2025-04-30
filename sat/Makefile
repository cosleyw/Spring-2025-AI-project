SHELL=/bin/bash

setup:
	python3 -m venv venv
	source venv/bin/activate && pip install -r requirements.txt

test:
	source venv/bin/activate && python -m unittest test_*.py

serve:
	source venv/bin/activate && fastapi dev --host 0.0.0.0 server.py

serve-prod:
	source venv/bin/activate && fastapi run server.py

run:
	source venv/bin/activate && python main.py

clean:
	rm -fr 'venv'
	rm -fr '__pycache__'
