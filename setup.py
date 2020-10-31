"""QuieTeX setup."""
# pylint: disable=invalid-name
from setuptools import setup

with open("Readme.md") as f:
    readme_lines = f.readlines()
    long_description = "\n".join(readme_lines[: readme_lines.index("## Development\n")])

meta = {}  # type: ignore
with open("src/quietex/_meta.py") as fp:
    exec(fp.read(), meta)  # pylint: disable=exec-used

tests_require = ["pyte", "pytest", "pytest-cov"]


setup(
    name="quietex",
    version=meta["__version__"],
    description="Filter output of pdflatex.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mje-nz/quietex",
    author="Matthew Edwards",
    license="BSD 3-Clause",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Text Processing :: Markup :: LaTeX",
    ],
    packages=["quietex"],
    package_dir={"": "src"},
    package_data={"quietex": ["latexmkrc"]},
    entry_points={"console_scripts": ["quietex=quietex.__main__:main"]},
    python_requires=">=3.7",
    install_requires=["attrs", "blessings", "pexpect", "pygments"],
    extras_require={"test": tests_require},
    tests_require=tests_require,
    zip_safe=True,
)
