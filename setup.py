from setuptools import setup, find_packages

README = open('README.md').read()

setup(name='desper',
      classifiers=['Development Status :: 3 - Beta',
                   'Intended Audience :: Developers',
                   'Programming Language :: Python :: 3 :: Only',
                   'Topic :: Games/Entertainment'],
      version='1.0.0',
      description='A Python3 game development toolkit for resource and logic '
                  'management',
      long_description=README,
      url='http://github.com/Ball-Man/desper',
      author='Francesco Mistri',
      author_email='franc.mistri@gmail.com',
      license='MIT',
      packages=find_packages(),
      )
