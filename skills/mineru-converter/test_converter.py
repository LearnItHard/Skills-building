#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MinerU Converter - Local File Conversion Test Script

Usage:
    python test_converter.py <pdf_file_path> [output_dir]

Examples:
    python test_converter.py document.pdf
    python test_converter.py document.pdf ./output
"""

import os
import sys
import time
import subprocess

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from converter import MinerUConverter
from config import MinerUConfig


def check_dependencies():
    """
    Check if required dependencies are installed.
    Returns True if all dependencies are available.
    """
    required = ['requests', 'dotenv', 'docx']
    missing = []
    
    for mod in required:
        try:
            __import__(mod)
        except ImportError:
            # Try python-docx
            if mod == 'docx':
                try:
                    __import__('python_docx')
                except ImportError:
                    missing.append(mod)
            else:
                missing.append(mod)
    
    if missing:
        print("[WARNING] Missing dependencies:", ", ".join(missing))
        print("          Some features may not work.")
        return False
    return True


def install_dependencies():
    """Install required dependencies."""
    print("[INFO] Installing dependencies...")
    try:
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install',
            'requests', 'python-docx', 'python-dotenv'
        ])
        print("[INFO] Dependencies installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to install dependencies: {e}")
        return False


def main():
    # Check dependencies first
    deps_ok = check_dependencies()
    
    if not deps_ok:
        print("\n[INFO] Run: pip install requests python-docx python-dotenv")
        print("       Or let me know if you want me to install them.")
        
        # Ask user if they want to install
        response = input("\nInstall dependencies now? (y/n): ").strip().lower()
        if response == 'y':
            if not install_dependencies():
                return
        else:
            return
    
    # Check arguments
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nPDF files in current directory:")
        for f in os.listdir('.'):
            if f.endswith('.pdf'):
                print(f"  - {f}")
        return
    
    # Get file path
    file_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "./output"
    
    print("=" * 60)
    print("MinerU Converter - Local File Conversion Test")
    print("=" * 60)
    print(f"Input file: {file_path}")
    print(f"Output directory: {output_dir}")
    print()
    
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"[ERROR] File not found: {file_path}")
        return
    
    file_size = os.path.getsize(file_path) / 1024 / 1024
    print(f"File size: {file_size:.2f} MB")
    print()
    
    try:
        # Load config
        print("[1/4] Loading config...")
        config = MinerUConfig.from_env()
        print(f"      API: {config.api_url}")
        print(f"      Token: {config.api_token[:20]}...")
        
        # Create converter
        print("[2/4] Initializing converter...")
        converter = MinerUConverter(config)
        
        # Run conversion
        print("[3/4] Starting conversion...")
        start_time = time.time()
        
        chapters = converter.convert(
            file_path,
            output_dir=output_dir,
            split_chapters=True,
            save_full_md=True
        )
        
        elapsed = time.time() - start_time
        
        # Output results
        print("[4/4] Done!")
        print()
        print("=" * 60)
        print(f"Conversion successful!")
        print(f"  Time elapsed: {elapsed:.1f} seconds")
        print(f"  Chapters generated: {len(chapters)}")
        print(f"  Output directory: {output_dir}")
        print()
        print("Output structure:")
        print(f"  {output_dir}/")
        print(f"  ├── index.json")
        print(f"  ├── filename_full.md")
        
        # Show directory structure
        if os.path.exists(output_dir):
            for item in sorted(os.listdir(output_dir)):
                item_path = os.path.join(output_dir, item)
                if os.path.isdir(item_path):
                    print(f"  ├── {item}/")
                    subfiles = os.listdir(item_path)[:3]
                    for sf in subfiles:
                        print(f"  │   └── {sf}")
                    if len(os.listdir(item_path)) > 3:
                        print(f"  │   └── ... ({len(os.listdir(item_path)) - 3} more)")
                elif item.endswith('.md'):
                    size = os.path.getsize(item_path) / 1024
                    print(f"  ├── {item} ({size:.1f} KB)")
        
    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
    except ValueError as e:
        print(f"[ERROR] {e}")
    except RuntimeError as e:
        print(f"[ERROR] Conversion failed: {e}")
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
