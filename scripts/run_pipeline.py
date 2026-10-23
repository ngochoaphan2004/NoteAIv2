#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/run_pipeline.py -> Forwarder sang scripts/_py_/run_pipeline.py
"""
import sys
import runpy
from pathlib import Path

target = Path(__file__).resolve().parent / "_py_" / "run_pipeline.py"
runpy.run_path(str(target), run_name="__main__")
