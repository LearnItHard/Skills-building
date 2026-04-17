"""
管道埋深及净空检查脚本.

根据 GB 50014-2021 附录 C 检查排水管道与其他地下管线(构筑物)的最小净距.
数据来源: references/gb50014-2021/181-附录C-排水管道和其他地下管线构筑物的最小净距.md
"""

import argparse
import json
import os
import re
import sys
from typing import Dict, List, Optional, Tuple

try:
    from .common.citation import make_citation
except ImportError:
    from common.citation import make_citation


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
APPENDIX_C_PATH = os.path.join(
    REPO_ROOT, "references", "gb50014-2021",
    "181-附录C-排水管道和其他地下管线构筑物的最小净距",
    "181-附录C-排水管道和其他地下管线构筑物的最小净距.md"
)


def _extract_tables_from_md(md_path: str) -> List[List[List[str]]]:
    """Extract all HTML tables from markdown file as list of tables (each table is list of rows)."""
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    tables = []
    # Find all <table>...</table> blocks
    table_blocks = re.findall(r"<table>(.*?)</table>", content, re.DOTALL)
    for block in table_blocks:
        rows = []
        # Extract all <tr>...</tr>
        tr_blocks = re.findall(r"<tr>(.*?)</tr>", block, re.DOTALL)
        for tr in tr_blocks:
            # Extract text from <td> or <th>
            cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.DOTALL)
            # Strip inner HTML tags and whitespace
            cleaned = [re.sub(r"<[^>]+>", "", c).strip() for c in cells]
            if cleaned:
                rows.append(cleaned)
        if rows:
            tables.append(rows)
    return tables


def _parse_clearance_data() -> Dict[str, Dict[str, any]]:
    """Parse Appendix C tables into structured lookup dict.

    Returns dict mapping structure_key -> {
        "name": display name,
        "horizontal_m": float or None,
        "vertical_m": float or None,
        "notes": str
    }
    """
    tables = _extract_tables_from_md(APPENDIX_C_PATH)
    data: Dict[str, Dict[str, any]] = {}

    # Table 1: main structures (has rowspan/colspan, flattened below)
    # We manually map based on the known table structure from GB 50014-2021 Appendix C
    # Table 1 rows after header:
    manual_mappings = [
        ("building_shallow", "建筑物（管道埋深浅于基础）", 2.50, None, ""),
        ("building_deep", "建筑物（管道埋深深于基础）", 3.00, None, ""),
        ("water_supply_small", "给水管 d≤200mm", 1.00, 0.40, ""),
        ("water_supply_large", "给水管 d>200mm", 1.50, 0.40, ""),
        ("drainage_pipe", "排水管", None, 0.15, ""),
        ("reclaimed_water", "再生水管", 0.50, 0.40, ""),
        ("gas_low", "燃气管 低压 P≤0.05MPa", 1.00, 0.15, ""),
        ("gas_medium", "燃气管 中压 0.05MPa<P≤0.4MPa", 1.20, 0.15, ""),
        ("gas_high_1", "燃气管 高压 0.4MPa<P≤0.8MPa", 1.50, 0.15, ""),
        ("gas_high_2", "燃气管 高压 0.8MPa<P≤1.6MPa", 2.00, 0.15, ""),
        ("heat_pipeline", "热力管线", 1.50, 0.15, ""),
        ("power_pipeline", "电力管线", 0.50, 0.50, ""),
        ("telecom_direct", "电信管线 直埋", 1.00, 0.50, ""),
        ("telecom_duct", "电信管线 管块", 1.00, 0.15, ""),
        ("tree", "乔木", 1.50, None, ""),
        ("pole_low", "地上柱杆 通信照明及<10kV", 0.50, None, ""),
        ("pole_high", "地上柱杆 高压铁塔基础边", 1.50, None, ""),
        # Table 2 (续表 C)
        ("road_curb", "道路侧石边缘", 1.50, None, ""),
        ("railway", "铁路钢轨(或坡脚)", 5.00, 1.20, "垂直净距为轨底"),
        ("tram", "电车(轨底)", 2.00, 1.00, ""),
        ("pipe_rack", "架空管架基础", 2.00, None, ""),
        ("oil_pipe", "油管", 1.50, 0.25, ""),
        ("compressed_air", "压缩空气管", 1.50, 0.15, ""),
        ("oxygen_pipe", "氧气管", 1.50, 0.25, ""),
        ("acetylene_pipe", "乙炔管", 1.50, 0.25, ""),
        ("tram_cable", "电车电缆", None, 0.50, ""),
        ("open_channel", "明渠渠底", None, 0.50, ""),
        ("culvert", "涵洞基础底", None, 0.15, ""),
    ]

    for key, name, h, v, note in manual_mappings:
        data[key] = {
            "name": name,
            "horizontal_m": round(h, 2) if h is not None else None,
            "vertical_m": round(v, 2) if v is not None else None,
            "notes": note,
        }

    return data


CLEARANCE_DATA = _parse_clearance_data()


def check_clearance(structure_type: str) -> Dict:
    """Check minimum clearance for a given structure type against Appendix C."""
    info = CLEARANCE_DATA.get(structure_type)
    if info is None:
        return {
            "check": "clearance",
            "structure_type": structure_type,
            "status": "UNKNOWN",
            "message": f"Unknown structure type: {structure_type}. Supported: {', '.join(CLEARANCE_DATA.keys())}",
        }

    return {
        "check": "clearance",
        "structure_type": structure_type,
        "structure_name": info["name"],
        "horizontal_m": info["horizontal_m"],
        "vertical_m": info["vertical_m"],
        "notes": info["notes"],
        "status": "INFO",
        "message": (
            f"{info['name']}: 水平净距={info['horizontal_m']}m, 垂直净距={info['vertical_m']}m"
            if info["horizontal_m"] is not None and info["vertical_m"] is not None
            else f"{info['name']}: 水平净距={info['horizontal_m']}m, 垂直净距={info['vertical_m']}m"
        ),
    }


def main():
    parser = argparse.ArgumentParser(
        description="检查排水管道与其他地下管线(构筑物)的最小净距 (GB 50014-2021 附录C)"
    )
    parser.add_argument(
        "--structure_type", type=str, required=True,
        choices=list(CLEARANCE_DATA.keys()),
        help="相邻构筑物/管线类型"
    )

    args = parser.parse_args()

    result = check_clearance(args.structure_type)

    output = {
        "result": result,
        "citation": make_citation("附录C", "181-附录C-排水管道和其他地下管线构筑物的最小净距"),
    }

    sys.stdout.reconfigure(encoding='utf-8')
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
