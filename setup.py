import os.path
from setuptools import (find_packages, setup)


def get_version():
    version_file = os.path.join(os.path.dirname(__file__), 'meertrapdb', 'version.py')

    with open(version_file, 'r') as f:
        raw = f.read()

    items = {}
    exec(raw, None, items)

    return items['__version__']


def get_long_description():
    with open('README.md', 'r') as fd:
        long_description = fd.read()

    return long_description


setup(
    name='meertrapdb',
    version=get_version(),
    author='Fabian Jankowski',
    author_email='fjankowsk at gmail.com',
    description='Database code for MeerTRAP.',
    long_description=get_long_description(),
    long_description_content_type='text/markdown',
    url='https://bitbucket.org/jankowsk/meertrapdb',
    license='MIT',
    packages=find_packages(),
    package_data={
        'meertrapdb': ['config/*'],
        'psrmatch': ['catalogues/*.txt']
    },
    install_requires=[
        'astropy',
        'healpy',
        'matplotlib',
        'nose2',
        'numpy',
        'pandas',
        'pony',
        'pygedm',
        'pytz',
        'pyyaml',
        'requests',
        'scipy'
    ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
    zip_safe=False
)
