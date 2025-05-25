"""
Provides core functions for histogram definition, dynamic evaluation, and population
using ROOT histograms (TH1F and TH2F). This module is used in the LHE file plotting
workflow to create and fill histograms based on user-defined YAML configurations.

Main Features
-------------
- Parse and create 1D and 2D ROOT histograms dynamically.
- Evaluate arbitrary functions on particle TLorentzVectors using safe `eval`.
- Fill histograms with single or pair-wise particle data.
- Save filled histograms to ROOT files.

Functions
---------
- evaluate_function : Safely evaluate user-defined functions over particle kinematics.
- create_histograms : Create ROOT histograms from config definitions.
- fill_histograms : Fill histograms using parsed LHE particle data.
- save_histograms_to_file : Write histograms to a `.root` file.

Notes
-----
This module expects particle objects to be dictionaries containing at least a `"pid"` key
and a `"vector"` key referencing a `ROOT.TLorentzVector` object.

Requires
--------
- ROOT (PyROOT bindings)
- math (standard library)

"""

import ROOT
from ROOT import TH1F, TH2F
import math

def evaluate_function(particle, function_string, beam_energy, second_particle=None):
    """
    Evaluate a user-defined function string using particle TLorentzVectors.

    Parameters
    ----------
    particle : dict
        Dictionary containing at least a 'vector' key with a TLorentzVector.
    function_string : str
        A string expression using variables X and optionally Y.
    beam_energy : float
        Beam energy for context-dependent calculations.
    second_particle : dict, optional
        Optional second particle with a 'vector' key.

    Returns
    -------
    float
        The evaluated result of the expression.

    Raises
    ------
    ValueError
        If the input data or evaluation fails.
    """
    if not function_string:
        raise ValueError("Function string is missing or empty.")

    X = particle.get("vector", None)
    Y = second_particle.get("vector", None) if second_particle else None

    if X is None:
        raise ValueError("First particle has no valid TLorentzVector.")
    if second_particle and Y is None:
        raise ValueError("Second particle has no valid TLorentzVector.")

    safe_locals = {
        "X": X,
        "Y": Y,
        "ROOT": ROOT,
        "math": math,
        "abs": abs,
        "min": min,
        "max": max
    }

    try:
        return eval(function_string, {"__builtins__": None}, safe_locals)
    except Exception as e:
        raise ValueError(f"Error evaluating function '{function_string}': {e}")

def create_histograms(config):
    """
    Create and return a dictionary of ROOT histograms from a configuration dict.

    Parameters
    ----------
    config : dict
        Dictionary containing 'histograms' and 'particles.include'.

    Returns
    -------
    dict
        Dictionary of histograms indexed by name.
    """
    histograms = {}
    include_pids = set(config["particles"]["include"])

    for cfg in config["histograms"]:
        if not any(pid in include_pids for pid in cfg.get("id", [])):
            continue

        name = cfg["name"]
        if cfg.get("mode") == "2d":
            h = ROOT.TH2F(
                name, name,
                cfg["xbins"], cfg["xmin"], cfg["xmax"],
                cfg["ybins"], cfg["ymin"], cfg["ymax"]
            )
        else:
            h = ROOT.TH1F(
                name, name,
                cfg["bins"], cfg["xmin"], cfg["xmax"]
            )

        h.SetDirectory(0)

        histograms[name] = {
            "hist": h,
            "xlabel": cfg.get("xlabel", ""),
            "unit": cfg.get("unit", ""),
            "mode": cfg.get("mode", "single"),
        }

    return histograms

def fill_histograms(histograms, particles, histogram_configs, label=None, weight=1.0, beam_energy=7000.):
    """
    Fill provided histograms based on evaluated user-defined functions.

    Parameters
    ----------
    histograms : dict
        Dictionary of histograms created by `create_histograms`.
    particles : list
        List of particles, each as a dict with 'pid' and 'vector'.
    histogram_configs : list
        List of histogram config entries from YAML.
    label : str, optional
        Optional label suffix to identify histograms.
    weight : float, optional
        Event weight for normalization. Default is 1.0.
    beam_energy : float, optional
        Beam energy in GeV. Default is 7000.

    Raises
    ------
    ValueError
        If histogram mode is unknown.
    """
    for config in histogram_configs:
        name = config["name"]
        ids = config.get("id", [])
        mode = config.get("mode", "single")
        function = config.get("function")

        full_name = f"{name}__{label}" if label else name

        if full_name not in histograms:
            continue

        histo = histograms[full_name]["hist"]

        selected_particles = [p for p in particles if p["pid"] in ids]

        if mode == "single":
            for p in selected_particles:
                if p["vector"] is None:
                    continue
                value = evaluate_function(p, function, beam_energy=beam_energy)
                histo.Fill(value, weight)

        elif mode == "pair":
            for i in range(len(selected_particles)):
                for j in range(i+1, len(selected_particles)):
                    p1 = selected_particles[i]
                    p2 = selected_particles[j]
                    if p1.get("vector") is None or p2.get("vector") is None:
                        continue
                    value = evaluate_function(p1, function, beam_energy=beam_energy, second_particle=p2)
                    histo.Fill(value, weight)

        elif mode == "2d":
            for p in selected_particles:
                if p["vector"] is None:
                    continue
                xfunc, yfunc = function
                xval = evaluate_function(p, xfunc, beam_energy=beam_energy)
                yval = evaluate_function(p, yfunc, beam_energy=beam_energy)
                histo.Fill(xval, yval, weight)

        else:
            raise ValueError(f"Unknown histogram mode: {mode}")

def save_histograms_to_file(histograms, output_file):
    """
    Write all histograms to a ROOT file.

    Parameters
    ----------
    histograms : dict
        Dictionary of histograms as returned by `create_histograms`.
    output_file : str
        Path to the output ROOT file.
    """
    f = ROOT.TFile(output_file, "RECREATE")
    for hinfo in histograms.values():
        hinfo["hist"].Write()
    f.Close()