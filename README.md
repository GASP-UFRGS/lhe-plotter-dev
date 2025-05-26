# LHE Plotter

**LHE Plotter** is a modular Python toolkit for parsing, processing, and visualizing data from LHE (Les Houches Event) files. Designed for high-energy physics workflows, it offers configurable histogramming, event filtering, and automatic ROOT output generation.

## Features

- Parse LHE files with custom kinematic filters
- Histogram definitions from YAML configuration
- ROOT-integrated plotting with export to `.root`, `.png`, `.pdf`, `.C`
- Command-line interface for easy batch processing
- Summary table in CSV format
- Test suite with regression check
- Integrated Sphinx documentation

## Project Structure

```
lhe-plotter-dev/
├── lhe_plotter/           # Main Python package
│   ├── __init__.py
│   ├── __main__.py
│   ├── main_cli.py
│   ├── parser.py
│   ├── process.py
│   ├── histo.py
│   ├── plotter.py
│   ├── histograms.yaml
│   ├── root_style.yaml
│   └── input.dat
├── test/                  # Test scripts and input
│   ├── run_test.sh
│   ├── test.lhe
│   ├── input_test.dat
│   ├── histograms_test.yaml
│   ├── root_style_test.yaml
│   ├── test_output/
│   │   ├── all_plots.pdf
│   │   ├── output.root
│   │   ├── pt_single_top.C
│   │   ├── pt_single_top.pdf
│   │   ├── pt_single_top.png
│   │   ├── pt_single_top.root
│   │   └── summary.csv
├── doc/                   # Sphinx documentation
│   ├── init_sphynx.sh
│   ├── requirements.txt
│   └── source/
├── .github/
│   └── workflows/test.yml
├── setup.py
├── requirements.txt
├── setup_env.sh
├── LICENSE
└── README.md
```

## Installation

Clone the repository and install in editable mode:

```bash
git clone https://github.com/GASP-UFRGS/lhe-plotter-dev.git
cd lhe-plotter-dev
python3 -m venv lhe-env
source lhe-env/bin/activate
pip install -e .
```

If needed, install additional dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the main CLI from the root directory:

```bash
lhe_parser \
    --input input.dat \
    --histos histograms.yaml \
    --style root_style.yaml \
    --output output.root
```

To display command-line options:

```bash
lhe-parser --help
lhe-plotter --help
```

## Testing

Run the test pipeline locally:

```bash
bash test/run_test.sh
```

This creates the following files in `test_output/`:

- `output.root`
- `summary.csv`
- `pt_single_top.{png,pdf,root,C}`
- `all_plots.pdf`

These outputs are used to validate that parsing, plotting, and export worked as expected.

## Documentation

Build HTML documentation with:

```bash
cd doc
bash init_sphynx.sh clean  # Optional: reset Sphinx setup
bash init_sphynx.sh
make html
open build/html/index.html
```

## Continuous Integration

The test workflow is defined in [`.github/workflows/test.yml`](.github/workflows/test.yml).

To test it locally using [act](https://github.com/nektos/act):

```bash
brew install act
act --container-architecture linux/amd64 -j test
```

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

