from glob import glob
from os.path import basename, splitext
from setuptools import find_packages, setup

setup(
    name='fastapi_namespace',
    description="For FastAPI Routing Class",
    version='0.1.3',
    python_requires='>=3.11.0',
    author="no hong seok",
    author_email="vet1ments@naver.com",
    maintainer="no hong seok",
    maintainer_email="vet1ments@naver.com",
    download_url="https://github.com/vet1ments/fastapi_namespace",
    license="MIT",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.108.0"
    ],
    tests_require=[
        "uvicorn>=0.9.0"
    ],
)