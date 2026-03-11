"""
DOCX to PDF Conversion Module

Converts Word documents (.doc, .docx) to PDF format.
Supports LibreOffice CLI and python-docx2pdf as fallback.
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional
import shutil


class DocxToPdfConverter:
    """Converts DOCX files to PDF format."""
    
    def __init__(self, timeout: int = 60):
        self.timeout = timeout
        self.libreoffice_path = self._find_libreoffice()
    
    def _find_libreoffice(self) -> Optional[str]:
        """Find LibreOffice executable path."""
        # Common paths for different OS
        possible_paths = [
            # Windows
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
            # macOS
            "/Applications/LibreOffice.app/Contents/MacOS/soffice",
            # Linux
            "/usr/bin/soffice",
            "/usr/bin/libreoffice",
            "/usr/lib/libreoffice/program/soffice",
        ]
        
        for path in possible_paths:
            if os.path.isfile(path):
                return path
        
        # Try which/where command
        try:
            result = shutil.which("soffice") or shutil.which("libreoffice")
            if result:
                return result
        except Exception:
            pass
        
        return None
    
    def is_available(self) -> bool:
        """Check if DOCX to PDF conversion is available."""
        return self.libreoffice_path is not None
    
    def convert(self, docx_path: str, output_dir: Optional[str] = None) -> str:
        """
        Convert DOCX to PDF.
        
        Args:
            docx_path: Path to DOCX file
            output_dir: Output directory (default: same as input)
            
        Returns:
            Path to generated PDF file
            
        Raises:
            RuntimeError: If conversion fails or LibreOffice not found
            FileNotFoundError: If input file doesn't exist
        """
        docx_path = Path(docx_path)
        
        if not docx_path.exists():
            raise FileNotFoundError(f"Input file not found: {docx_path}")
        
        if not self.is_available():
            raise RuntimeError(
                "LibreOffice not found. Please install LibreOffice:\n"
                "- Windows: https://www.libreoffice.org/download/download/\n"
                "- macOS: brew install --cask libreoffice\n"
                "- Linux: sudo apt-get install libreoffice"
            )
        
        # Determine output directory
        if output_dir is None:
            output_dir = docx_path.parent
        else:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        
        # LibreOffice command
        cmd = [
            self.libreoffice_path,
            "--headless",
            "--convert-to", "pdf",
            "--outdir", str(output_dir),
            str(docx_path)
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            if result.returncode != 0:
                raise RuntimeError(
                    f"LibreOffice conversion failed:\n"
                    f"stdout: {result.stdout}\n"
                    f"stderr: {result.stderr}"
                )
            
            # Generated PDF path
            pdf_name = docx_path.stem + ".pdf"
            pdf_path = output_dir / pdf_name
            
            if not pdf_path.exists():
                raise RuntimeError(
                    f"PDF file not created. Expected: {pdf_path}"
                )
            
            return str(pdf_path)
            
        except subprocess.TimeoutExpired:
            raise RuntimeError(
                f"Conversion timed out after {self.timeout} seconds"
            )
        except Exception as e:
            raise RuntimeError(f"Conversion failed: {e}")
    
    def convert_with_temp(self, docx_path: str) -> str:
        """
        Convert DOCX to PDF using temporary directory.
        Useful for intermediate conversions.
        
        Returns:
            Path to generated PDF in temp directory
        """
        temp_dir = tempfile.mkdtemp(prefix="mineru_docx_")
        return self.convert(docx_path, temp_dir)


def convert_docx_to_pdf(docx_path: str, output_dir: Optional[str] = None) -> str:
    """
    Convenience function to convert DOCX to PDF.
    
    Args:
        docx_path: Path to DOCX file
        output_dir: Output directory (optional)
        
    Returns:
        Path to generated PDF
    """
    converter = DocxToPdfConverter()
    return converter.convert(docx_path, output_dir)
