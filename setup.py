from setuptools import setup, find_packages

README = open('README.md').read()

setup(name='desper',
      classifiers=['Intended Audience :: Developers',
                   'Programming Language :: Python :: 3 :: Only',
                   'Topic :: Games/Entertainment'],
      python_requires='>=3.9',
      version='1.1.1post',
      description='A Python3 game development toolkit for resource and logic '
                  'management',
      long_description_content_type='text/markdown',
      long_description=README,
      url='http://github.com/Ball-Man/desper',
      author='Francesco Mistri',
      author_email='franc.mistri@gmail.com',
      license='MIT',
      packages=find_packages(),
      )
