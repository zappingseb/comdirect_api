"""Python library for comdirect API interaction

"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
from os import path


# io.open is needed for projects that support Python 2.7
# It ensures open() defaults to text mode with universal newlines,
# and accepts an argument to specify the text encoding
# Python 3 only projects can skip this import
from io import open

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Arguments marked as "Required" below must be included for upload to PyPI.
# Fields marked as "Optional" may be commented out.
setup(
    name='comdirect',  # Required
    version='0.0.1',  # Required
    description='Python library for comdirect API interaction',  # Optional
    url='https://github.com/zappingseb/comdirect_api',  # Optional
    author='Sebastian Engel-Wolf',  # Optional
    author_email='sebastian@mail-wolf.de',  # Optional

    # Classifiers help users find your project by categorizing it.
    #
    # For a list of valid classifiers, see https://pypi.org/classifiers/
    classifiers=[  # Optional
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Banking API :: German Banks',
        'License :: OSI Approved :: GNU GPLv3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    keywords='comdirect api banking',  # Optional

    # When your source code is in a subdirectory under the project root, e.g.
    # `src/`, it is necessary to specify the `package_dir` argument.
    package_dir={'': 'comdirect'},  # Optional
    packages=find_packages(where='comdirect'),  # Required
    python_requires='>=3.6, <4',
    project_urls={  # Optional
        'Bug Reports': 'https://github.com/zappingseb/comdirect_api/issues',
        'Funding': 'https://www.mail-wolf.de',
        'Say Thanks!': 'http://twitter.com/zappingseb',
        'Source': 'https://github.com/zappingseb/comdirect_api/',
    },
)