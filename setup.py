from setuptools import setup, find_packages

setup(
    name="lhe-plotter",
    version="0.1",
    description="LHE Plotter: ROOT histogram analysis for LHE files",
    author="diemort",
    author_email="cms@ufrgs.br",
    packages=find_packages(),
    install_requires=[],
    entry_points={
        "console_scripts": [
            "lhe-parser  = lhe_plotter.__main__:main",
            "lhe-plotter = lhe_plotter.plotter:main",
        ]
    },
    include_package_data=True,
    zip_safe=False,
)

