lint:
	flake8 nose_dehaze tests

test:
	nosetests tests

black:
	black nose_dehaze tests

isort:
	isort nose_dehaze tests

mypy:
	mypy nose_dehaze
