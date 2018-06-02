import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="netblocks",
    version="0.0.1",
    description="Get the Google netblocks",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hm-distro/netblocks/tree/master/netblocks",
    packages=setuptools.find_packages(),
    classifiers=(
        "Programming Language :: Python :: 2",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ),
)