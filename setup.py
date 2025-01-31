from setuptools import setup, find_packages

setup(
    name="collaborative-ai-editor",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "python-multipart",
        "jinja2",
        "websockets"
    ],
)
