SHELL=/bin/bash

setup:
	python3 -m venv venv
	source venv/bin/activate && pip install -r requirements.txt

serve:
	source venv/bin/activate && fastapi dev server.py

serve-prod:
	source venv/bin/activate && fastapi run server.py

run:
	source venv/bin/activate && python main.py

clean:
	rm -fr 'venv'
	rm -fr '__pycache__'
