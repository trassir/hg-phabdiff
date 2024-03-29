import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="hg-phabdiff",
    version="0.1",
    author="Vladimir Looze",
    author_email="woldemar@mimas.ru",
    description="Mercurial extension for transparently applying phabricator diffs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/trassir/hg-phabdiff",
    packages=setuptools.find_packages(where='src'),
    # When your source code is in a subdirectory under the project root, e.g.
    # `src/`, it is necessary to specify the `package_dir` argument.
    package_dir={'': 'src'},
    license="GNU General Public License v3 (GPLv3)",
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers"
    ],
    python_requires=">=3.6",
    install_requires=[
        "mercurial>=5.8",
        "phabricator>=0.7.0",
        "hexdump",
        "brotli==1.0.9", # either hg or phabricator needs this but does not install. hg-phabdiff fails without this.
        ]
)
