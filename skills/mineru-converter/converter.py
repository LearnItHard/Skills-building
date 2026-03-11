"""
MinerU Converter Core Module

Main entry point for converting documents to Markdown using MinerU API v4.
Supports PDF, DOC, DOCX, and image files from public URLs or local files.
"""

import os
import io
import time
import json
import zipfile
from pathlib import Path
from typing import List, Optional, Union, Dict, Any
import requests

from config import MinerUConfig, SUPPORTED_INPUT_FORMATS
from docx_to_pdf import DocxToPdfConverter
from chapter_splitter import ChapterSplitter, Chapter


class MinerUConverter:
    """Main converter class for MinerU document conversion."""
    
    def __init__(self, config: Optional[MinerUConfig] = None):
        self.config = config or MinerUConfig.from_env()
        self.docx_converter = DocxToPdfConverter()
        self.chapter_splitter = ChapterSplitter()
    
    def convert(self, file_path: str, output_dir: Optional[str] = None, 
                split_chapters: bool = True, save_full_md: bool = True) -> Union[List[Chapter], str]:
        """Convert local file to Markdown."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        ext = file_path.suffix.lower()
        if ext not in SUPPORTED_INPUT_FORMATS:
            raise ValueError(f"Unsupported format: {ext}")
        
        # Upload and convert
        print(f"Uploading file: {file_path.name}")
        batch_id = self._upload_and_submit(str(file_path))
        
        # Wait for completion
        print(f"Processing (batch: {batch_id})...")
        md_content = self._wait_for_batch(batch_id)
        
        # Save output
        if output_dir is None:
            output_dir = self.config.output_dir
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        base_name = file_path.stem
        if save_full_md:
            (output_path / f"{base_name}_full.md").write_text(md_content, encoding='utf-8')
        
        if split_chapters:
            chapters = self._split_into_chapters(md_content, output_path, base_name)
            print(f"Created {len(chapters)} chapters")
            return chapters
        return md_content
    
    def convert_from_url(self, file_url: str, output_dir: Optional[str] = None,
                        split_chapters: bool = True, save_full_md: bool = True) -> Union[List[Chapter], str]:
        """Convert file from public URL."""
        if output_dir is None:
            output_dir = self.config.output_dir
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        print(f"Converting from URL: {file_url}")
        
        # Submit URL task
        headers = self.config.get_headers()
        resp = requests.post(
            f"{self.config.api_url}/extract/task",
            headers=headers,
            json={
                "url": file_url,
                "enable_formula": self.config.enable_formula,
                "enable_table": self.config.enable_table,
                "language": self.config.language,
                "is_ocr": self.config.is_ocr,
                "model_version": self.config.model_version
            },
            timeout=30
        )
        result = resp.json()
        if result.get("code") != 0:
            raise RuntimeError(f"API error: {result.get('msg')}")
        
        task_id = result["data"]["task_id"]
        print(f"Task submitted: {task_id}")
        
        # Wait for completion
        md_content = self._wait_for_task(task_id)
        
        from urllib.parse import urlparse
        base_name = Path(urlparse(file_url).path).stem or "document"
        
        if save_full_md:
            (output_path / f"{base_name}_full.md").write_text(md_content, encoding='utf-8')
        
        if split_chapters:
            chapters = self._split_into_chapters(md_content, output_path, base_name)
            print(f"Created {len(chapters)} chapters")
            return chapters
        return md_content
    
    def _upload_and_submit(self, file_path: str) -> str:
        """Upload local file and get batch ID."""
        file_path = Path(file_path)
        headers = self.config.get_headers()
        
        # Step 1: Get upload URL
        upload_url = f"{self.config.api_url}/file-urls/batch"
        resp = requests.post(
            upload_url,
            headers=headers,
            json={
                "files": [{"name": file_path.name}],
                "enable_formula": self.config.enable_formula,
                "enable_table": self.config.enable_table,
                "language": self.config.language,
                "model_version": self.config.model_version
            },
            timeout=30
        )
        result = resp.json()
        if result.get("code") != 0:
            raise RuntimeError(f"Failed to get upload URL: {result.get('msg')}")
        
        upload_urls = result["data"]["file_urls"]
        if not upload_urls:
            raise RuntimeError("No upload URL returned")
        
        batch_id = result["data"]["batch_id"]
        
        # Step 2: Upload file
        upload_link = upload_urls[0]
        print(f"Uploading to temporary storage...")
        
        with open(file_path, 'rb') as f:
            upload_resp = requests.put(upload_link, data=f, timeout=300)
        
        if upload_resp.status_code != 200:
            raise RuntimeError(f"Upload failed: {upload_resp.status_code}")
        
        print(f"Upload complete")
        return batch_id
    
    def _wait_for_batch(self, batch_id: str) -> str:
        """Wait for batch completion and return markdown."""
        headers = self.config.get_headers()
        url = f"{self.config.api_url}/extract-results/batch/{batch_id}"
        
        for attempt in range(self.config.max_poll_attempts):
            resp = requests.get(url, headers=headers, timeout=30)
            result = resp.json()
            
            if result.get("code") != 0:
                raise RuntimeError(f"Status check failed: {result.get('msg')}")
            
            data = result.get("data", {})
            extract_results = data.get("extract_result", [])
            
            if not extract_results:
                if attempt % 5 == 0:
                    print(f"  Waiting for task creation...")
                time.sleep(self.config.poll_interval)
                continue
            
            # Check first result
            result_item = extract_results[0]
            state = result_item.get("state", "").lower()
            
            if state in ["done", "success"]:
                zip_url = result_item.get("full_zip_url")
                if zip_url:
                    return self._extract_from_zip(zip_url)
                raise RuntimeError("No result URL")
            
            elif state in ["failed", "error", "failure"]:
                raise RuntimeError(f"Task failed: {result_item.get('err_msg', state)}")
            
            elif attempt % 5 == 0:
                print(f"  Status: {state} ({attempt+1}/{self.config.max_poll_attempts})")
            
            time.sleep(self.config.poll_interval)
        
        raise RuntimeError("Polling timeout")
    
    def _wait_for_task(self, task_id: str) -> str:
        """Wait for task completion and return markdown."""
        headers = self.config.get_headers()
        url = f"{self.config.api_url}/extract/task/{task_id}"
        
        for attempt in range(self.config.max_poll_attempts):
            resp = requests.get(url, headers=headers, timeout=30)
            result = resp.json()
            
            if result.get("code") != 0:
                raise RuntimeError(f"Status check failed: {result.get('msg')}")
            
            data = result.get("data", {})
            state = data.get("state", "").lower()
            
            if state in ["done", "success"]:
                zip_url = data.get("full_zip_url")
                if zip_url:
                    return self._extract_from_zip(zip_url)
                raise RuntimeError("No result URL")
            
            elif state in ["failed", "error", "failure"]:
                raise RuntimeError(f"Task failed: {data.get('err_msg', state)}")
            
            elif attempt % 5 == 0:
                print(f"  Status: {state} ({attempt+1}/{self.config.max_poll_attempts})")
            
            time.sleep(self.config.poll_interval)
        
        raise RuntimeError("Polling timeout")
    
    def _extract_from_zip(self, zip_url: str) -> str:
        """Extract markdown from result zip."""
        resp = requests.get(zip_url, timeout=120)
        resp.raise_for_status()
        
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            md_files = [f for f in zf.namelist() if f.endswith('.md')]
            if not md_files:
                raise RuntimeError("No markdown in result")
            
            main_file = 'full.md' if 'full.md' in md_files else md_files[0]
            with zf.open(main_file) as f:
                return f.read().decode('utf-8')
    
    def _split_into_chapters(self, md_content: str, output_path: Path, base_name: str) -> List[Chapter]:
        """Split markdown into chapters with directory structure."""
        splitter = ChapterSplitter(base_name)
        
        # Use the new split_and_save method that creates subdirectories
        index = splitter.split_and_save(
            md_content, 
            str(output_path), 
            base_filename=base_name,
            save_full=False  # Already saved in convert()
        )
        
        # Get chapters for return (need to re-split to get Chapter objects)
        chapters = splitter.split(md_content)
        splitter.generate_filenames(chapters)
        
        return chapters
        """Split markdown into chapters."""
        splitter = ChapterSplitter(base_name)
        chapters = splitter.split(md_content)
        splitter.generate_filenames(chapters)
        
        for ch in chapters:
            if ch.file_path:
                (output_path / ch.file_path).write_text(ch.content, encoding='utf-8')
        
        hierarchy = splitter.build_hierarchy(chapters)
        index = {
            "source_file": base_name,
            "total_chapters": len(chapters),
            "chapters": [c.to_dict() for c in hierarchy]
        }
        (output_path / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2))
        
        return chapters


def convert_document(file_path: str, api_token: Optional[str] = None,
                    output_dir: str = "./output", split_chapters: bool = True):
    """Convenience function for local file conversion."""
    config = MinerUConfig(api_token=api_token) if api_token else MinerUConfig.from_env()
    converter = MinerUConverter(config)
    return converter.convert(file_path, output_dir, split_chapters)
