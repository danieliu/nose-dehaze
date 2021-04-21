lint:
	flake8 nose_dehaze tests

test:
	nosetests tests

test-all:
	tox -p

black:
	black nose_dehaze tests

isort:
	isort nose_dehaze tests

mypy:
	mypy nose_dehaze

build:
	python -m build

publish: build
	pip install -U twine
	twine upload dist/*

publish-test: build
	pip install -U twine
	twine upload -r testpypi dist/*

.PHONY: build
