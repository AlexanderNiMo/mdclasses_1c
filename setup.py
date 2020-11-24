from setuptools import setup, find_packages
from os.path import join, dirname
from pkg_resources import parse_requirements


def load_requirements(fname: str) -> list:
    requirements = []
    with open(fname, 'r') as fp:
        for req in parse_requirements(fp.read()):
            extras = '[{}]'.format(','.join(req.extras)) if req.extras else ''
            requirements.append(
                '{}{}{}'.format(req.name, extras, req.specifier)
            )
    return requirements


setup(
    name='mdclasses',
    author='Alexander_NiMo',
    author_email='binipox@gmail.com',
    lisense='MIT',
    version='0.14',
    long_description=open(join(dirname(__file__), 'README.md'), encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/AlexanderNiMo/designer_cmd',
    platforms=['Windows','Linux'],
    packages=find_packages(exclude=['tests']),
    install_requires=load_requirements('requirements.txt'),
    include_package_data=True,
    test_suite='mdclasses.tests'
)