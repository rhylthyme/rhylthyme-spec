from setuptools import setup, find_packages

setup(
    name="rhylthyme-spec",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "jsonschema>=4.0.0",
    ],
    python_requires=">=3.8",
    author="Rhylthyme Team",
    author_email="your.email@example.com",
    description="JSON schemas and specifications for Rhylthyme programs and environments",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/rhylthyme-spec",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
) 