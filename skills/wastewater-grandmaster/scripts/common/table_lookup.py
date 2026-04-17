"""
Table lookup functions for GB 50014-2021 parameters.

This module provides lookup functions for standard values from the Chinese
national standard GB 50014-2021 (室外排水设计标准):
- Roughness coefficients for different pipe materials
- Maximum design fullness for different pipe diameters
- Minimum design velocities for different pipe categories
"""

from typing import Literal, Dict, Optional


# Roughness coefficients (n) from GB 50014-2021 Table 5.2.3
ROUGHNESS_COEFFICIENTS: Dict[str, float] = {
    # Metal pipes
    "concrete": 0.013,           # Concrete pipe, reinforced concrete pipe
    "reinforced_concrete": 0.013,
    "cement_mortar_lined_ductile_iron": 0.011,  # Cement mortar lined ductile iron pipe
    "asbestos_cement": 0.012,    # Asbestos cement pipe
    "steel": 0.012,              # Steel pipe
    
    # Plastic pipes
    "upvc": 0.010,               # UPVC pipe
    "pe": 0.010,                 # PE pipe
    "frp": 0.010,                # Glass fiber reinforced plastic pipe
    "plastic": 0.010,            # Generic plastic
    
    # Other materials
    "cement_mortar_lined_channel": 0.013,  # Cement mortar lined channel
    "dry_stone": 0.022,          # Dry stone channel (middle of 0.020-0.025)
    "wet_stone": 0.017,          # Wet stone channel
    "brick": 0.015,              # Brick channel
    "soil": 0.027,               # Soil channel (middle of 0.025-0.030)
    "grass": 0.025,              # Grass lined channel
}

# Maximum design fullness from GB 50014-2021 Table 5.2.4
MAX_FULLNESS_RULES = [
    (300, 0.55),    # 200-300mm -> 0.55
    (450, 0.65),    # 350-450mm -> 0.65
    (900, 0.70),    # 500-900mm -> 0.70
    (float('inf'), 0.75),  # >=1000mm -> 0.75
]

# Minimum design velocities from GB 50014-2021 Section 5.2.7
MIN_VELOCITIES: Dict[str, float] = {
    "sewage": 0.6,           # 污水管道
    "storm": 0.75,          # 雨水管道 (not used in this task)
    "combined": 0.75,       # 合流管道 (not used in this task)
    "storm_combined": 0.75,  # 雨水和合流管道
    "open_channel": 0.4,    # 明渠
    "pressure_sludge": 0.9,  # 压力污泥管道
}

# Mapping of common material names to roughness keys
MATERIAL_ALIASES: Dict[str, str] = {
    "钢筋混凝土管": "reinforced_concrete",
    "混凝土管": "concrete",
    "水泥砂浆抹面渠道": "cement_mortar_lined_channel",
    "球墨铸铁管": "cement_mortar_lined_ductile_iron",
    "石棉水泥管": "asbestos_cement",
    "钢管": "steel",
    "UPVC管": "upvc",
    "PE管": "pe",
    "塑料管": "plastic",
    "玻璃钢管": "frp",
    "PVC": "upvc",
}


def roughness_coefficient(material: str) -> float:
    """
    Get the roughness coefficient (Manning's n) for a given pipe material.
    
    Args:
        material: Pipe material name (supports English keys and Chinese aliases)
        
    Returns:
        Roughness coefficient value
        
    Raises:
        ValueError: If material is not recognized
        
    Example:
        >>> roughness_coefficient("concrete")
        0.013
        >>> roughness_coefficient("钢筋混凝土管")
        0.013
        >>> roughness_coefficient("plastic")
        0.010
    """
    # First try direct match
    material_lower = material.lower().strip()
    
    if material_lower in ROUGHNESS_COEFFICIENTS:
        return ROUGHNESS_COEFFICIENTS[material_lower]
    
    # Try Chinese aliases
    if material in MATERIAL_ALIASES:
        key = MATERIAL_ALIASES[material]
        return ROUGHNESS_COEFFICIENTS[key]
    
    # Try partial matching for common terms
    for key in ROUGHNESS_COEFFICIENTS:
        if key in material_lower or material_lower in key:
            return ROUGHNESS_COEFFICIENTS[key]
    
    raise ValueError(
        f"Unknown material: '{material}'. "
        f"Supported materials: {list(ROUGHNESS_COEFFICIENTS.keys())}"
    )


def max_fullness(diameter_mm: float) -> float:
    """
    Get the maximum design fullness for a given pipe diameter.
    
    From GB 50014-2021 Table 5.2.4:
    - 200~300mm -> 0.55
    - 350~450mm -> 0.65
    - 500~900mm -> 0.70
    - >=1000mm -> 0.75
    
    Args:
        diameter_mm: Pipe diameter in millimeters
        
    Returns:
        Maximum design fullness ratio (0-1)
        
    Raises:
        ValueError: If diameter is not positive
        
    Example:
        >>> max_fullness(200)
        0.55
        >>> max_fullness(400)
        0.65
        >>> max_fullness(600)
        0.70
        >>> max_fullness(1000)
        0.75
        >>> max_fullness(1500)
        0.75
    """
    if diameter_mm <= 0:
        raise ValueError("Diameter must be positive")
    
    for max_d, fullness in MAX_FULLNESS_RULES:
        if diameter_mm <= max_d:
            return fullness
    
    return 0.75  # Should not reach here with the inf in the list


def min_velocity(pipe_category: Literal["sewage", "storm_combined", "pressure_sludge"]) -> float:
    """
    Get the minimum design velocity for a given pipe category.
    
    From GB 50014-2021 Section 5.2.7:
    - sewage: 0.6 m/s (污水管道)
    - storm_combined: 0.75 m/s (雨水管道和合流管道满流时)
    - pressure_sludge: 0.9 m/s (压力污泥管道)
    
    Args:
        pipe_category: Category of pipe - must be exactly "sewage", "storm_combined", or "pressure_sludge"
        
    Returns:
        Minimum design velocity in m/s
        
    Raises:
        ValueError: If pipe_category is not recognized
        
    Example:
        >>> min_velocity("sewage")
        0.6
        >>> min_velocity("storm_combined")
        0.75
        >>> min_velocity("pressure_sludge")
        0.9
    """
    if pipe_category not in MIN_VELOCITIES:
        raise ValueError(
            f"Unknown pipe_category: '{pipe_category}'. "
            f"Expected one of: sewage, storm_combined, pressure_sludge"
        )
    
    return MIN_VELOCITIES[pipe_category]


def get_all_roughness_values() -> Dict[str, float]:
    """Return all available roughness coefficients."""
    return ROUGHNESS_COEFFICIENTS.copy()


def get_all_min_velocities() -> Dict[str, float]:
    """Return all available minimum velocities."""
    return MIN_VELOCITIES.copy()