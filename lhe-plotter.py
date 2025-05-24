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

from utils import *
from process import *
from histo import *
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

def copy_config_files(outdir, config_files):
    """
    Copy important configuration files into the specified output directory.

    Parameters
    ----------
    outdir : str
        Output directory path.
    config_files : list of str
        List of file paths to copy.
    """
    os.makedirs(outdir, exist_ok=True)
    for file in config_files:
        if os.path.exists(file):
            shutil.copy(file, outdir)

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

def main(input_file, output_root_file):
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

        for particles in process_lhe_file_with_summary(file_path, particles_to_include, apply_cuts, cuts, file_cfg, verbose=args.verbose):
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
    final_output_path = os.path.join(final_outdir, output_filename)
    save_histograms_to_file(histograms, final_output_path)

    summary_path = os.path.join(final_outdir, f"summary{label_suffix}.csv")
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
        Contains (file_cfg, config, outdir, verbose)

    Returns
    -------
    dict
        Dictionary with histogram output and event summary.
    """
    file_cfg, config, outdir, verbose = args
    file_path = file_cfg["path"]
    label = file_cfg["label"]
    cross_section = file_cfg.get("cross_section", 1.0)
    histogram_configs = config["histograms"]
    particles_to_include = config["particles"]["include"]
    apply_cuts = config.get("apply_cuts", False)
    cuts = config.get("cuts", [])

    logger = setup_logger(label, outdir)
    logger.info(f"Started processing {file_path}...")

    file_histos = create_histograms([
        {**cfg, "name": f"{cfg['name']}__{label}"} for cfg in histogram_configs
    ])

    total_events = count_lhe_events(file_path)
    events_passing_cuts = 0

    for particles in process_lhe_file_with_summary(file_path, particles_to_include, apply_cuts, cuts, file_cfg, verbose=args.verbose):
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

def run_parallel_batch(config_file, outdir="batch_output", verbose=False):
    """
    Run batch processing in parallel for all input files in a config.

    Parameters
    ----------
    config_file : str
        Path to YAML or DAT configuration file.
    outdir : str, optional
        Output directory name.
    verbose : bool, optional
        Enable verbose logging.
    """
    os.makedirs(outdir, exist_ok=True)
    config = load_input_file(config_file)
    file_cfgs = config["files"]

    job_args = [(fc, config, outdir, verbose) for fc in file_cfgs]
    all_histos = {}
    all_summary = []

    print(f"\nStarting parallel batch mode ({len(file_cfgs)} jobs)...\n")

    with concurrent.futures.ProcessPoolExecutor() as executor:
        results = list(tqdm(executor.map(process_single_file_with_logging, job_args), total=len(file_cfgs), desc="Batch Progress"))

    for res in results:
        all_histos.update(res["histograms"])
        all_summary.append(res["summary"])

    label_suffix = build_label_suffix(config)
    output_file = os.path.join(outdir, f"output{label_suffix}.root")

    save_histograms_to_file(all_histos, output_file)

    summary_path = os.path.join(outdir, "summary.csv")
    with open(summary_path, "w", newline="") as csvfile:
        fieldnames = ["filename", "total_events", "passed_events", "passed_percent"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_summary)

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

# CLI ENTRY POINT
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process LHE files and fill ROOT histograms.")
    parser.add_argument("--config", dest="input_file", help="YAML or DAT config file", required=False)
    parser.add_argument("--histos", required=True, help="YAML file with histogram definitions")
    parser.add_argument("--output", dest="output_file", help="Output ROOT file (normal mode only)")
    parser.add_argument("--batch", action="store_true", help="Enable batch mode over all input files")
    parser.add_argument("--outdir", default="batch_output", help="Output folder for batch mode")
    parser.add_argument("--verbose", action="store_true", help="Enable per-event logging inside batch logs")
    parser.add_argument("--auto-plot", action="store_true", help="Automatically call plotter_from_root after filling histograms")

    args = parser.parse_args()
    config = load_input_file(args.input_file)
    final_outdir = build_dynamic_outdir(args.outdir, config)
    label_suffix = build_label_suffix(config)
    output_filename = f"output{label_suffix}.root"
    final_output_path = os.path.join(final_outdir, output_filename)

    copy_config_files(final_outdir, ["input.dat", "histograms.yaml", "root_style.yaml"])

    if args.histos:
        external_histos = load_histogram_definitions(args.histos)
        config["histograms"] = external_histos
    elif "histograms" not in config:
        print("No histograms found in config or via --histos.")
        sys.exit(1)

    if args.batch:
        if not args.input_file:
            print("Error: --batch requires --config (input file).")
        else:
            run_parallel_batch(args.input_file, outdir=final_outdir, verbose=args.verbose)
    elif args.input_file and final_output_path:
        main(input_file=args.input_file, output_root_file=final_output_path)
    else:
        parser.print_help()

    if args.auto_plot:
        print("Auto-plotting enabled! Launching plotter_from_root.py...")
        script_dir = os.path.dirname(os.path.realpath(__file__))
        plotter_path = os.path.join(script_dir, "plotter_from_root.py")

        plot_cmd = [
            "python3", plotter_path,
            "--input", final_output_path,
            "--config", args.input_file,
            "--outdir", final_outdir
        ]

        if args.histos:
            plot_cmd.extend(["--histos", args.histos])

        if hasattr(args, "style") and args.style:
            plot_cmd.extend(["--style", args.style])

        subprocess.run(plot_cmd, check=True)