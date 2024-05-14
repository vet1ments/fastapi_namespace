from glob import glob
from os.path import basename, splitext
from setuptools import find_packages, setup

setup(
    name='fastapi_namespace',
    version='0.1.1',
    python_requires='>=3.11.0',
    author="no hong seok",
    author_email="vet1ments@naver.com",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.108.0"
    ],
    tests_require=[
        "uvicorn>=0.9.0"
    ],
)