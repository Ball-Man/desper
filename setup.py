from setuptools import setup

README = open('README.md').read()
REQUIREMENTS = open('requirements.txt').read().splitlines()

setup(name='desper',
      classifiers=['Development Status :: 3 - Alpha',
                   'Intended Audience :: Developers',
                   'Programming Language :: Python :: 3 :: Only',
                   'Topic :: Games/Entertainment'],
      version='0.1',
      description='A Python3 game development toolkit, based on open source '
                  + 'projects.',
      long_description=README,
      url='http://github.com/Ball-Man/desper',
      author='Francesco Mistri',
      author_email='franc.mistri@gmail.com',
      license='MIT',
      packages=['desper', 'desper.core', 'desper.glet'],
      install_requires=REQUIREMENTS
      )
