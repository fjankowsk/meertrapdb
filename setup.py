import os.path
from setuptools import setup

def get_version():
    version_file = os.path.join(os.path.dirname(__file__), 'meertrapdb', 'version.py')

    with open(version_file, 'r') as f:
        raw = f.read()

    items = {}
    exec(raw, None, items)

    return items['__version__']

setup(name='meertrapdb',
      version=get_version(),
      description='Database code for MeerTRAP.',
      url='https://bitbucket.org/jankowsk/meertrapdb',
      author='Fabian Jankowski',
      author_email='fjankowsk at gmail.com',
      license='MIT',
      packages=['meertrapdb'],
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
      zip_safe=False)
