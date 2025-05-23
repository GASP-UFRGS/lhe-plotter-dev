import ROOT
from ROOT import TH1F, TH2F
import math

def evaluate_function(particle, function_string, beam_energy, second_particle=None):
    """
    Evaluate a dynamic function on TLorentzVectors.
    `particle` is main particle (X), `second_particle` is optional (Y).
    """

    if not function_string:
        raise ValueError("Function string is missing or empty.")

    # Get vectors safely
    X = particle.get("vector", None)
    Y = second_particle.get("vector", None) if second_particle else None

    if X is None:
        raise ValueError("First particle has no valid TLorentzVector.")
    if second_particle and Y is None:
        raise ValueError("Second particle has no valid TLorentzVector.")

    # Provide safe eval environment
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
    histograms = {}
    include_pids = set(config["particles"]["include"])

    for cfg in config["histograms"]:
        if not any(pid in include_pids for pid in cfg.get("id", [])):
            continue  # Skip this histogram if no matching PID

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
            "hist": h,  # <-- use the 'h' you created!
            "xlabel": cfg.get("xlabel", ""),
            "unit": cfg.get("unit", ""),
            "mode": cfg.get("mode", "single"),  # useful if you want to know later
        }

    return histograms

def fill_histograms(histograms, particles, histogram_configs, label=None, weight=1.0, beam_energy=7000.):
    """
    Fill histograms dynamically based on the function provided by the user.
    `particles` is a list of dictionaries with "pid" and "vector" keys.
    """
    for config in histogram_configs:
        name = config["name"]
        ids = config.get("id", [])
        mode = config.get("mode", "single")
        function = config.get("function")

        full_name = f"{name}__{label}" if label else name

        if full_name not in histograms:
            continue  # Skip if histogram not found

        histo = histograms[full_name]["hist"]

        # Match particles based on PID
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
    Save all histograms to a ROOT file.
    """
    f = ROOT.TFile(output_file, "RECREATE")
    for hinfo in histograms.values():
        hinfo["hist"].Write()
    f.Close()
