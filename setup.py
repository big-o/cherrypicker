# Always prefer setuptools over distutils
from setuptools import setup, find_packages
from os import path


here = path.abspath(path.dirname(__file__))


# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()


# Copy dependencies from requirements file
with open(path.join(here, 'requirements.txt'), encoding='utf-8') as f:
    requirements = f.read().split('\n')


setup(
    name=__name__,
    version='0.0.0',
    description='Pluck and flatten complex data.',
    long_description=long_description,
    url='https://github.com/big-o/cherrypicker',
    classifiers=[  # Optional
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3'
    ],
    keywords='cherrypicker etl data',  # Optional
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),  # Required
    python_requires='>=3.0',
    install_requires=requirements,
    extras_require={
        'dev': ['check-manifest'],
        'test': ['coverage'],
    }
)
