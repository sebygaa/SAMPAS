from setuptools import setup, find_packages

setup(
    name="SAMPAS",
    version="0.1.0",
    author="Your Name",
    description="Simulation-Aided Material & Processes Analysis System",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.21",
    ],
    entry_points={
        "console_scripts": [
            "sampas=sampas.app:main",
        ],
        "gui_scripts": [
            "sampas-gui=sampas.app:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
