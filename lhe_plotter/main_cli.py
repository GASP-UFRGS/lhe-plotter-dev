"""
Command-line interface for LHE Plotter.

This module defines the main CLI interface for processing LHE files and generating
ROOT histograms. It supports both single-run and batch modes, and can automatically
invoke plotting routines after histogram generation.

Functions
---------
main_cli()
    Parses command-line arguments and dispatches LHE processing or batch jobs.
"""

import os
import argparse
from . import utils, process, histo, plotter_from_root
import subprocess
from .lhe_plotter import run_lhe_plotter, run_parallel_batch
from .lhe_plotter import load_histogram_definitions

def main():
    """
    Entry point for the LHE plotter command-line interface.

    This function parses user arguments to perform LHE file processing and 
    histogram generation. It supports the following operations:
    
    - Running in single-file or batch mode
    - Applying event cuts and weights
    - Normalizing histograms using cross sections and luminosity
    - Automatically plotting histograms with the `plotter_from_root` module

    The command-line options allow configuration of input files, histogram definitions,
    output directories, verbosity, and plotting behavior.

    Raises
    ------
    SystemExit
        If required arguments are missing or invalid.
    """
    parser = argparse.ArgumentParser(description="Process LHE files and fill ROOT histograms.")
    parser.add_argument("--config", dest="input_file", help="YAML or DAT config file", required=False)
    parser.add_argument("--histos", required=True, help="YAML file with histogram definitions")
    parser.add_argument("--output", dest="output_file", help="Output ROOT file (normal mode only)")
    parser.add_argument("--batch", action="store_true", help="Enable batch mode over all input files")
    parser.add_argument("--outdir", default="batch_output", help="Output folder for batch mode")
    parser.add_argument("--verbose", action="store_true", help="Enable per-event logging inside batch logs")
    parser.add_argument("--auto-plot", action="store_true", help="Automatically call plotter_from_root after filling histograms")

    args = parser.parse_args()
    config = utils.load_input_file(args.input_file)
    final_outdir = utils.build_dynamic_outdir(args.outdir, config)
    label_suffix = utils.build_label_suffix(config)
    output_filename = f"output{label_suffix}.root"
    final_output_path = os.path.join(final_outdir, output_filename)

    utils.copy_config_files(final_outdir, ["input.dat", "histograms.yaml", "root_style.yaml"])

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
        run_lhe_plotter(
            input_file=args.input_file,
            output_root_file=final_output_path,
            config=config,
            final_outdir=final_outdir,
            verbose=args.verbose
        )
    else:
        parser.print_help()

    if args.auto_plot:
        print("Auto-plotting enabled! Launching plotter_from_root.py...")
        script_dir = os.path.dirname(os.path.realpath(__file__))
        plotter_path = os.path.join(script_dir, "plotter_from_root.py")

        plot_cmd = [
            "python3", "-m", "lhe_plotter.plotter_from_root",
            "--input", final_output_path,
            "--config", args.input_file,
            "--outdir", final_outdir
        ]

        if args.histos:
            plot_cmd.extend(["--histos", args.histos])

        if hasattr(args, "style") and args.style:
            plot_cmd.extend(["--style", args.style])

        subprocess.run(plot_cmd, check=True)

if __name__ == "__main__":
    main()

