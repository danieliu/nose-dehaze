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
