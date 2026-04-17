"""
Unit conversion functions for wastewater hydraulic calculations.

These functions convert between common units used in wastewater engineering:
- Flow rates: L/s, m³/s, m³/d
- Lengths: mm, m
- Areas: hm², m²
"""

import math
from typing import Union


def Lps_to_m3ps(lps: float) -> float:
    """
    Convert liters per second to cubic meters per second.
    
    Args:
        lps: Flow rate in liters per second (L/s)
        
    Returns:
        Flow rate in cubic meters per second (m³/s)
        
    Example:
        >>> Lps_to_m3ps(100)
        0.1
    """
    return lps / 1000.0


def m3pd_to_m3ps(m3pd: float) -> float:
    """
    Convert cubic meters per day to cubic meters per second.
    
    Args:
        m3pd: Flow rate in cubic meters per day (m³/d)
        
    Returns:
        Flow rate in cubic meters per second (m³/s)
        
    Example:
        >>> m3pd_to_m3ps(86400)  # 1 m³/d = 1/86400 m³/s
        0.001
    """
    return m3pd / 86400.0


def mm_to_m(mm: float) -> float:
    """
    Convert millimeters to meters.
    
    Args:
        mm: Length in millimeters (mm)
        
    Returns:
        Length in meters (m)
        
    Example:
        >>> mm_to_m(1000)
        1.0
    """
    return mm / 1000.0


def hm2_to_m2(hm2: float) -> float:
    """
    Convert hectares to square meters.
    
    Args:
        hm2: Area in hectares (hm²)
        
    Returns:
        Area in square meters (m²)
        
    Example:
        >>> hm2_to_m2(1)
        10000.0
    """
    return hm2 * 10000.0


def m2_to_hm2(m2: float) -> float:
    """
    Convert square meters to hectares.
    
    Args:
        m2: Area in square meters (m²)
        
    Returns:
        Area in hectares (hm²)
        
    Example:
        >>> m2_to_hm2(10000)
        1.0
    """
    return m2 / 10000.0


def m3ps_to_Lps(m3ps: float) -> float:
    """
    Convert cubic meters per second to liters per second.
    
    Args:
        m3ps: Flow rate in cubic meters per second (m³/s)
        
    Returns:
        Flow rate in liters per second (L/s)
        
    Example:
        >>> m3ps_to_Lps(0.1)
        100.0
    """
    return m3ps * 1000.0


def m3ps_to_m3pd(m3ps: float) -> float:
    """
    Convert cubic meters per second to cubic meters per day.
    
    Args:
        m3ps: Flow rate in cubic meters per second (m³/s)
        
    Returns:
        Flow rate in cubic meters per day (m³/d)
        
    Example:
        >>> m3ps_to_m3pd(0.001)  # 0.001 m³/s = 86.4 m³/d
        86.4
    """
    return m3ps * 86400.0


def m_to_mm(m: float) -> float:
    """
    Convert meters to millimeters.
    
    Args:
        m: Length in meters (m)
        
    Returns:
        Length in millimeters (mm)
        
    Example:
        >>> m_to_mm(1.0)
        1000.0
    """
    return m * 1000.0