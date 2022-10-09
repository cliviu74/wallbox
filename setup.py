import os
from setuptools import setup


def read(name):
    return open(os.path.join(os.path.dirname(__file__), name)).read()


setup(
    name="wallbox",
    version="0.4.10",
    description="Module for interacting with Wallbox EV charger api",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    keywords="",
    author="Liviu Chiribuca",
    author_email="cliviu74@yahoo.com",
    url="https://github.com/cliviu74/wallbox",
    license="Apache 2",
    packages=["wallbox"],
    install_requires=["requests>=2.22.0", "simplejson>=3.16.0", "aenum>=3.1.8"],
    python_requires=">=3.7",
    classifiers=["Programming Language :: Python :: 3",],
)
