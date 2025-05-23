import pylhe
from tqdm import tqdm
from ROOT import TLorentzVector

def get_number_of_events_from_lhe(file_path):
    """Quickly scan the LHE header and retrieve the number of events."""
    with open(file_path, "r") as f:
        for line in f:
            if "Number of Events" in line:
                # Extract the number after ":"
                parts = line.split(":")
                if len(parts) == 2:
                    try:
                        return int(parts[1].strip())
                    except ValueError:
                        pass
            if "<event>" in line:
                break  # Stop if events start and header info wasn't found
    return None  # If not found

def process_lhe_file_with_summary(file_path, particles_to_include, apply_cuts, cuts, file_cfg, verbose=False):
    """Process LHE file, apply cuts, and use TLorentzVector for particle kinematics."""
    total_events = get_number_of_events_from_lhe(file_path)
    if total_events:
        print(f"📝 Found number of events in header: {total_events}")
    else:
        print(f"⚠️ No event count found in header. Counting manually...")
        total_events = count_lhe_events(file_path)

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

        if len(particles) > 0:
            passed_events += 1
            yield particles

    # Print summary
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
    Apply cuts: if any particle matching the ID fails, reject the event.
    If verbose=True, print debug messages for each cut check.
    """
    if verbose:
        print("\n📋 Event particle list:")
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

        # Find matching particles
        selected = [p for p in particles if p["pid"] in ids]

        if verbose:
            print("\n📋 Event particle list:")
            for p in particles:
                try:
                    pid = p["pid"]
                    pt = p["vector"].Pt()
                    print(f"    PID={pid}, Pt={pt:.2f}")
                except Exception as e:
                    print(f"    Error in particle: {e}")

        if not selected:
            if verbose:
                print(f"❌ No matching particles found for this cut → Rejecting event")
            return False

        if mode == "single":
            for p in selected:
                try:
                    value = eval(f'p["vector"].{function}')
                except Exception as e:
                    raise ValueError(f"Error evaluating '{function}' on particle: {e}")

                if verbose:
                    status = "✅ PASS" if min_val <= value <= max_val else "❌ FAIL"
                    print(f"    Particle PID={p['pid']} → {function} = {value:.2f} ({status})")

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
                        raise ValueError(f"Error evaluating '{function}' on particle pair: {e}")

                    if verbose:
                        status = "✅ PASS" if min_val <= value <= max_val else "❌ FAIL"
                        print(f"    Particle Pair ({p1['pid']},{p2['pid']}) → {function} = {value:.2f} ({status})")

                    if min_val <= value <= max_val:
                        passed_any = True
                        break
                if passed_any:
                    break

            if not passed_any:
                if verbose:
                    print(f"❌ No pair satisfied {function} cut → Rejecting event")
                return False

        else:
            raise ValueError(f"Unknown mode '{mode}' in cut definition.")

    if verbose:
        print("✅ Event passed all cuts!\n")
    return True

