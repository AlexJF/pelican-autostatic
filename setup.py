from setuptools import setup

with open("README.rst") as f:
    long_description = f.read()

setup(
    # Basic package information:
    name="pelican-autostatic",
    version="1.0.0",
    py_modules=("autostatic",),
    # Packaging options:
    zip_safe=False,
    include_package_data=True,
    # Package dependencies:
    install_requires=["pelican>=3.4.0"],
    # Metadata for PyPI:
    author="Alexandre Fonseca",
    author_email="alexandrejorgefonseca@gmail.com",
    license="Apache",
    url="https://github.com/AlexJF/pelican-autostatic",
    download_url="https://github.com/AlexJF/pelican-autostatic/archive/v0.2.2.zip",
    keywords="pelican blog static generic automatic",
    description=(
        "A generator for Pelican allowing flexible referencing " "of static content"
    ),
    long_description=long_description,
)
