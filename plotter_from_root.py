from utils import *
import ROOT
import os
import yaml
import random
import argparse
import glob
import sys

def save_canvas_as_macro(canvas, base_name, output_dir):
    macro_path = os.path.join(output_dir, f"{base_name}.C")
    canvas.SaveAs(macro_path)

def load_style_yaml(style_file):
    import yaml
    with open(style_file, "r") as f:
        return yaml.safe_load(f).get("style", {})

def find_histogram_config(base_name, histo_config_list):
    for cfg in histo_config_list:
        if cfg.get("name") == base_name:
            return cfg
    return None

def load_plot_config(yaml_file):
    with open(yaml_file, "r") as f:
        cfg = yaml.safe_load(f)
    return cfg.get("plots", {})

def load_histo_config(yaml_file):
    with open(yaml_file, "r") as f:
        cfg = yaml.safe_load(f)
    return cfg.get("histograms", {})

def extract_basename(hname):
    return hname.split("__")[0]

def extract_label(hname):
    return hname.split("__")[1] if "__" in hname else ""

def group_histograms_by_basename(hist_names):
    grouped = {}
    for h in hist_names:
        base = extract_basename(h)
        grouped.setdefault(base, []).append(h)
    return grouped

def generate_dummy_data(hist_sum):
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

# -----------------------------
# 📈 Drawing Logic
# -----------------------------

def draw_histogram_group(canvas, base, hnames, f, config, histo_config, output_dir, is_first, is_last, multi_pdf_path=None):
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
            c.SaveAs(f"{output_dir}/{hname}.root")
            c.SaveAs(f"{output_dir}/{hname}.png")
            c.SaveAs(f"{output_dir}/{hname}.pdf")
    else:
        ymax = 0

        for i, hname in enumerate(hnames):
            h = f.Get(hname)
            h.SetFillColorAlpha(0,0)
            h.SetLineColor(colors[i % len(colors)])
            h.SetTitle("")
            h.SetLineWidth(2)
            h.SetStats(0)
            label = extract_label(hname)

            base_name = extract_basename(hname)
            cfg = find_histogram_config(base_name, histo_config)
            if cfg:
                xlabel = cfg.get("xlabel", "")
                unit = cfg.get("unit", "")
            else:
                xlabel = ""
                unit = ""

            normalize_xsec = config.get("normalize_by_cross_section", False)
            integrated_lumi = config.get("integrated_luminosity", False)
            lumi = config.get("lumi", 1)

            if xlabel:
                h.GetXaxis().SetTitleOffset(1.1)
                h.GetXaxis().SetTitle(xlabel)

            if normalize_xsec:
                if not normalize_xsec:
                    ylabel = "Events"
                elif normalize_xsec and integrated_lumi:
                    ylabel = "Yield"
                elif normalize_xsec and not integrated_lumi:
                    if xlabel and not unit:
                        ylabel = f"d#sigma/d{xlabel}"
                    elif xlabel and unit:
                        ylabel = f"d#sigma/d{xlabel} ({unit})"
                    else:
                        ylabel = "d#sigma/dx"
                h.GetYaxis().SetTitle(ylabel)

            # Update max
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

        # Save PNG and PDF
        c.SaveAs(f"{output_dir}/{base}.root")
        c.SaveAs(f"{output_dir}/{base}.png")
        c.SaveAs(f"{output_dir}/{base}.pdf")
        save_canvas_as_macro(c,base,output_dir)

        # Save into multipage PDF if needed
        if multi_pdf_path:
            if is_first:
                c.Print(multi_pdf_path + "(")
            c.Print(multi_pdf_path)
            if is_last:
                c.Print(multi_pdf_path + ")")

# -----------------------------
# 🚀 Main Plotting Function
# -----------------------------

def plot_histograms_from_root(root_file_path, input_yaml="input.dat", input_histo="histograms.yaml", output_dir="plots", style_file=None):
    ROOT.gROOT.SetBatch(True)
    os.makedirs(output_dir, exist_ok=True)
    with open(input_yaml, "r") as f:
        config = yaml.safe_load(f)
    label_suffix = build_label_suffix(config)
    multi_pdf_path = os.path.join(output_dir, f"all_plots{label_suffix}.pdf")
    ROOT.gSystem.Exec(f"rm -f {multi_pdf_path}")

    if style_file:
        apply_root_style(style_file)   # apply ROOT style
        style = load_style_yaml(style_file)   # load config dict for canvas, margins
    else:
        style = {}

    input_config = load_plot_config(input_yaml)
    histo_config = load_histo_config(input_histo)

    f = ROOT.TFile.Open(root_file_path)
    if not f or f.IsZombie():
        print("❌ Could not open ROOT file.")
        return

    all_keys = [k.GetName() for k in f.GetListOfKeys()]
    grouped = group_histograms_by_basename(all_keys)

    canvas_width = style.get("canvas", {}).get("width", 800)
    canvas_height = style.get("canvas", {}).get("height", 700)
    #canvas = ROOT.TCanvas("c", "", canvas_width, canvas_height)
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

    print(f"✅ PNGs saved to: {output_dir}/")
    canvas.Print(multi_pdf_path + ")")
    print(f"📄 Multipage PDF created: {multi_pdf_path}")

def apply_root_style(style_file, is_2d=False):
    """Apply ROOT style settings from YAML."""
    with open(style_file, "r") as f:
        style = yaml.safe_load(f)["style"]

    for cmd in style.get("histogram1D_commands", []):
        try:
            if "h->" in cmd:
                exec(cmd.replace("h->", "h."))  # apply per-histogram commands
            else:
                ROOT.gROOT.ProcessLine(cmd + ";")  # global style command
        except Exception as e:
            print(f"⚠️ Failed to apply ROOT command: {cmd} ({e})")

    # Apply specific histogram type commands
    if is_2d:
        commands = style.get("histogram2D_commands", [])
    else:
        commands = style.get("histogram1D_commands", [])

    for cmd in commands:
        try:
            ROOT.gROOT.ProcessLine(cmd + ";")
        except Exception as e:
            print(f"⚠️ Failed to apply ROOT command: {cmd} ({e})")

# -----------------------------
# 🧭 CLI Entry Point
# -----------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot histograms from ROOT file with YAML config.")
    parser.add_argument("--input", "--input_file", dest="root_file", help="Input ROOT file", required=True)
    parser.add_argument("--config", help="Input YAML config for plots", required=True)
    parser.add_argument("--histos", help="External histogram definitions (YAML)")
    parser.add_argument("--outdir", default="plots", help="Output folder for plots")
    parser.add_argument("--style", help="Optional ROOT style YAML file")
    parser.add_argument("--batch", help="Run batch mode on a folder of ROOT+YAML jobs")

    args = parser.parse_args()

    if args.batch:
        job_dirs = [d for d in os.listdir(args.batch) if os.path.isdir(os.path.join(args.batch, d))]
        for job in job_dirs:
            job_path = os.path.join(args.batch, job)
            root_files = glob.glob(os.path.join(job_path, "*.root"))
            yaml_files = glob.glob(os.path.join(job_path, "*.yaml")) + glob.glob(os.path.join(job_path, "*.dat"))
            if not root_files or not yaml_files:
                print(f"❌ Skipping {job}: missing root or config file")
                continue
            print(f"📁 Processing batch: {job}")
            plot_histograms_from_root(
                root_file_path=root_files[0],
                input_yaml=yaml_files[0],
                input_histo=yaml_files[1],
                output_dir=os.path.join(job_path, "plots"),
                style_file=args.style
            )
    else:
        plot_histograms_from_root(
            root_file_path=args.root_file,
            input_yaml=args.config,
            input_histo=args.histos,
            output_dir=args.outdir,
            style_file=args.style
        )
