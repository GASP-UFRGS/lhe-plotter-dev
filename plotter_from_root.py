"""
A ROOT-based plotting utility to visualize histograms stored in ROOT files.

This script loads a `.root` file containing pre-filled histograms and generates
publication-quality plots using the ROOT framework. Configuration is handled via
YAML or DAT files, allowing customization of styles, axis labels, log scales, stacking,
and dummy data overlays.

Main Features
-------------
- Automatically groups histograms by base name and overlays multiple processes.
- Supports 1D and 2D histograms.
- Custom axis labels, units, styles, and color schemes via YAML.
- Generates PNG, PDF, and ROOT macro files for each plot.
- Supports multipage PDF export.
- Optional dummy data generation and overlay.

Functions
---------
- plot_histograms_from_root : Main function for rendering histograms from a ROOT file.
- draw_histogram_group : Core logic for drawing and formatting individual histogram panels.
- generate_dummy_data : Create synthetic (smeared) data overlay.
- load_style_yaml : Load style configuration from a YAML file.
- apply_root_style : Apply ROOT commands defined in the style YAML.
- group_histograms_by_basename : Organize histograms by observable name.

Command Line Interface
----------------------
Supports batch and single-file execution:

    python plotter_from_root.py --input FILE.root --config input.yaml --histos histograms.yaml --outdir plots/

Requires
--------
- ROOT (PyROOT bindings)
- PyYAML
"""

from utils import *
import ROOT
import os
import yaml
import random
import argparse
import glob
import sys

def save_canvas_as_macro(canvas, base_name, output_dir):
    """
    Save the current canvas as a ROOT macro file.

    Parameters
    ----------
    canvas : ROOT.TCanvas
        The canvas to be saved.
    base_name : str
        The base name for the output file.
    output_dir : str
        Directory to save the macro file.
    """
    macro_path = os.path.join(output_dir, f"{base_name}.C")
    canvas.SaveAs(macro_path)

def load_style_yaml(style_file):
    """
    Load the ROOT plotting style from a YAML file.

    Parameters
    ----------
    style_file : str
        Path to the style YAML file.

    Returns
    -------
    dict
        Dictionary with style configuration.
    """
    with open(style_file, "r") as f:
        return yaml.safe_load(f).get("style", {})

def find_histogram_config(base_name, histo_config_list):
    """
    Find the histogram configuration for a given base name.

    Parameters
    ----------
    base_name : str
        Base name of the histogram.
    histo_config_list : list
        List of histogram configuration dictionaries.

    Returns
    -------
    dict or None
        Matching configuration dictionary, if found.
    """
    for cfg in histo_config_list:
        if cfg.get("name") == base_name:
            return cfg
    return None

def load_plot_config(yaml_file):
    """
    Load the 'plots' section from a YAML configuration file.

    Parameters
    ----------
    yaml_file : str
        Path to YAML file.

    Returns
    -------
    dict
        Dictionary containing plotting options.
    """
    with open(yaml_file, "r") as f:
        cfg = yaml.safe_load(f)
    return cfg.get("plots", {})

def load_histo_config(yaml_file):
    """
    Load the 'histograms' section from a YAML configuration file.

    Parameters
    ----------
    yaml_file : str
        Path to YAML file.

    Returns
    -------
    list
        List of histogram configurations.
    """
    with open(yaml_file, "r") as f:
        cfg = yaml.safe_load(f)
    return cfg.get("histograms", {})

def extract_basename(hname):
    """
    Extract the base observable name from a histogram name.

    Parameters
    ----------
    hname : str
        Histogram name.

    Returns
    -------
    str
        Base name without label suffix.
    """
    return hname.split("__")[0]

def extract_label(hname):
    """
    Extract the label suffix from a histogram name.

    Parameters
    ----------
    hname : str
        Histogram name.

    Returns
    -------
    str
        Label part of the histogram name.
    """
    return hname.split("__")[1] if "__" in hname else ""

def group_histograms_by_basename(hist_names):
    """
    Group histogram names by their base observable name.

    Parameters
    ----------
    hist_names : list of str
        List of histogram names.

    Returns
    -------
    dict
        Dictionary mapping base names to lists of labeled histogram names.
    """
    grouped = {}
    for h in hist_names:
        base = extract_basename(h)
        grouped.setdefault(base, []).append(h)
    return grouped

def generate_dummy_data(hist_sum):
    """
    Generate dummy (smeared) data based on the sum of histograms.

    Parameters
    ----------
    hist_sum : ROOT.TH1
        Summed histogram to be used as basis.

    Returns
    -------
    ROOT.TH1
        New histogram containing dummy data.
    """
    data = hist_sum.Clone("dummy_data")
    data.Reset()
    for b in range(1, hist_sum.GetNbinsX() + 1):
        y = hist_sum.GetBinContent(b)
        err = (y ** 0.5) if y > 0 else 1.0
        smeared = random.gauss(y, err)
        data.SetBinContent(b, max(0, smeared))
        data.SetBinError(b, err)
    data.SetMarkerStyle(20)
    data.SetMarkerColor(ROOT.kBlack)
    data.SetLineColor(ROOT.kBlack)
    data.SetStats(0)
    return data

# Remaining functions are already documented correctly with NumPy-style. Let me know if you want full rewriting of the entire file.
