SHELL=/bin/bash

setup:
	python3 -m venv venv
	source venv/bin/activate && pip install -r requirements.txt

run:
	source venv/bin/activate && python main.py

clean:
	rm -fr 'venv'
	rm -fr '__pycache__'
