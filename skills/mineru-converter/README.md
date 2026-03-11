# MinerU Document Converter

基于 [MinerU API v4](https://mineru.net/) 的高质量文档转换工具，支持 PDF、Word、PPT 和图片转换为结构化 Markdown。

## 功能特性

- 📄 **PDF → Markdown** - 支持文本、扫描件 OCR
- 📝 **Word/DOCX → Markdown** - 自动转换为 PDF 后处理
- 🖼️ **图片 → Markdown** - OCR 文字识别
- 📊 **表格公式识别** - 自动识别表格和数学公式
- 📑 **章节自动分割** - 按标题层级拆分文档
- 🌐 **中英文支持** - 优化中文文档处理

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

依赖：
- `requests>=2.28.0` - HTTP 请求
- `python-docx>=0.8.11` - Word 文档处理
- `python-dotenv>=1.0.0` - 环境变量管理

### 2. 配置 API Token

复制环境变量示例文件：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的 MinerU API Token：

```env
MINERU_API_TOKEN=your_token_here
```

获取 Token：https://mineru.net/apiManage

### 3. 转换文档

```python
from converter import MinerUConverter
from config import MinerUConfig

# 加载配置
config = MinerUConfig.from_env()
converter = MinerUConverter(config)

# 转换本地文件
chapters = converter.convert(
    "document.pdf",
    output_dir="./output",
    split_chapters=True
)

print(f"生成 {len(chapters)} 个章节")
for ch in chapters:
    print(f"- {ch.title}")
```

## 使用示例

### 转换 PDF

```python
from converter import convert_document

chapters = convert_document(
    file_path="论文.pdf",
    api_token="your_token",
    output_dir="./output"
)
```

### 转换 Word 文档

```python
chapters = converter.convert(
    "报告.docx",
    output_dir="./output",
    split_chapters=True
)
```

### 批量处理

```python
import os

files = ["doc1.pdf", "doc2.docx", "doc3.png"]
for file in files:
    try:
        chapters = converter.convert(file, output_dir=f"./output/{file}")
        print(f"✅ {file}: {len(chapters)} 章节")
    except Exception as e:
        print(f"❌ {file}: {e}")
```

## 输出结构

```
output/
├── index.json                 # 章节索引
├── document_full.md           # 完整文档
├── 01-前言/
│   └── 01-前言.md
├── 02-目录/
│   └── 02-目录.md
├── 03-正文/
│   ├── 03-正文.md
│   ├── 03-01-第一节.md
│   └── 03-02-第二节.md
└── ...
```

## 配置选项

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `MINERU_API_TOKEN` | - | **必需** API Token |
| `MINERU_ENABLE_FORMULA` | `true` | 启用公式识别 |
| `MINERU_ENABLE_TABLE` | `true` | 启用表格识别 |
| `MINERU_LANGUAGE` | `ch` | 语言：`ch`(中文), `en`(英文), `ch,en` |
| `MINERU_MODEL_VERSION` | `vlm` | 模型版本 |
| `MINERU_POLL_INTERVAL` | `3` | 轮询间隔（秒）|
| `MINERU_MAX_POLL_ATTEMPTS` | `100` | 最大轮询次数 |

### 代码配置

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

## API 限制

- 每日最高 2000 页（高优先级）
- 单文件最大 200MB，600 页
- 支持格式：PDF, DOC, DOCX, PPT, PPTX, PNG, JPG, JPEG

## 常见问题

**Q: Token 无效报错？**  
A: 检查 Token 是否正确，是否已过期，或是否包含多余空格。

**Q: 转换超时？**  
A: 大文件需要更长时间，增加 `MINERU_MAX_POLL_ATTEMPTS` 值。

**Q: 中文识别不准确？**  
A: 设置 `MINERU_LANGUAGE=ch`，确保使用中文模型。

**Q: 如何仅转换不分割章节？**  
A: 设置 `split_chapters=False`，只输出完整文档。

## 项目结构

```
mineru-converter/
├── converter.py          # 核心转换器
├── config.py             # 配置管理
├── chapter_splitter.py   # 章节分割
├── docx_to_pdf.py        # DOCX 转 PDF
├── requirements.txt      # 依赖列表
├── .env.example          # 环境变量示例
└── test_converter.py     # 测试脚本
```

## 许可证

MIT License

## 相关链接

- [MinerU 官网](https://mineru.net/)
- [API 文档](https://mineru.net/apiDocs)
- [GitHub 仓库](https://github.com/LearnItHard/Skills-building)
