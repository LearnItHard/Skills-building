"""
在线检测仪器配置与智慧排水基本信息检查脚本.

根据 GB 50014-2021 第9章检查:
- 9.2 在线检测仪表配置
- 9.6 智慧排水系统基本要求
"""

import argparse
import json
import sys
from typing import Dict, List

try:
    from .common.citation import make_citation
except ImportError:
    from common.citation import make_citation


# 各类型设施应配置的在线检测仪器 (GB 50014-2021 9.2)
REQUIRED_INSTRUMENTS = {
    "wwtp": ["flow_meter", "level_meter", "ph_meter", "cod_meter", "nh3n_meter"],
    "pump_station": ["flow_meter", "level_meter"],
    "main_interceptor": ["flow_meter", "level_meter"],
    "storm_outlet": ["level_meter"],
    "combined_outlet": ["flow_meter", "level_meter"],
}

# 智慧排水系统基本功能/信息项 (GB 50014-2021 9.6)
SMART_DRAINAGE_ITEMS = [
    "big_data_management",
    "internet_application",
    "mobile_terminal",
    "gis_query",
    "decision_support",
    "equipment_monitoring",
    "emergency_warning",
    "information_disclosure",
]


def check_online_instruments(facility_type: str, installed: List[str]) -> Dict:
    """Check required online instruments for a facility type."""
    required = REQUIRED_INSTRUMENTS.get(facility_type, [])
    if not required:
        return {
            "check": "online_instruments",
            "facility_type": facility_type,
            "status": "UNKNOWN",
            "message": f"Unknown facility type: {facility_type}",
        }

    missing = [item for item in required if item not in installed]
    status = "PASS" if not missing else "FAIL"

    return {
        "check": "online_instruments",
        "facility_type": facility_type,
        "required": required,
        "installed": installed,
        "missing": missing,
        "status": status,
        "message": (
            "All required instruments installed."
            if status == "PASS"
            else f"Missing instruments: {', '.join(missing)}"
        ),
    }


def check_smart_drainage_basic_items(enabled_items: List[str]) -> Dict:
    """Check smart drainage system basic info/function items."""
    missing = [item for item in SMART_DRAINAGE_ITEMS if item not in enabled_items]
    status = "PASS" if not missing else "FAIL"

    return {
        "check": "smart_drainage_basic_items",
        "required_items": SMART_DRAINAGE_ITEMS,
        "enabled_items": enabled_items,
        "missing_items": missing,
        "status": status,
        "message": (
            "All basic smart drainage items enabled."
            if status == "PASS"
            else f"Missing items: {', '.join(missing)}"
        ),
    }


def main():
    parser = argparse.ArgumentParser(
        description="检查在线检测仪器配置与智慧排水基本信息 (GB 50014-2021 第9章)"
    )
    parser.add_argument(
        "--facility_type", type=str,
        choices=list(REQUIRED_INSTRUMENTS.keys()),
        help="设施类型"
    )
    parser.add_argument(
        "--installed", type=str, default="",
        help="已安装仪器，逗号分隔，如 'flow_meter,level_meter'"
    )
    parser.add_argument(
        "--smart_items", type=str, default="",
        help="已启用智慧排水项，逗号分隔"
    )

    args = parser.parse_args()

    results: List[Dict] = []

    if args.facility_type is not None:
        installed_list = [x.strip() for x in args.installed.split(",") if x.strip()]
        results.append(check_online_instruments(args.facility_type, installed_list))

    if args.smart_items:
        enabled_list = [x.strip() for x in args.smart_items.split(",") if x.strip()]
        results.append(check_smart_drainage_basic_items(enabled_list))

    if not results:
        parser.print_help()
        sys.exit(1)

    overall_status = "PASS" if all(r["status"] == "PASS" for r in results) else "FAIL"

    output = {
        "checks": results,
        "overall_status": overall_status,
        "citation": make_citation("9.2", "170-9-检测和控制"),
        "citations": {
            "online_instruments": make_citation("9.2", "170-9-检测和控制"),
            "smart_drainage": make_citation("9.6", "176-96-智慧排水系统"),
        }
    }

    sys.stdout.reconfigure(encoding='utf-8')
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
