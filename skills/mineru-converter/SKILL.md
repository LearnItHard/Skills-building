---
name: mineru-document-converter
description: Use when converting PDF, DOC, DOCX documents to Markdown with chapter splitting, formula/table recognition, and structured output organization via MinerU API v4
---

# MinerU Document Converter

## Overview

High-quality document conversion tool using **MinerU API v4**. Converts PDF and Word documents from **local files** or **public URLs** to structured Markdown with automatic chapter detection and splitting.

**Core capabilities:**
- PDF/Image → Markdown (local file or public URL)
- DOC/DOCX → PDF → Markdown
- Automatic chapter splitting by headers
- Formula and table recognition
- **Async API with polling**
- PDF/Image → Markdown (via public URL)
- DOC/DOCX → PDF → Markdown
- Automatic chapter splitting by headers
- Formula and table recognition
- **Async API with polling**

## Important: API v4 Usage

**MinerU API v4 supports two input methods:**

1. **Local File Upload** (推荐) - 自动上传到临时存储并处理
2. **Public URL** - 提供文件的公开访问链接

**MinerU API v4 requires files to be accessible via public HTTP URL.**

The API does NOT support direct file upload. You must:
1. Host your file on a public server (cloud storage, CDN, etc.)
2. Provide the public URL to the converter

## When to Use

**Use this skill when:**
- Converting academic papers to Markdown
- Processing technical documentation with formulas/tables
- Need structured output with chapter hierarchy
- Batch processing multiple documents from URLs
- OCR required for scanned documents

**Don't use when:**
- Simple text extraction (use basic tools)
- Document has no clear structure (no headers)
- MinerU API is unavailable
- Files are only available locally (need to upload first)
- Simple text extraction (use basic tools)
- Document has no clear structure (no headers)
- MinerU API is unavailable

## Prerequisites

1. **Get API Token**: https://mineru.net/apiManage

2. **Set Up Python Environment** (recommend virtual environment):
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate
   # Windows: venv\Scripts\activate
   # macOS/Linux: source venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   
   **Dependencies** (`requirements.txt`):
   - `requests>=2.28.0` - HTTP requests
   - `python-docx>=0.8.11` - DOCX file handling
   - `python-dotenv>=1.0.0` - .env file support

4. **Configure API Token** (choose one method):
   
   **Method A: JSON config file** (recommended - auto-detected):
   ```bash
   # Copy example
   cp config.json.example config.json
   
   # Edit with your token
   # Searches: ./config.json, ~/config.json, ~/.mineru/config.json
   ```
   
   **Method B: .env file**:
   ```bash
   # Copy example
   cp .env.example .env
   
   # Edit .env with your token
   MINERU_API_TOKEN=your_token_here
   ```
4. **Configure API Token** (choose one method):
   
   **Method A: .env file** (recommended):
   ```bash
   # Copy example
   cp .env.example .env
   
   # Edit .env with your token
   MINERU_API_TOKEN=your_token_here
   ```
   
   **Method B: Environment variable**:
   ```bash
   # Windows PowerShell
   $env:MINERU_API_TOKEN="your_token_here"
   
   # macOS/Linux
   export MINERU_API_TOKEN="your_token_here"
   ```
   
   **Method C: Direct in code**:
   ```python
   from converter import MinerUConverter
   from config import MinerUConfig
   
   converter = MinerUConverter(
       MinerUConfig(api_token="your_token_here")
   )
   ```

## Quick Start

### Convert Local File (Recommended)

```python
from converter import MinerUConverter
from config import MinerUConfig

# Load config from .env
config = MinerUConfig.from_env()
converter = MinerUConverter(config)

# Convert local PDF file
chapters = converter.convert(
    "document.pdf",           # Local file path
    output_dir="./output",
    split_chapters=True
)

for chapter in chapters:
    print(f"{chapter.title} -> {chapter.file_path}")
```

### Convert from Public URL

```python
from converter import MinerUConverter
from config import MinerUConfig

# Load config from .env
config = MinerUConfig.from_env()
converter = MinerUConverter(config)

# Convert from public URL
chapters = converter.convert_from_url(
    "https://example.com/document.pdf",
    output_dir="./output",
    split_chapters=True
)

for chapter in chapters:
    print(f"{chapter.title} -> {chapter.file_path}")
```

### Convert with API Token Directly

For local files:
```python
from converter import convert_document

chapters = convert_document(
    file_path="document.pdf",
    api_token="your_token_here",
    output_dir="./output"
)
```

For public URLs:
```python
from converter import convert_document_from_url

chapters = convert_document_from_url(
    file_url="https://your-cdn.com/file.pdf",
    api_token="your_token_here",
    output_dir="./output"
)
```

```python
from converter import MinerUConverter
from config import MinerUConfig

# Load config from .env
config = MinerUConfig.from_env()
converter = MinerUConverter(config)

# Convert from public URL
chapters = converter.convert_from_url(
    "https://example.com/document.pdf",
    output_dir="./output",
    split_chapters=True
)

for chapter in chapters:
    print(f"{chapter.title} -> {chapter.file_path}")
```

### Convert with API Token Directly

```python
from converter import convert_document_from_url

chapters = convert_document_from_url(
    file_url="https://your-cdn.com/file.pdf",
    api_token="your_token_here",
    output_dir="./output"
)
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MINERU_API_TOKEN` | - | **Required** API token |
| `MINERU_API_URL` | `https://mineru.net/api/v4` | API v4 endpoint |
| `MINERU_ENABLE_FORMULA` | `true` | Enable formula recognition |
| `MINERU_ENABLE_TABLE` | `true` | Enable table recognition |
| `MINERU_LANGUAGE` | `ch` | Languages: `ch`, `en`, `ch,en` |
| `MINERU_IS_OCR` | `false` | Force OCR mode |
| `MINERU_MODEL_VERSION` | `vlm` | Model: `vlm`, `MinerU-HTML` |
| `MINERU_POLL_INTERVAL` | `3` | Seconds between status checks |
| `MINERU_MAX_POLL_ATTEMPTS` | `100` | Maximum polling attempts |

### Code Configuration

```python
from config import MinerUConfig

config = MinerUConfig(
    api_token="your_token",
    enable_formula=True,
    enable_table=True,
    language="ch,en",
    model_version="vlm",
    poll_interval=5
)
```

## Supported Formats

| Format | Extension | Notes |
|--------|-----------|-------|
| PDF | `.pdf` | Via public URL |
| Word | `.doc`, `.docx` | Via public URL |
| PowerPoint | `.ppt`, `.pptx` | Via public URL |
| Images | `.png`, `.jpg`, `.jpeg` | Via public URL, OCR mode |

## API v4 Workflow

```
┌─────────────┐    POST /extract/task    ┌─────────────┐
│  Your Code  │ ───────────────────────> │  MinerU API │
│             │  {url, enable_formula..} │             │
└─────────────┘                          └─────────────┘
                                                │
                                                │ Returns task_id
                                                ▼
┌─────────────┐    GET /extract/task/{id}  ┌─────────────┐
│  Your Code  │ ───────────────────────> │  MinerU API │
│  (polling)  │                          │  (async)    │
└─────────────┘                          └─────────────┘
       ▲                                          │
       └──────────────────────────────────────────┘
                         Returns result_url when SUCCESS
```

## Output Structure

```
output/
├── index.json              # Chapter index with hierarchy
├── document_full.md        # Full Markdown (if requested)
├── chapter-01-Introduction.md
├── chapter-02-Background.md
├── chapter-02-01-History.md
└── chapter-02-02-Current-State.md
```

### index.json Format

```json
{
  "source_file": "document",
  "total_chapters": 5,
  "chapters": [
    {
      "title": "Introduction",
      "level": 1,
      "file": "chapter-01-Introduction.md",
      "children": []
    },
    {
      "title": "Background",
      "level": 1,
      "file": "chapter-02-Background.md",
      "children": [
        {
          "title": "History",
          "level": 2,
          "file": "chapter-02-01-History.md",
          "children": []
        }
      ]
    }
  ]
}
```

## Advanced Usage

### Chapter Splitting Only

```python
from chapter_splitter import split_markdown_by_chapters

index = split_markdown_by_chapters(
    md_content="# Chapter 1\n...",
    output_dir="./chapters",
    base_filename="doc"
)
```

### Batch Processing from URLs

```python
from converter import MinerUConverter

converter = MinerUConverter()

urls = [
    "https://cdn.example.com/doc1.pdf",
    "https://cdn.example.com/doc2.pdf",
]

for url in urls:
    try:
        chapters = converter.convert_from_url(
            url,
            output_dir=f"./output/{url.split('/')[-1].split('.')[0]}"
        )
        print(f"Converted: {len(chapters)} chapters")
    except Exception as e:
        print(f"Failed: {e}")
```

## For AI Agents

**When user wants to use this skill, follow these steps:**

### Step 1: Check Python Environment
```bash
python --version  # Need 3.8+
```

### Step 2: Create and Activate Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install requests python-docx python-dotenv
# or
pip install -r requirements.txt
```

### Step 4: Configure API Token
Ask user for MinerU API token (from https://mineru.net/apiManage)

Create `.env` file:
```
MINERU_API_TOKEN=user_provided_token
```

### Step 5: Execute Conversion

For local files (recommended):
```python
from converter import MinerUConverter
from config import MinerUConfig

config = MinerUConfig.from_env()  # Auto-reads .env
converter = MinerUConverter(config)

# Convert local file - automatically uploads and processes
chapters = converter.convert(
    "path/to/your/file.pdf",
    output_dir="./output"
)
```

For public URLs:
```python
chapters = converter.convert_from_url(
    "https://example.com/file.pdf",
    output_dir="./output"
)
```

### Step 6: Handle Results
- Check `output_dir` for generated Markdown files
- `index.json` contains chapter hierarchy
- `*_full.md` contains complete document
**Important**: API v4 requires public URL.

Ask user:
- "Is your file already hosted on a public URL?"
- If NO: "You need to upload the file to cloud storage first (AWS S3, GitHub, etc.)"

### Step 6: Execute Conversion
```python
from converter import MinerUConverter
from config import MinerUConfig
## Uploading Files (Optional)

Local files are automatically uploaded to temporary storage and processed. If you need to use public URLs instead, here are options:

### Option 1: AWS S3 (Recommended)
```python
import boto3

s3 = boto3.client('s3')
s3.upload_file('local.pdf', 'bucket', 'file.pdf', ExtraArgs={'ACL': 'public-read'})
url = "https://bucket.s3.amazonaws.com/file.pdf"
```

### Option 2: GitHub (for small files)
Upload to GitHub repository and use raw URL:
```
https://raw.githubusercontent.com/user/repo/main/file.pdf
```

### Option 3: Temporary hosting services
- File.io
- Transfer.sh
- Catbox.moe
config = MinerUConfig.from_env()  # Auto-reads .env
converter = MinerUConverter(config)

# Use convert_from_url with public URL
chapters = converter.convert_from_url(
    "https://user-provided-url.com/file.pdf",
    output_dir="./output"
)
```

## Uploading Files for Conversion

Since MinerU API v4 requires public URLs, here are upload options:

### Option 1: AWS S3 (Recommended)
```python
import boto3

s3 = boto3.client('s3')
s3.upload_file('local.pdf', 'bucket', 'file.pdf', ExtraArgs={'ACL': 'public-read'})
url = "https://bucket.s3.amazonaws.com/file.pdf"
```

### Option 2: GitHub (for small files)
Upload to GitHub repository and use raw URL:
```
https://raw.githubusercontent.com/user/repo/main/file.pdf
```

### Option 3: Temporary hosting services
- File.io
- Transfer.sh
- Catbox.moe

## Common Mistakes

| Issue | Cause | Solution |
|-------|-------|----------|
| `MINERU_API_TOKEN not set` | Missing env var | Export token or create .env file |
| `Task failed` | File not accessible | Check file exists and is valid |
| `Timeout waiting for result` | Large file | Increase `MAX_POLL_ATTEMPTS` |
| `No markdown content` | OCR failed | Try `is_ocr=true` for image-based PDFs |
| `401 Unauthorized` | Invalid token | Check token from https://mineru.net/apiManage |
| `Upload failed` | Network issue | Retry or check file size (<200MB) |
|-------|-------|----------|
| `MINERU_API_TOKEN not set` | Missing env var | Export token or create .env file |
| `Local file conversion requires HTTP URL` | Using local path | Host file on public URL first |
| `Task failed` | File URL not accessible | Check URL is public and valid |
| `Timeout waiting for result` | Large file | Increase `MAX_POLL_ATTEMPTS` |
| `No markdown content` | OCR failed | Try `is_ocr=true` for image-based PDFs |
| `401 Unauthorized` | Invalid token | Check token from https://mineru.net/apiManage |

## API Rate Limits

- 2000 pages/day at highest priority
- Pages > 2000: reduced priority
- Single file max: 200MB, 600 pages
- Rate limit: Check response headers

## Error Handling

```python
from converter import MinerUConverter

converter = MinerUConverter()

try:
    chapters = converter.convert_from_url("https://example.com/file.pdf")
except ValueError as e:
    print(f"Invalid input: {e}")
except RuntimeError as e:
    print(f"Conversion failed: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Module Reference

| Module | Purpose |
|--------|---------|
| `converter.py` | Main MinerUConverter class |
| `config.py` | Configuration management |
| `docx_to_pdf.py` | DOCX to PDF conversion |
| `chapter_splitter.py` | Markdown chapter splitting |

## Troubleshooting

**Q: Can I convert local files?**
A: Yes! Use `converter.convert("file.pdf")` - files are automatically uploaded to temporary storage.

**Q: What file formats are supported?**
A: PDF, DOC, DOCX, PPT, PPTX, PNG, JPG, JPEG. Maximum 200MB per file.

**Q: Task status stuck at PENDING?**
A: Large files take time. Increase `poll_interval` and `max_poll_attempts`.

**Q: Formula/table recognition not working?**
A: Set `enable_formula=true` and `enable_table=true` in config.

**Q: Chinese text not recognized correctly?**
A: Set `language="ch"` (default) or `"ch,en"` for bilingual.

**Q: Can I convert local files?**
A: No, API v4 requires public URLs. Upload to cloud storage first.

**Q: Where to host files temporarily?**
A: Use AWS S3, GitHub raw URLs, or services like file.io.

**Q: Task status stuck at PENDING?**
A: Large files take time. Increase `poll_interval` and `max_poll_attempts`.

**Q: Formula/table recognition not working?**
A: Set `enable_formula=true` and `enable_table=true` in config.

**Q: Chinese text not recognized correctly?**
A: Set `language="ch"` (default) or `"ch,en"` for bilingual.
