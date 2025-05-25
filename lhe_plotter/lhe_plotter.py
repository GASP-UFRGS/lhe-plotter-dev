"""
Script for processing LHE (Les Houches Event) files, applying cuts,
filling histograms, normalizing them, and optionally plotting results.

Main features:
- Reads configuration from YAML/DAT files
- Processes multiple LHE files
- Applies particle-level cuts
- Computes weighted histograms
- Outputs results in ROOT format
- Supports parallel batch processing
- Optional plotting via plotter_from_root.py
"""

from .utils import *
from .process import *
from .histo import *
from tqdm import tqdm
import logging
import csv
import sys
import os
import argparse
import concurrent.futures
import yaml
import ROOT
import subprocess
import shutil

def count_lhe_events(file_path):
    """
    Count the number of <event> tags in an LHE file.

    Parameters
    ----------
    file_path : str
        Path to the LHE file.

    Returns
    -------
    int
        Number of events.
    """
    with open(file_path, "r") as f:
        return sum(1 for line in f if "<event>" in line)

def setup_logger(label, log_dir):
    """
    Initialize a file-based logger for a specific job.

    Parameters
    ----------
    label : str
        Logger label.
    log_dir : str
        Directory where the log file will be saved.

    Returns
    -------
    logging.Logger
        Configured logger.
    """
    log_path = os.path.join(log_dir, f"{label}.log")
    logger = logging.getLogger(label)
    handler = logging.FileHandler(log_path)
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    handler.setFormatter(formatter)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    logger.propagate = False
    return logger


    """
    Main function to process LHE files and fill histograms.

    Parameters
    ----------
    input_file : str
        Input YAML configuration file.
    output_root_file : str
        Output ROOT file path.
    """
    histogram_configs = config["histograms"]
    plot_config = config.get("plots", {})
    normalize = plot_config.get("normalize_by_cross_section", False)
    lumi = plot_config.get("lumi", 1.0)

    histograms = {}
    summary_rows = []

    for file_cfg in config["files"]:
        file_path = file_cfg["path"]
        label = file_cfg["label"]
        cross_section = file_cfg.get("cross_section", 1.0)
        new_config = config.copy()
        new_config["histograms"] = [
            {**cfg, "name": f"{cfg['name']}__{label}"} for cfg in config["histograms"]
        ]
        file_histos = create_histograms(new_config)

        total_events = count_lhe_events(file_path)
        events_passing_cuts = 0

        particles_to_include = config["particles"]["include"]
        apply_cuts = config.get("apply_cuts", False)
        cuts = config.get("cuts", [])

        print(f"Processing {file_path}...")

        for particles in process_lhe_file_with_summary(file_path, particles_to_include, apply_cuts, cuts, file_cfg, verbose=verbose):
            events_passing_cuts += 1
            event_weight = 1.0
            if normalize:
                event_weight = (cross_section * lumi) / total_events
            fill_histograms(file_histos, particles, histogram_configs, label=label, weight=event_weight)

        histograms.update(file_histos)
        summary_rows.append({
            "filename": file_path,
            "total_events": total_events,
            "passed_events": events_passing_cuts,
            "passed_percent": f"{(events_passing_cuts / total_events) * 100:.2f}"
        })

    label_suffix = build_label_suffix(config)
    output_filename = f"output{label_suffix}.root"
    save_histograms_to_file(histograms, final_output_path)

    summary_path = os.path.join(final_output_path, f"summary{label_suffix}.csv")
    with open(summary_path, "w", newline="") as csvfile:
        fieldnames = ["filename", "total_events", "passed_events", "passed_percent"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summary_rows)

def process_single_file_with_logging(args):
    """
    Process a single file (used in batch mode) with logging.

    Parameters
    ----------
    args : tuple
        Contains (file_cfg, config, final_output_path, verbose)

    Returns
    -------
    dict
        Dictionary with histogram output and event summary.
    """
    file_cfg, config, final_output_path, verbose = args
    file_path = file_cfg["path"]
    label = file_cfg["label"]
    cross_section = file_cfg.get("cross_section", 1.0)
    histogram_configs = config["histograms"]
    particles_to_include = config["particles"]["include"]
    apply_cuts = config.get("apply_cuts", False)
    cuts = config.get("cuts", [])

    logger = setup_logger(label, final_output_path)
    logger.info(f"Started processing {file_path}...")

    file_histos = create_histograms([
        {**cfg, "name": f"{cfg['name']}__{label}"} for cfg in histogram_configs
    ])

    total_events = count_lhe_events(file_path)
    events_passing_cuts = 0

    for particles in process_lhe_file_with_summary(file_path, particles_to_include, apply_cuts, cuts, file_cfg, verbose=verbose):
        events_passing_cuts += 1
        event_weight = 1.0
        if config["plots"].get("normalize_by_cross_section", False):
            lumi = config["plots"].get("lumi", 1.0)
            event_weight = (cross_section * lumi) / total_events
        beam_energy = config.get("beam_energy", 6500.0)
        fill_histograms(file_histos, particles, histogram_configs, label=label, weight=event_weight, beam_energy=beam_energy)
        if verbose:
            logger.info(f"Event {events_passing_cuts} passed")

    logger.info(f"Finished {file_path}: {events_passing_cuts}/{total_events} passed")

    return {
        "label": label,
        "histograms": file_histos,
        "summary": {
            "filename": file_path,
            "total_events": total_events,
            "passed_events": events_passing_cuts,
            "passed_percent": f"{(events_passing_cuts / total_events) * 100:.2f}"
        }
    }

def run_parallel_batch(config_file, final_output_path="batch_output", verbose=False):
    """
    Run batch processing in parallel for all input files in a config.

    Parameters
    ----------
    config_file : str
        Path to YAML or DAT configuration file.
    final_output_path : str, optional
        Output directory name.
    verbose : bool, optional
        Enable verbose logging.
    """
    os.makedirs(final_output_path, exist_ok=True)
    config = utils.load_input_file(config_file)
    file_cfgs = config["files"]

    job_args = [(fc, config, final_output_path, verbose) for fc in file_cfgs]
    all_histos = {}
    all_summary = []

    print(f"\nStarting parallel batch mode ({len(file_cfgs)} jobs)...\n")

    with concurrent.futures.ProcessPoolExecutor() as executor:
        results = list(tqdm(executor.map(process_single_file_with_logging, job_args), total=len(file_cfgs), desc="Batch Progress"))

    for res in results:
        all_histos.update(res["histograms"])
        all_summary.append(res["summary"])

    label_suffix = build_label_suffix(config)
    output_file = os.path.join(final_output_path, f"output{label_suffix}.root")

    save_histograms_to_file(all_histos, output_file)

    summary_path = os.path.join(final_output_path, "summary.csv")
    with open(summary_path, "w", newline="") as csvfile:
        fieldnames = ["filename", "total_events", "passed_events", "passed_percent"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_summary)

def run_lhe_plotter(input_file, output_root_file, config, final_outdir, verbose=False):
    """
    Main logic for processing LHE files and filling ROOT histograms.

    Parameters
    ----------
    input_file : str
        Path to the main config file (YAML or DAT).
    output_root_file : str
        Path to the output ROOT file where histograms will be saved.
    config : dict
        Parsed configuration dictionary.
    final_outdir : str
        Output directory for ROOT and summary files.
    verbose : bool, optional
        If True, enables verbose output during processing.
    """
    histogram_configs = config["histograms"]
    plot_config = config.get("plots", {})
    normalize = plot_config.get("normalize_by_cross_section", False)
    lumi = plot_config.get("lumi", 1.0)

    histograms = {}
    summary_rows = []

    for file_cfg in config["files"]:
        file_path = file_cfg["path"]
        label = file_cfg["label"]
        cross_section = file_cfg.get("cross_section", 1.0)
        new_config = config.copy()
        new_config["histograms"] = [
            {**cfg, "name": f"{cfg['name']}__{label}"} for cfg in histogram_configs
        ]
        file_histos = create_histograms(new_config)

        # Count total number of events
        from .process import get_number_of_events_from_lhe
        total_events = get_number_of_events_from_lhe(file_path)
        if not total_events:
            total_events = sum(1 for line in open(file_path) if "<event>" in line)
        events_passing_cuts = 0

        particles_to_include = config["particles"]["include"]
        apply_cuts = config.get("apply_cuts", False)
        cuts = config.get("cuts", [])

        print(f"Processing {file_path}...")

        for particles in process_lhe_file_with_summary(
            file_path, particles_to_include, apply_cuts, cuts, file_cfg, verbose=verbose
        ):
            events_passing_cuts += 1
            event_weight = 1.0
            if normalize:
                event_weight = (cross_section * lumi) / total_events
            fill_histograms(
                file_histos, particles, histogram_configs,
                label=label, weight=event_weight
            )

        histograms.update(file_histos)
        summary_rows.append({
            "filename": file_path,
            "total_events": total_events,
            "passed_events": events_passing_cuts,
            "passed_percent": f"{(events_passing_cuts / total_events) * 100:.2f}"
        })

    # Save final output
    save_histograms_to_file(histograms, output_root_file)

    print(f"Histograms saved to {output_root_file}")

    # Save summary CSV
    label_suffix = build_label_suffix(config)
    summary_path = os.path.join(final_outdir, f"summary{label_suffix}.csv")
    with open(summary_path, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["filename", "total_events", "passed_events", "passed_percent"])
        writer.writeheader()
        writer.writerows(summary_rows)

    print(f"Summary written to {summary_path}")

def load_histogram_definitions(histo_file):
    """
    Load histogram definitions from a YAML file.

    Parameters
    ----------
    histo_file : str
        YAML file path.

    Returns
    -------
    list
        List of histogram configurations.
    """
    with open(histo_file, "r") as f:
        return yaml.safe_load(f)["histograms"]

