from setuptools import setup, find_packages

setup(
    name="scheduling",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "autogen",
        "google-auth-oauthlib",
        "google-auth-httplib2",
        "google-api-python-client",
        "python-dotenv",
    ],
    python_requires=">=3.8",
) 