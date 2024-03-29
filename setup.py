# Always prefer setuptools over distutils
import importlib.util
import os

from setuptools import find_packages, setup

about = None
for root, dirs, files in os.walk("."):
    for _dir in dirs:
        if _dir.startswith("."):
            continue

        for subroot, subdirs, subfiles in os.walk(_dir):
            for subfile in subfiles:
                if subfile != "__about__.py":
                    continue

                path = os.path.join(subroot, subfile)
                spec = importlib.util.spec_from_file_location("about", path)
                about = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(about)

if about is None:
    raise RuntimeError("Unable to find version string.")

# Get the long description from the README file
with open("README.rst", encoding="utf-8") as f:
    long_description = f.read()


def parse_requirements(filename):
    # Copy dependencies from requirements file
    with open(filename, encoding="utf-8") as f:
        requirements = [line.strip() for line in f.read().splitlines()]
        requirements = [
            line.split("#")[0].strip()
            for line in requirements
            if not line.startswith("#")
        ]

    return requirements


setup(
    name=about.__name__,
    version=about.__version__,
    description=about.__description__,
    long_description=long_description,
    url=about.__url__,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    keywords="cherrypicker data etl extract flatten jquery",
    packages=find_packages(exclude=["contrib", "docs", "tests"]),
    python_requires=">=3.6",
    install_requires=parse_requirements("requirements.txt"),
    extras_require={
        "dev": parse_requirements("requirements-dev.txt"),
        "test": parse_requirements("requirements-test.txt"),
    },
)
