#!/usr/bin/env bash

set -euo pipefail
cd "$(dirname "$0")"

if [[ "${1:-}" == "clean" ]]; then
  echo "Removing Sphinx documentation files..."
  rm -rf source/ build/ Makefile
  echo "Clean complete."
  exit 0
fi

echo "Initializing Sphinx documentation in $(pwd)..."

# Step 1: Run Sphinx quickstart if not already done
if [ -f "source/conf.py" ]; then
  echo "Sphinx already initialized. Skipping quickstart."
else
  sphinx-quickstart -q -p "LHE Plotter" -a "diemort" --sep --makefile --no-batchfile .
fi

# Step 2: Detect platform-specific sed
SED_CMD="sed -i"
case "$(uname)" in
  Darwin) SED_CMD="sed -i ''" ;;
  Linux|MINGW*|MSYS*|CYGWIN*) SED_CMD="sed -i" ;;
  *) echo "Unsupported platform: $(uname)"; exit 1 ;;
esac

# Step 3: Modify conf.py
CONF_FILE="source/conf.py"
PACKAGE_PATH="../lhe_plotter"

# Add Python path
if ! grep -q "sys.path.insert" "$CONF_FILE"; then
  echo "Injecting Python path into $CONF_FILE"
  $SED_CMD "s|^# import sys|import os\\nimport sys\\nsys.path.insert(0, os.path.abspath('$PACKAGE_PATH'))|" "$CONF_FILE"
fi

# Replace or insert the full extensions list
echo "Enabling Sphinx extensions..."
$SED_CMD "/^extensions =/c\\
extensions = [\\
    'sphinx.ext.autodoc',\\
    'sphinx.ext.napoleon',\\
    'sphinx.ext.viewcode',\\
    'sphinx.ext.autosummary',\\
]
" "$CONF_FILE"

# Add theme
if ! grep -q "html_theme = 'sphinx_rtd_theme'" "$CONF_FILE"; then
  echo "Setting theme to sphinx_rtd_theme..."
  $SED_CMD "s|# html_theme = 'alabaster'|html_theme = 'sphinx_rtd_theme'|" "$CONF_FILE"
fi

# Enable autosummary
if ! grep -q "autosummary_generate" "$CONF_FILE"; then
  echo "Enabling autosummary generation..."
  echo "autosummary_generate = True" >> "$CONF_FILE"
fi

# Step 4: Create modules.rst and api.rst
echo "Creating modules.rst and api.rst..."

cat > source/modules.rst <<EOF
Modules
=======

.. toctree::
   :maxdepth: 2

   api
EOF

cat > source/api.rst <<EOF
API Reference
=============

.. automodule:: lhe_plotter.utils
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: lhe_plotter.histo
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: lhe_plotter.process
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: lhe_plotter.plotter
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: lhe_plotter.parser
   :members:
   :undoc-members:
   :show-inheritance:
EOF

# Step 5: Add modules.rst to index.rst if missing
if ! grep -q "modules" source/index.rst; then
  echo "Adding 'modules' to index.rst..."
  awk '/.. toctree::/ {print; print "   modules"; next} 1' source/index.rst > source/index.rst.tmp && mv source/index.rst.tmp source/index.rst
fi

echo "Sphinx setup complete! Run 'make html' from inside the doc/ folder to build your documentation."

