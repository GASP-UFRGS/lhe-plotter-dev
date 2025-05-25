"""
process.py

Module for reading and processing LHE files using pylhe and ROOT.
It filters events based on particle IDs and configurable cut conditions,
and yields particle lists suitable for histogramming.

Functions
---------
- get_number_of_events_from_lhe(file_path)
- process_lhe_file_with_summary(file_path, particles_to_include, apply_cuts, cuts, file_cfg, verbose)
- pass_cuts(particles, cuts, verbose)

Dependencies
------------
- pylhe
- tqdm
- ROOT (TLorentzVector)
"""

import pylhe
from tqdm import tqdm
from ROOT import TLorentzVector

def get_number_of_events_from_lhe(file_path):
    """
    Attempt to extract the number of events from the LHE header.

    Parameters
    ----------
    file_path : str
        Path to the LHE file.

    Returns
    -------
    int or None
        Number of events if found, otherwise None.
    """
    with open(file_path, "r") as f:
        for line in f:
            if "Number of Events" in line:
                parts = line.split(":")
                if len(parts) == 2:
                    try:
                        return int(parts[1].strip())
                    except ValueError:
                        pass
            if "<event>" in line:
                break
    return None

def process_lhe_file_with_summary(file_path, particles_to_include, apply_cuts, cuts, file_cfg, verbose=False):
    """
    Process LHE events and yield selected particles per event, optionally applying cuts.

    Parameters
    ----------
    file_path : str
        Path to the LHE file.
    particles_to_include : list of int
        PDG IDs of particles to retain.
    apply_cuts : bool
        Whether to apply the provided cuts to events.
    cuts : list of dict
        Cut configuration. Each dict should have 'function', 'id', 'mode', and optional 'min', 'max'.
    file_cfg : dict
        File-specific configuration including 'cross_section'.
    verbose : bool, optional
        If True, print detailed debug output.

    Yields
    ------
    list of dict
        Particles passing selection, with keys 'pid' and 'vector'.

    Notes
    -----
    Prints a summary of processed events and cross section information at the end.
    """
    total_events = get_number_of_events_from_lhe(file_path)
    if total_events:
        print(f"Found number of events in header: {total_events}")
    else:
        print("No event count found in header. Counting manually...")
        total_events = sum(1 for _ in pylhe.read(file_path))

    events = pylhe.read_lhe_file(file_path).events
    total_read_events = 0
    passed_events = 0

    for event in tqdm(events, total=total_events, desc=f"Processing {file_path}", unit="evt", dynamic_ncols=True, bar_format="{l_bar}{bar} | {n_fmt}/{total_fmt} [{elapsed}<{remaining}]"):
        total_read_events += 1
        particles = []

        for particle in event.particles:
            if particle.id in particles_to_include:
                vec = TLorentzVector()
                vec.SetPxPyPzE(particle.px, particle.py, particle.pz, particle.e)
                particles.append({"pid": particle.id, "vector": vec})

        if apply_cuts and not pass_cuts(particles, cuts, verbose=verbose):
            continue

        if particles:
            passed_events += 1
            yield particles

    total_cross_section = file_cfg["cross_section"]
    print(f"Summary for {file_path}:")
    print(f"Cross section: {total_cross_section} pb")
    print(f"Total events processed: {total_events}")
    print(f"Events passing cuts: {passed_events} ({(passed_events / total_events) * 100:.2f}%)")
    efficiency = passed_events / total_events if total_events > 0 else 0
    cross_section_visible = total_cross_section * efficiency
    print(f"Visible cross section: {cross_section_visible} pb")

def pass_cuts(particles, cuts, verbose=False):
    """
    Determine whether a list of particles satisfies a set of cuts.

    Parameters
    ----------
    particles : list of dict
        Each dict should have keys 'pid' and 'vector' (TLorentzVector).
    cuts : list of dict
        List of cut configurations. Each should contain:
        - 'function': name of TLorentzVector method (e.g. 'Pt()')
        - 'id': list of PDG IDs to which the cut applies
        - 'mode': 'single' or 'pair'
        - 'min' and/or 'max': float bounds
    verbose : bool, optional
        Whether to print detailed cut diagnostics.

    Returns
    -------
    bool
        True if the event passes all cuts, False otherwise.
    """
    if verbose:
        print("\nEvent particle list:")
        for p in particles:
            try:
                pt = p["vector"].Pt()
                print(f"    PID={p['pid']}, Pt={pt:.2f}")
            except Exception as e:
                print(f"    PID={p['pid']} (error computing Pt: {e})")

    for cut in cuts:
        function = cut.get('function')
        mode = cut.get('mode', 'single')
        ids = cut.get('id', [])
        min_val = cut.get('min', float('-inf'))
        max_val = cut.get('max', float('inf'))

        if not function:
            raise ValueError("Missing 'function' in cut definition.")

        selected = [p for p in particles if p["pid"] in ids]

        if not selected:
            if verbose:
                print(f"No matching particles for cut → Rejecting event")
            return False

        if mode == "single":
            for p in selected:
                try:
                    value = eval(f'p["vector"].{function}')
                except Exception as e:
                    raise ValueError(f"Error evaluating '{function}' on particle: {e}")

                if verbose:
                    status = "PASS" if min_val <= value <= max_val else "FAIL"
                    print(f"    PID={p['pid']} → {function} = {value:.2f} ({status})")

                if not (min_val <= value <= max_val):
                    return False

        elif mode == "pair":
            passed_any = False
            for i in range(len(selected)):
                for j in range(i+1, len(selected)):
                    p1, p2 = selected[i], selected[j]
                    combined = p1["vector"] + p2["vector"]
                    try:
                        value = eval(f'combined.{function}')
                    except Exception as e:
                        raise ValueError(f"Error evaluating '{function}' on pair: {e}")

                    if verbose:
                        status = "PASS" if min_val <= value <= max_val else "FAIL"
                        print(f"    Pair ({p1['pid']},{p2['pid']}) → {function} = {value:.2f} ({status})")

                    if min_val <= value <= max_val:
                        passed_any = True
                        break
                if passed_any:
                    break
            if not passed_any:
                if verbose:
                    print("No pair passed → Rejecting event")
                return False
        else:
            raise ValueError(f"Unknown mode '{mode}' in cut definition.")

    if verbose:
        print("Event passed all cuts.")
    return True
