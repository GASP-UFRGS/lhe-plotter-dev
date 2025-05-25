from setuptools import setup, find_packages

setup(
    name="lhe-plotter",
    version="0.1",
    description="LHE Plotter: ROOT histogram analysis for LHE files",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=[
        # Optional: leave empty if requirements are managed via requirements.txt
    ],
    entry_points={
        "console_scripts": [
            "lhe-plotter = lhe_plotter.__main__:main",
            "lhe-plotter-plot = lhe_plotter.plotter_from_root:main",
        ]
    },
    include_package_data=True,
    zip_safe=False,
)

