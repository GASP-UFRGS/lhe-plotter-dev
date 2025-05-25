"""
lhe_plotter
===========

A Python module for parsing LHE files, applying selection cuts, and generating
ROOT histograms and publication-quality plots. Includes support for automatic
cross-section normalization, configurable binning, batch processing, and plotting.

Modules exposed:
- `process`: Functions for reading and filtering LHE files using `pylhe` and ROOT.
- `histo`: Histogram creation and filling utilities.
- `plotter_from_root`: Tools to visualize saved ROOT histograms.
- `utils`: Helpers for config parsing, labeling, and normalization setup.
"""

from .histo import (
    create_histograms,
    fill_histograms,
    save_histograms_to_file,
    evaluate_function,
)

from .process import (
    process_lhe_file_with_summary,
    get_number_of_events_from_lhe,
    pass_cuts,
)

from .parser import (
    run_lhe_plotter,
    run_parallel_batch,
    load_histogram_definitions
)

from .plotter import (
    plot_histograms_from_root,
)

from .utils import (
    build_dynamic_outdir,
    build_label_suffix,
    load_input_file,
    post_process_histograms,
    apply_root_style,
)

__all__ = [
    "create_histograms",
    "fill_histograms",
    "save_histograms_to_file",
    "evaluate_function",
    "process_lhe_file_with_summary",
    "get_number_of_events_from_lhe",
    "pass_cuts",
    "plot_histograms_from_root",
    "build_dynamic_outdir",
    "build_label_suffix",
    "load_input_file",
    "post_process_histograms",
    "run_lhe_plotter",
    "run_parallel_batch",
    "load_histogram_definitions",
]

