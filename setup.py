from setuptools import setup, find_packages

setup(
    author="kokaito-git",
    name="kmodels",
    version="0.1.2.2",
    description="KModels",
    author_email="kokaito.git@gmail.com",
    url="https://github.com/kokaito-git/kmodels",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS",
        "Operating System :: POSIX :: Linux",
        "License :: OSI Approved :: MIT License",
    ],
    install_requires=[
        "pydantic",
        "typeguard",
        "kcolors"
    ],
    packages=find_packages(),
    python_requires=">=3.13",
    include_package_data=True,
)
