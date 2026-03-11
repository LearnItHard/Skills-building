"""
Chapter Splitter Module

Splits Markdown content by headers into separate chapter files.
Generates index.json for chapter navigation.
Outputs to subdirectories by chapter hierarchy.
"""

import re
import json
import os
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any


@dataclass
class Chapter:
    """Represents a document chapter."""
    
    title: str
    level: int
    content: str = ""
    file_path: Optional[str] = None
    dir_path: Optional[str] = None  # New: directory path for this chapter
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    children: List["Chapter"] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert chapter to dictionary (excluding content for index)."""
        return {
            "title": self.title,
            "level": self.level,
            "file": self.file_path,
            "dir": self.dir_path,
            "page_start": self.page_start,
            "page_end": self.page_end,
            "children": [c.to_dict() for c in self.children]
        }


class ChapterSplitter:
    """Splits Markdown content into chapters by headers."""
    
    # Regex to match Markdown headers: ^(#{1,6})\s+(.+)$
    HEADER_PATTERN = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
    
    def __init__(self, base_filename: str = "chapter"):
        """
        Initialize splitter.
        
        Args:
            base_filename: Base name for generated files (default: "chapter")
        """
        self.base_filename = base_filename
    
    def split(self, md_content: str) -> List[Chapter]:
        """
        Split Markdown content into chapters.
        
        Args:
            md_content: Full Markdown content
            
        Returns:
            List of Chapter objects
        """
        chapters = []
        
        # Find all headers with their positions
        matches = list(self.HEADER_PATTERN.finditer(md_content))
        
        if not matches:
            # No headers found - treat entire content as one chapter
            return [Chapter(
                title="Document",
                level=1,
                content=md_content.strip()
            )]
        
        for i, match in enumerate(matches):
            level = len(match.group(1))
            title = match.group(2).strip()
            
            # Determine content range
            start_pos = match.start()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(md_content)
            
            # Extract content (including the header)
            content = md_content[start_pos:end_pos].strip()
            
            chapter = Chapter(
                title=title,
                level=level,
                content=content
            )
            chapters.append(chapter)
        
        return chapters
    
    def build_hierarchy(self, chapters: List[Chapter]) -> List[Chapter]:
        """
        Build chapter hierarchy based on header levels.
        
        Args:
            chapters: Flat list of chapters
            
        Returns:
            Hierarchical chapter structure
        """
        if not chapters:
            return []
        
        root = []
        stack = []
        
        for chapter in chapters:
            # Pop stack until we find parent or empty
            while stack and stack[-1].level >= chapter.level:
                stack.pop()
            
            if stack:
                # Add as child to current parent
                stack[-1].children.append(chapter)
            else:
                # Add to root
                root.append(chapter)
            
            # Push current chapter to stack
            stack.append(chapter)
        
        return root
    
    def generate_filenames(self, chapters: List[Chapter], parent_dir: str = "") -> None:
        """
        Generate filenames and directory paths for all chapters.
        Creates subdirectories for each top-level chapter.
        
        Args:
            chapters: List of chapters (modified in-place)
            parent_dir: Parent directory path
        """
        counters = {}
        
        for chapter in chapters:
            level = chapter.level
            
            # Initialize counter for this level
            if level not in counters:
                counters[level] = 0
            
            counters[level] += 1
            
            # Reset deeper levels
            for l in list(counters.keys()):
                if l > level:
                    counters[l] = 0
            
            # Build filename prefix
            parts = []
            for l in sorted(counters.keys()):
                if counters[l] > 0:
                    parts.append(f"{counters[l]:02d}")
            
            # Sanitize title for filename and directory
            safe_title = re.sub(r'[^\w\s-]', '', chapter.title).strip()
            safe_title = re.sub(r'[-\s]+', '-', safe_title)
            safe_title = safe_title[:30]  # Limit length
            
            # Create directory name (for top-level chapters, create subdir)
            if level == 1:
                dir_name = f"{'-'.join(parts)}-{safe_title}"
                chapter.dir_path = dir_name
            else:
                # Use parent's directory
                chapter.dir_path = parent_dir
            
            # Build filename
            filename_prefix = f"{'-'.join(parts)}"
            if safe_title:
                filename_prefix += f"-{safe_title}"
            
            chapter.file_path = f"{filename_prefix}.md"
            
            # Process children with current directory
            if chapter.children:
                self.generate_filenames(chapter.children, chapter.dir_path)
    
    def save_chapters(
        self,
        chapters: List[Chapter],
        output_dir: str,
        generate_index: bool = True,
        save_full: bool = True,
        full_content: str = ""
    ) -> Dict[str, Any]:
        """
        Save chapters to files and optionally generate index.
        
        Creates subdirectory structure:
        output/
        ├── index.json
        ├── filename_full.md
        ├── 01-chapter-a/
        │   ├── 01-chapter-a.md
        │   ├── 01-01-sub-section.md
        │   └── ...
        ├── 02-chapter-b/
        │   ├── 02-chapter-b.md
        │   └── ...
        └── ...
        
        Args:
            chapters: List of chapters
            output_dir: Output directory path
            generate_index: Whether to generate index.json
            save_full: Whether to save full.md
            full_content: Full markdown content for full.md
            
        Returns:
            Index dictionary
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate filenames and directories
        self.generate_filenames(chapters)
        
        # Save each chapter to its subdirectory
        for chapter in chapters:
            if chapter.file_path and chapter.dir_path:
                # Create chapter's directory
                chapter_dir = output_path / chapter.dir_path
                chapter_dir.mkdir(parents=True, exist_ok=True)
                
                # Save chapter file
                file_path = chapter_dir / chapter.file_path
                file_path.write_text(chapter.content, encoding='utf-8')
        
        # Save full content
        if save_full and full_content:
            full_path = output_path / f"{self.base_filename}_full.md"
            full_path.write_text(full_content, encoding='utf-8')
        
        # Build and save index
        if generate_index:
            hierarchy = self.build_hierarchy(chapters)
            index = {
                "source_file": self.base_filename,
                "total_chapters": len(chapters),
                "structure": "directory",
                "chapters": [c.to_dict() for c in hierarchy]
            }
            
            index_path = output_path / "index.json"
            index_path.write_text(
                json.dumps(index, ensure_ascii=False, indent=2),
                encoding='utf-8'
            )
            
            return index
        
        return {}
    
    def split_and_save(
        self,
        md_content: str,
        output_dir: str,
        base_filename: Optional[str] = None,
        save_full: bool = True
    ) -> Dict[str, Any]:
        """
        One-step split and save operation.
        
        Args:
            md_content: Markdown content
            output_dir: Output directory
            base_filename: Optional base filename override
            save_full: Whether to save full.md
            
        Returns:
            Index dictionary
        """
        if base_filename:
            self.base_filename = base_filename
        
        chapters = self.split(md_content)
        return self.save_chapters(
            chapters, 
            output_dir, 
            save_full=save_full,
            full_content=md_content
        )


def split_markdown_by_chapters(
    md_content: str,
    output_dir: str,
    base_filename: str = "chapter",
    save_full: bool = True
) -> Dict[str, Any]:
    """
    Convenience function to split Markdown and save chapters.
    
    Args:
        md_content: Markdown content
        output_dir: Output directory
        base_filename: Base name for chapter files
        save_full: Whether to save full.md
        
    Returns:
        Index dictionary
    """
    splitter = ChapterSplitter(base_filename)
    return splitter.split_and_save(md_content, output_dir, save_full=save_full)
