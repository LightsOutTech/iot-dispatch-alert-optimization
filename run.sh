#!/usr/bin/env bash
set -e
echo "=== Running Optimization Solution ==="
python3 solution.py
echo ""
echo "=== Running Unit Tests ==="
python3 -m unittest test_solution.py
