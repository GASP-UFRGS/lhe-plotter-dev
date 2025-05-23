import yaml
import random
import sys

def build_dynamic_outdir(base_outdir, config):
    """Create a dynamic output directory name based on plot options."""
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
    if len(sys.argv) != 3:
        print("Usage: python lhe_analysis.py <input_config.yaml> <output_histograms.root>")
        sys.exit(1)
    input_file = sys.argv[1]
    output_root_file = sys.argv[2]
    return input_file,output_root_file

def load_input_file(filename):
    with open(filename, 'r') as f:
        config = yaml.safe_load(f)
    return config

def post_process_histograms(config, histograms):
    """
    Apply normalization and other post-processing to histograms.
    Count the total number of events directly from the LHE file.
    """
    total_events = 0
    total_cross_section = 0.0
    lumi = config.get('integrated_luminosity', 1.0)
    
    for file_cfg in config['files']:
        lhe_file = file_cfg['path']
        cross_section = file_cfg.get('cross_section', 1.0)
        
        # Count events in the LHE file
        event_count = sum(1 for _ in pylhe.read(lhe_file))
        total_events += event_count
        total_cross_section += cross_section
        
        print(f"File: {lhe_file}")
        print(f"  Events: {event_count}")
        print(f"  Cross Section: {cross_section} pb")
    
    print(f"\nTotal Events: {total_events}")
    print(f"Total Cross Section: {total_cross_section} pb")
    
    # Normalize histograms if required
    if config.get('normalize_by_cross_section', False):
        scale_factor = lumi * total_cross_section / total_events
        print(f"Applying normalization with scale factor: {scale_factor}")
        for hist in histograms.values():
            hist.Scale(scale_factor)

    # Add dummy data to histograms if enabled
    if config.get('add_dummy_data', False):
        print("Adding dummy data to histograms...")
        for hist_name, hist in histograms.items():
            add_dummy_data(hist, config['dummy_data_config'])
    
    # Apply other flags (e.g., log scale, stacking)
    if config.get('log_scale', False):
        for hist in histograms.values():
            hist.SetMinimum(0.1)  # Avoid zero bins in log scale
    
    if config.get('stack_histograms', False):
        print("Stacking histograms is currently only supported during plotting.")

def add_dummy_data(histogram, dummy_config):
    """
    Add dummy data to a histogram based on the configuration.
    
    Parameters:
    - histogram: The ROOT histogram to modify.
    - dummy_config: Configuration for generating dummy data, including:
        * distribution: Type of distribution ('gaussian', 'uniform', etc.).
        * params: Parameters for the distribution.
        * n_points: Number of points to generate.
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
    Return a function to extract the desired variable from a TLorentzVector.

    Args:
        variable_name (str): Name of the variable to extract ("pt", "eta", "phi").

    Returns:
        function: A function that takes a particle dictionary and returns the variable value.
    """
    if variable_name == "pt":
        return lambda p: p["vector"].Pt()
    elif variable_name == "eta":
        return lambda p: p["vector"].Eta()
    elif variable_name == "phi":
        return lambda p: p["vector"].Phi()
    else:
        raise ValueError(f"Unsupported variable: {variable_name}")


