from setuptools import setup, find_packages
from os import path
from io import open

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='comdirect-ynab',
    version='0.0.1',
    description='Python library for comdirect API and YNAB interaction',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/zappingseb/comdirect_api',
    author='Sebastian Engel-Wolf',
    author_email='sebastian@mail-wolf.de',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    keywords='comdirect api banking ynab',
    packages=find_packages(include=['comdirect*', 'ynabimporter*']),
    python_requires='>=3.6, <4',
    project_urls={
        'Bug Reports': 'https://github.com/zappingseb/comdirect_api/issues',
        'Funding': 'https://www.mail-wolf.de',
        'Say Thanks!': 'http://twitter.com/zappingseb',
        'Source': 'https://github.com/zappingseb/comdirect_api/',
    },
)