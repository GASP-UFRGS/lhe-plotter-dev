#!/bin/bash

echo "Running LHE plotter test..."

# Activate virtual environment if it exists
if [ -f "./lhe-env/bin/activate" ]; then
  source ./lhe-env/bin/activate
fi

# Define input and output paths
INPUT_FILE="input_test.dat"
HISTO_FILE="histograms_test.yaml"
OUTDIR="test_output"

# Call the Python module as a script using -m
python3 -m lhe_plotter \
  --config "$INPUT_FILE" \
  --histos "$HISTO_FILE" \
  --outdir "$OUTDIR" \
  --auto-plot \
  --verbose

