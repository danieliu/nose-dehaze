from setuptools import setup

setup(
    name="nose-dehaze",
    version="0.1.0",
    description="A nosetests plugin to colorize error and failure output.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/danieliu/nose-dehaze",
    author="Daniel Liu",
    author_email="idaniel.liu@gmail.com",
    packages=["nose_dehaze"],
    license="MIT License",
    entry_points={
        "nose.plugins.0.10": [
            "nose_dehaze = nose_dehaze.plugin:Dehaze",
        ]
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Software Development :: Testing",
    ],
    install_requires=[
        'six',
        'termcolor',
    ],
)
