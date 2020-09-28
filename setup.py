from setuptools import setup, find_packages
from os.path import join, dirname

setup(
    name='mdclasses',
    version='0.13',
    packages=find_packages(),
    long_description=open(join(dirname(__file__), 'README.md'), encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    install_reqs=['lxml>=4.5.2']
)