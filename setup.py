from setuptools import setup, find_packages

setup(
    name="collaborative-ai-editor",
    version="0.1.0",
    packages=find_packages(include=['app', 'app.*']),
    include_package_data=True,
    install_requires=[
        "fastapi",
        "uvicorn",
        "python-multipart",
        "jinja2",
        "websockets",
        "httpx"  # Required for TestClient
    ],
    python_requires=">=3.10",
)
