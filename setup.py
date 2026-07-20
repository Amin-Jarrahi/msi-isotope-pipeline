from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="msi-isotope-pipeline",
    version="2.0.0",
    author="Alex(Amin) Jarrahi",
    author_email="alexajarrahi@gmail.com",
    description="Spatial-statistics-driven pipeline for isotope and adduct detection in MSI data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Amin-Jarrahi/msi-isotope-pipeline",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.9",
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
    ],
)
