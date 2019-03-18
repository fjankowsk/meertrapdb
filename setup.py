from setuptools import setup

setup(name='meertrapdb',
      version='0.1',
      description='Database code for MeerTRAP.',
      url='https://bitbucket.org/jankowsk/meertrapdb',
      author='Fabian Jankowski',
      author_email='fjankowsk at gmail.com',
      license='MIT',
      packages=['meertrapdb'],
      install_requires=[
            'matplotlib',
            'numpy',
            'pony',
            'pyyaml'
      ],
      zip_safe=False)