#!/bin/bash

echo "Building Sphinx documentation..."
sphinx-build -b html source build

if [ $? -eq 0 ]; then
    echo "Documentation built successfully. Starting web server..."
    # Kill any process using port 8000
    fuser -k 8000/tcp > /dev/null 2>&1 || true
    echo "Access your documentation at http://localhost:8000"
    echo "Press Ctrl+C to stop the server."
    python3 -m http.server 8000 --directory build
else
    echo "Sphinx build failed. Please check the output above for errors."
fi
