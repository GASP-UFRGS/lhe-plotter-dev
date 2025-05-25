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
- group_histograms_by_basename : Organize histograms by observable name.

Command Line Interface
----------------------
Supports batch and single-file execution:

    python plotter.py --input FILE.root --config input.yaml --histos histograms.yaml --outdir plots/

Requires
--------
- ROOT (PyROOT bindings)
- PyYAML
"""

import ROOT
import os
import yaml
import random
import argparse
import glob
import sys
from lhe_plotter.utils import build_label_suffix, apply_root_style


def save_canvas_as_macro(canvas, base_name, output_dir):
    """
    Save a ROOT canvas as a .C macro.

    Parameters
    ----------
    canvas : ROOT.TCanvas
        The canvas to save.
    base_name : str
        Base name for the output file.
    output_dir : str
        Directory to save the macro file.
    """
    macro_path = os.path.join(output_dir, f"{base_name}.C")
    canvas.SaveAs(macro_path)


def load_style_yaml(style_file):
    """
    Load a style configuration dictionary from a YAML file.

    Parameters
    ----------
    style_file : str
        Path to the style YAML file.

    Returns
    -------
    dict
        Dictionary with style parameters.
    """
    with open(style_file, "r") as f:
        return yaml.safe_load(f).get("style", {})


def find_histogram_config(base_name, histo_config_list):
    """
    Retrieve histogram config dictionary for a given histogram name.

    Parameters
    ----------
    base_name : str
        Base name of the histogram (e.g. without __label).
    histo_config_list : list
        List of histogram config dictionaries.

    Returns
    -------
    dict or None
        The matching config or None if not found.
    """
    for cfg in histo_config_list:
        if cfg.get("name") == base_name:
            return cfg
    return None


def load_plot_config(yaml_file):
    """
    Load plot configuration section from YAML file.

    Parameters
    ----------
    yaml_file : str
        Path to input YAML file.

    Returns
    -------
    dict
        Dictionary with plotting config options.
    """
    with open(yaml_file, "r") as f:
        cfg = yaml.safe_load(f)
    return cfg.get("plots", {})


def load_histo_config(yaml_file):
    """
    Load histogram definitions from YAML file.

    Parameters
    ----------
    yaml_file : str
        Path to YAML file.

    Returns
    -------
    list
        List of histogram config dictionaries.
    """
    with open(yaml_file, "r") as f:
        cfg = yaml.safe_load(f)
    return cfg.get("histograms", {})


def extract_basename(hname):
    """Return the base name of a histogram key (before '__')."""
    return hname.split("__")[0]


def extract_label(hname):
    """Return the label of a histogram key (after '__')."""
    return hname.split("__")[1] if "__" in hname else ""


def group_histograms_by_basename(hist_names):
    """
    Group histogram keys into base-name groups.

    Parameters
    ----------
    hist_names : list of str
        Full histogram names with labels.

    Returns
    -------
    dict
        Dictionary mapping base names to lists of full names.
    """
    grouped = {}
    for h in hist_names:
        base = extract_basename(h)
        grouped.setdefault(base, []).append(h)
    return grouped


def generate_dummy_data(hist_sum):
    """
    Generate pseudo-data by smearing a summed histogram.

    Parameters
    ----------
    hist_sum : ROOT.TH1
        Histogram to base pseudo-data on.

    Returns
    -------
    ROOT.TH1
        New histogram with Gaussian fluctuations.
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


def draw_histogram_group(canvas, base, hnames, f, config, histo_config, output_dir, is_first, is_last, multi_pdf_path=None):
    """
    Draw a group of histograms with shared base name.

    Parameters
    ----------
    canvas : ROOT.TCanvas
        Canvas used to draw the plots.
    base : str
        Base name of the histogram group.
    hnames : list of str
        Full histogram names in the group.
    f : ROOT.TFile
        ROOT file containing histograms.
    config : dict
        Plotting config dictionary.
    histo_config : list
        List of all histogram metadata entries.
    output_dir : str
        Output directory to save files.
    is_first : bool
        Whether this is the first page of the multi-PDF.
    is_last : bool
        Whether this is the last page of the multi-PDF.
    multi_pdf_path : str, optional
        Output PDF path if saving all plots to a single PDF.
    """
    is_logy = config.get("log_scale", False)
    is_logx = config.get("log_x", False)
    use_stack = config.get("stacked", False)
    colors = config.get("colors", [632, 600, 416, 432, 801])
    use_dummy = config.get("add_dummy_data", False)
    transparent = config.get("transparent", False)

    c = canvas
    c.Clear()
    c.SetLogy(is_logy)
    c.SetLogx(is_logx)
    if transparent:
        c.SetFillStyle(0)
        c.SetFrameFillStyle(0)

    legend = ROOT.TLegend(0.7, 0.75, 0.88, 0.88)
    legend.SetFillStyle(0)
    stack = ROOT.THStack(f"stack_{base}", base)
    hist_sum = None

    first_hist = f.Get(hnames[0])
    is_2d = first_hist.InheritsFrom("TH2")

    if is_2d:
        for hname in hnames:
            h2 = f.Get(hname)
            h2.SetStats(0)
            h2.SetContour(99)
            h2.SetTitle("")
            h2.Draw("colz")
            print(f"→ Saving 2D to: {output_dir}/{base}.png")
            c.SaveAs(f"{output_dir}/{hname}.root")
            c.SaveAs(f"{output_dir}/{hname}.png")
            c.SaveAs(f"{output_dir}/{hname}.pdf")
    else:
        ymax = 0
        for i, hname in enumerate(hnames):
            h = f.Get(hname)
            h.SetFillColorAlpha(0, 0)
            h.SetLineColor(colors[i % len(colors)])
            h.SetTitle("")
            h.SetLineWidth(2)
            h.SetStats(0)
            label = extract_label(hname)
            base_name = extract_basename(hname)
            cfg = find_histogram_config(base_name, histo_config)
            xlabel = cfg.get("xlabel", "") if cfg else ""
            unit = cfg.get("unit", "") if cfg else ""

            normalize_xsec = config.get("normalize_by_cross_section", False)
            integrated_lumi = config.get("integrated_luminosity", False)
            lumi = config.get("lumi", 1)

            if xlabel:
                h.GetXaxis().SetTitleOffset(1.1)
                h.GetXaxis().SetTitle(xlabel)

            if normalize_xsec:
                if normalize_xsec and integrated_lumi:
                    ylabel = "Yield"
                elif xlabel and not unit:
                    ylabel = f"d#sigma/d{xlabel}"
                elif xlabel and unit:
                    ylabel = f"d#sigma/d{xlabel} ({unit})"
                else:
                    ylabel = "d#sigma/dx"
                h.GetYaxis().SetTitle(ylabel)

            this_max = h.GetMaximum()
            if this_max > ymax:
                ymax = this_max

            if use_stack:
                stack.Add(h)
                legend.AddEntry(h, label, "f")
            else:
                draw_opt = "hist same" if i else "hist"
                h.Draw(draw_opt)
                legend.AddEntry(h, label, "l")

            if hist_sum is None:
                hist_sum = h.Clone(f"{base}_sum")
                hist_sum.SetDirectory(0)
            else:
                hist_sum.Add(h)

        if use_stack:
            stack.Draw("hist")
            stack.SetMinimum(0)
            stack.SetMaximum(1.2 * ymax)
        else:
            first_histogram = f.Get(hnames[0])
            first_histogram.SetMinimum(0)
            first_histogram.SetMaximum(1.2 * ymax)

        if use_dummy:
            data = generate_dummy_data(hist_sum)
            data.Draw("E1 same")
            legend.AddEntry(data, "data (dummy)", "lep")

        legend.SetTextSize(0.03)
        legend.Draw()

        print(f"→ Saving 1D to: {output_dir}/{base}.png")
        c.SaveAs(f"{output_dir}/{base}.root")
        c.SaveAs(f"{output_dir}/{base}.png")
        c.SaveAs(f"{output_dir}/{base}.pdf")
        save_canvas_as_macro(c, base, output_dir)

        if multi_pdf_path:
            if is_first:
                c.Print(multi_pdf_path + "(")
            c.Print(multi_pdf_path)
            if is_last:
                c.Print(multi_pdf_path + ")")


def plot_histograms_from_root(root_file_path, input_yaml="input.dat", input_histo="histograms.yaml", output_dir="plots", style_file=None):
    """
    Main driver function to visualize histograms using config and style.

    Parameters
    ----------
    root_file_path : str
        Path to input ROOT file.
    input_yaml : str
        Path to input plot config YAML.
    input_histo : str
        Path to histogram definitions YAML.
    output_dir : str
        Output folder for plots.
    style_file : str, optional
        Optional path to a YAML style file.
    """
    ROOT.gROOT.SetBatch(True)
    os.makedirs(output_dir, exist_ok=True)
    with open(input_yaml, "r") as f:
        config = yaml.safe_load(f)

    label_suffix = build_label_suffix(config)
    multi_pdf_path = os.path.join(output_dir, f"all_plots{label_suffix}.pdf")
    ROOT.gSystem.Exec(f"rm -f {multi_pdf_path}")

    if style_file:
        apply_root_style(style_file)
        style = load_style_yaml(style_file)
    else:
        style = {}

    input_config = load_plot_config(input_yaml)
    histo_config = load_histo_config(input_histo)

    f = ROOT.TFile.Open(root_file_path)
    if not f or f.IsZombie():
        print("Error: Could not open ROOT file.")
        return

    all_keys = [k.GetName() for k in f.GetListOfKeys()]
    grouped = group_histograms_by_basename(all_keys)

    canvas = ROOT.TCanvas("c", "", 800, 800)
    canvas.SetLeftMargin(0.20)
    canvas.SetRightMargin(0.12)
    canvas.SetTopMargin(0.12)
    canvas.SetBottomMargin(0.12)

    for i, (base, hnames) in enumerate(grouped.items()):
        draw_histogram_group(
            canvas, base, hnames, f, input_config, histo_config, output_dir,
            is_first=(i == 0),
            is_last=(i == len(grouped) - 1),
            multi_pdf_path=multi_pdf_path
        )

    print(f"PNG plots saved to: {output_dir}/")
    print(f"Multi-page PDF saved to: {multi_pdf_path}")

def main_cli():
    """
    Entry point when plotter.py is run as a module.
    """
    parser = argparse.ArgumentParser(description="Standalone ROOT histogram plotter.")
    parser.add_argument("--input", required=True, help="Input ROOT file")
    parser.add_argument("--config", required=True, help="YAML config file (input.dat)")
    parser.add_argument("--histos", help="Histogram config YAML")
    parser.add_argument("--outdir", default="plots", help="Output folder for plots")
    parser.add_argument("--style", help="Optional ROOT style YAML")

    args = parser.parse_args()

    plot_histograms_from_root(
        root_file_path=args.input,
        input_yaml=args.config,
        input_histo=args.histos,
        output_dir=args.outdir,
        style_file=args.style
    )

if __name__ == "__main__":
    main_cli()

