from glob import glob
from os.path import basename, splitext
from setuptools import find_packages, setup

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name='fastapi_namespace_vet1ments',
    description="For FastAPI Routing Class",
    version='{{VERSION_PLACEHOLDER}}',
    long_description=long_description,
    long_description_content_type='text/markdown',
    python_requires='>=3.11.0',
    author="no hong seok",
    author_email="vet1ments@naver.com",
    maintainer="no hong seok",
    maintainer_email="vet1ments@naver.com",
    project_urls={
        "Repository": "https://github.com/vet1ments/fastapi_namespace"
    },
    license="MIT",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.108.0"
    ],
    tests_require=[
        "uvicorn>=0.9.0"
    ],
)