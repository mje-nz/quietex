"""quietex setup."""
from setuptools import setup

with open("Readme.md") as f:
    readme_lines = f.readlines()
    long_description = "\n".join(readme_lines[: readme_lines.index("## Development\n")])


setup(
    name="quietex",
    version="0.2.0pre",
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
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Text Processing :: Markup :: LaTeX",
    ],
    packages=["quietex"],
    # TODO: This is broken now that I have everything in quietex/__main__.py
    entry_points={"console_scripts": ["quietex=quietex:main"]},
    python_requires=">=3.5",
    install_requires=["attrs", "pexpect"],
    zip_safe=False,
)
