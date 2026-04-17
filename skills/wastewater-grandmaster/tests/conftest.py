import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS_DIR = os.path.join(REPO_ROOT, "scripts")
REFERENCES_DIR = os.path.join(REPO_ROOT, "references")
sys.path.insert(0, SCRIPTS_DIR)
