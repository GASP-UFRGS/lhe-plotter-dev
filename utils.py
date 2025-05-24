"""
Utility functions for managing configuration, file paths, and post-processing of histograms
in LHE file analysis workflows.

This module provides helper functions to build dynamic output directory names,
load YAML configurations, normalize ROOT histograms, and generate dummy data.

License: MIT or your license of choice
"""

import yaml
import random
import sys

def build_dynamic_outdir(base_outdir, config):
    """
    Create a dynamic output directory name based on configuration flags.

    Parameters
    ----------
    base_outdir : str
        Base name of the output directory.
    config : dict
        Configuration dictionary.

    Returns
    -------
    str
        Dynamically generated output directory name.
    """
    plot_config = config.get("plots", {})
    labels = []

    if config.get("apply_cuts", False):
        labels.append("cuts")
    if plot_config.get("normalize_by_cross_section", False):
        labels.append("norm")
    if plot_config.get("log_scale", False):
        labels.append("logy")
    if plot_config.get("log_x", False):
        labels.append("logx")
    if plot_config.get("stacked", False):
        labels.append("stacked")
    if plot_config.get("add_dummy_data", False):
        labels.append("dummy")

    if labels:
        label_suffix = "_" + "_".join(labels)
        dynamic_outdir = base_outdir.rstrip("/") + label_suffix
    else:
        dynamic_outdir = base_outdir.rstrip("/")

    return dynamic_outdir

def build_label_suffix(config):
    """
    Build a label suffix string from configuration flags.

    Parameters
    ----------
    config : dict
        Configuration dictionary.

    Returns
    -------
    str
        Suffix string like "_cuts_norm_logy".
    """
    plot_config = config.get("plots", {})
    labels = []

    if config.get("apply_cuts", False):
        labels.append("cuts")
    if plot_config.get("normalize_by_cross_section", False):
        labels.append("norm")
    if plot_config.get("log_scale", False):
        labels.append("logy")
    if plot_config.get("log_x", False):
        labels.append("logx")
    if plot_config.get("stacked", False):
        labels.append("stacked")
    if plot_config.get("add_dummy_data", False):
        labels.append("data")

    return "_" + "_".join(labels) if labels else ""

def check(args):
    """
    Validate command-line arguments for running the LHE analysis.

    Parameters
    ----------
    args : list
        List of command-line arguments.

    Returns
    -------
    tuple
        Input file and output ROOT file path.
    """
    if len(sys.argv) != 3:
        print("Usage: python lhe_analysis.py <input_config.yaml> <output_histograms.root>")
        sys.exit(1)
    input_file = sys.argv[1]
    output_root_file = sys.argv[2]
    return input_file, output_root_file

def load_input_file(filename):
    """
    Load a YAML configuration file.

    Parameters
    ----------
    filename : str
        Path to YAML file.

    Returns
    -------
    dict
        Parsed YAML configuration.
    """
    with open(filename, 'r') as f:
        config = yaml.safe_load(f)
    return config

def post_process_histograms(config, histograms):
    """
    Apply normalization and post-processing to histograms.

    Parameters
    ----------
    config : dict
        Configuration dictionary.
    histograms : dict
        Dictionary of ROOT histograms.
    """
    total_events = 0
    total_cross_section = 0.0
    lumi = config.get('integrated_luminosity', 1.0)

    for file_cfg in config['files']:
        lhe_file = file_cfg['path']
        cross_section = file_cfg.get('cross_section', 1.0)

        event_count = sum(1 for _ in pylhe.read(lhe_file))
        total_events += event_count
        total_cross_section += cross_section

        print(f"File: {lhe_file}")
        print(f"  Events: {event_count}")
        print(f"  Cross Section: {cross_section} pb")

    print(f"\nTotal Events: {total_events}")
    print(f"Total Cross Section: {total_cross_section} pb")

    if config.get('normalize_by_cross_section', False):
        scale_factor = lumi * total_cross_section / total_events
        print(f"Applying normalization with scale factor: {scale_factor}")
        for hist in histograms.values():
            hist.Scale(scale_factor)

    if config.get('add_dummy_data', False):
        print("Adding dummy data to histograms...")
        for hist_name, hist in histograms.items():
            add_dummy_data(hist, config['dummy_data_config'])

    if config.get('log_scale', False):
        for hist in histograms.values():
            hist.SetMinimum(0.1)

    if config.get('stack_histograms', False):
        print("Stacking histograms is currently only supported during plotting.")

def add_dummy_data(histogram, dummy_config):
    """
    Add dummy data points to a histogram for visualization purposes.

    Parameters
    ----------
    histogram : ROOT.TH1
        ROOT histogram object.
    dummy_config : dict
        Configuration with distribution type and parameters.
    """
    distribution = dummy_config.get('distribution', 'gaussian')
    params = dummy_config.get('params', {})
    n_points = dummy_config.get('n_points', 1000)

    for _ in range(n_points):
        if distribution == 'gaussian':
            mean = params.get('mean', 0)
            sigma = params.get('sigma', 1)
            value = random.gauss(mean, sigma)
        elif distribution == 'uniform':
            low = params.get('low', 0)
            high = params.get('high', 1)
            value = random.uniform(low, high)
        elif distribution == 'exponential':
            scale = params.get('scale', 1)
            value = random.expovariate(1 / scale)
        else:
            raise ValueError(f"Unsupported distribution: {distribution}")

        histogram.Fill(value)

def get_variable_function(variable_name):
    """
    Return a lambda function to extract a variable from TLorentzVector.

    Parameters
    ----------
    variable_name : str
        One of "pt", "eta", "phi".

    Returns
    -------
    function
        Lambda function extracting the requested variable.
    """
    if variable_name == "pt":
        return lambda p: p["vector"].Pt()
    elif variable_name == "eta":
        return lambda p: p["vector"].Eta()
    elif variable_name == "phi":
        return lambda p: p["vector"].Phi()
    else:
        raise ValueError(f"Unsupported variable: {variable_name}")