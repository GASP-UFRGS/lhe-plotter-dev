#!/bin/bash
set -e

echo "Running LHE plotter test..."
python3 ../lhe-plotter.py \
  --config input_test.dat \
  --histos histograms_test.yaml \
  --output output_test.root \
  --auto-plot \
  --outdir test_output \

