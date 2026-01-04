"""Setup script for AnthroKit package."""

from setuptools import setup, find_packages

setup(
    name="anthrokit",
    version="1.0.0",
    packages=find_packages(include=["anthrokit", "anthrokit.*"]),
    include_package_data=True,
    package_data={
        "anthrokit": ["anthrokit.yaml"],
    },
)
