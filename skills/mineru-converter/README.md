# MinerU Document Converter

A high-quality document conversion tool based on [MinerU API v4](https://mineru.net/), supporting conversion of PDF, Word, PPT, and images to structured Markdown.

## Features

- 📄 **PDF → Markdown** - Supports text and scanned documents OCR
- 📝 **Word/DOCX → Markdown** - Automatically converts to PDF then processes
- 🖼️ **Image → Markdown** - OCR text recognition
- 📊 **Table & Formula Recognition** - Automatic recognition of tables and mathematical formulas
- 📑 **Auto Chapter Splitting** - Splits documents by heading hierarchy
- 🌐 **Chinese & English Support** - Optimized for Chinese document processing

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Dependencies:
- `requests>=2.28.0` - HTTP requests
- `python-docx>=0.8.11` - Word document processing
- `python-dotenv>=1.0.0` - Environment variable management

### 2. Configure API Token

Copy the environment variable example file:

```bash
cp .env.example .env
```

Edit the `.env` file and add your MinerU API Token:

```env
MINERU_API_TOKEN=your_token_here
```

Get Token: https://mineru.net/apiManage

### 3. Convert Documents

```python
from converter import MinerUConverter
from config import MinerUConfig

# Load configuration
config = MinerUConfig.from_env()
converter = MinerUConverter(config)

# Convert local file
chapters = converter.convert(
    "document.pdf",
    output_dir="./output",
    split_chapters=True
)

print(f"Generated {len(chapters)} chapters")
for ch in chapters:
    print(f"- {ch.title}")
```

## Usage Examples

### Convert PDF

```python
from converter import convert_document

chapters = convert_document(
    file_path="paper.pdf",
    api_token="your_token",
    output_dir="./output"
)
```

### Convert Word Document

```python
chapters = converter.convert(
    "report.docx",
    output_dir="./output",
    split_chapters=True
)
```

### Batch Processing

```python
import os

files = ["doc1.pdf", "doc2.docx", "doc3.png"]
for file in files:
    try:
        chapters = converter.convert(file, output_dir=f"./output/{file}")
        print(f"✅ {file}: {len(chapters)} chapters")
    except Exception as e:
        print(f"❌ {file}: {e}")
```

## Output Structure

```
output/
├── index.json                 # Chapter index
├── document_full.md           # Full document
├── 01-Introduction/
│   └── 01-Introduction.md
├── 02-Table-of-Contents/
│   └── 02-Table-of-Contents.md
├── 03-Content/
│   ├── 03-Content.md
│   ├── 03-01-Section-One.md
│   └── 03-02-Section-Two.md
└── ...
```

## Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MINERU_API_TOKEN` | - | **Required** API Token |
| `MINERU_ENABLE_FORMULA` | `true` | Enable formula recognition |
| `MINERU_ENABLE_TABLE` | `true` | Enable table recognition |
| `MINERU_LANGUAGE` | `ch` | Language: `ch`(Chinese), `en`(English), `ch,en` |
| `MINERU_MODEL_VERSION` | `vlm` | Model version |
| `MINERU_POLL_INTERVAL` | `3` | Polling interval (seconds) |
| `MINERU_MAX_POLL_ATTEMPTS` | `100` | Maximum polling attempts |

### Code Configuration

```python
from config import MinerUConfig

config = MinerUConfig(
    api_token="your_token",
    enable_formula=True,
    enable_table=True,
    language="ch,en",
    model_version="vlm"
)
```

## API Limitations

- Maximum 2000 pages/day (high priority)
- Single file max: 200MB, 600 pages
- Supported formats: PDF, DOC, DOCX, PPT, PPTX, PNG, JPG, JPEG

## FAQ

**Q: Invalid Token error?**  
A: Check if the Token is correct, not expired, or contains extra spaces.

**Q: Conversion timeout?**  
A: Large files take longer. Increase `MINERU_MAX_POLL_ATTEMPTS` value.

**Q: Chinese recognition inaccurate?**  
A: Set `MINERU_LANGUAGE=ch` to ensure Chinese model is used.

**Q: How to convert without splitting chapters?**  
A: Set `split_chapters=False` to output only the full document.

## Project Structure

```
mineru-converter/
├── converter.py          # Core converter
├── config.py             # Configuration management
├── chapter_splitter.py   # Chapter splitting
├── docx_to_pdf.py        # DOCX to PDF conversion
├── requirements.txt      # Dependencies
├── .env.example          # Environment variables example
└── test_converter.py     # Test script
```

## License

MIT License

## Related Links

- [MinerU Official](https://mineru.net/)
- [API Documentation](https://mineru.net/apiDocs)
- [GitHub Repository](https://github.com/LearnItHard/Skills-building)
