lint:
	flake8 dehaze tests

test:
	nosetests

black:
	black nose_dehaze tests

isort:
	isort nose_dehaze tests
