# nose-dehaze

A [nosetests](https://nose.readthedocs.io/en/latest/) plugin to format and colorize test failure output for readability.

## Installation

```bash
pip install nose-dehaze
```

## Usage

Load the plugin explicitly when calling nosetests:

```bash
nosetests --dehaze
```

or set the environment variable:

```bash
export NOSE_DEHAZE=1

nosetests
```

## Development

Refer to `Makefile` for commands to test, autoformat, lint, typecheck, etc.

```bash
pip install -r requirements.txt       # minimum to run code
pip install -r requirements-dev.txt   # for autoformat, lint, type checking, debugging
pip install -r requirements-test.txt  # for running tests
```

### Testing

Running 

```bash
# simply run tests
make test

# run tests with all supported python versions
make test-all
```
