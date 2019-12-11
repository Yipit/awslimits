SHELL := /bin/bash

setup:
	python setup.py develop
	pip install -r requirements.txt

run:
	@python awslimits/server.py

test:
	@py.test tests/

travis:
	nosetests --with-coverage ./tests/

publish:
	python setup.py sdist bdist_wheel upload

deploy: setup
	python scripts/setup_iam_role.py staging zappa_settings.json
	flask-zappa deploy staging zappa_settings.json
