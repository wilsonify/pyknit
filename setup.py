import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pyknit", 
    version="0.0.1",
    author="Terri Oda",
    author_email="terri@toybox.ca",
    description="A set of tools for knitters to create charts and eventually more.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/terriko/pyknit",
    packages=setuptools.find_packages(),
    classifiers=[
        "Development Status :: 1 - Planning",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
