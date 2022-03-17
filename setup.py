from setuptools import setup, find_packages

with open("README.md", encoding="utf-8") as readme:
    LONG_DESCRIPTION = readme.read()

setup(
    name="pypedrive-api",
    version="0.2.2",
    description="Asyncio/aiohttp based library for interacting with the Pipedrive API.",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    author="Austin Howard",
    author_email="austin@tangibleintelligence.com",
    packages=find_packages("src"),
    package_dir={"": "src"},
    python_requires=">3.6.1",
    install_requires=[
        "aiohttp[speedups]>=3.8,<4", "pydantic[email]>=1.7.3,<2"
    ],
)
