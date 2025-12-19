import xml.etree.ElementTree as ET
from typing import List, Dict, Tuple, Optional


class XMLParseError(Exception):
    """Exception raised when XML parsing fails."""
    pass


class BoundsParseError(Exception):
    """Exception raised when bounds parsing fails."""
    pass


def _parse_bounds(bounds_str: str) -> Tuple[int, int, int, int]:
    """
    Parses Android bounds string into coordinates.
    
    Args:
        bounds_str: Bounds string in format "[x1,y1][x2,y2]"
        
    Returns:
        Tuple of (x1, y1, x2, y2)
        
    Raises:
        BoundsParseError: If bounds string cannot be parsed
    """
    try:
        # Extract coordinates: "[140,200][400,350]" -> ["140", "200", "400", "350"]
        coords_str = bounds_str.replace("][", ",").replace("[", "").replace("]", "")
        coords = coords_str.split(",")
        
        if len(coords) != 4:
            raise BoundsParseError(f"Expected 4 coordinates, got {len(coords)}")
        
        x1, y1, x2, y2 = map(int, coords)
        return x1, y1, x2, y2
        
    except (ValueError, AttributeError) as e:
        raise BoundsParseError(f"Failed to parse bounds '{bounds_str}': {str(e)}") from e


def _is_valid_bounds(x1: int, y1: int, x2: int, y2: int) -> bool:
    """
    Checks if bounds are valid (non-zero area).
    
    Args:
        x1, y1, x2, y2: Bounds coordinates
        
    Returns:
        True if bounds have valid area
    """
    width = x2 - x1
    height = y2 - y1
    return width > 0 and height > 0


def _is_interactive_element(node: ET.Element) -> bool:
    """
    Checks if an XML node represents an interactive element.
    
    Args:
        node: XML element node
        
    Returns:
        True if element is interactive or has meaningful content
    """
    is_clickable = node.attrib.get("clickable") == "true"
    is_editable = (
        node.attrib.get("focus") == "true" or 
        node.attrib.get("focusable") == "true"
    )
    has_text = bool(node.attrib.get("text", ""))
    has_desc = bool(node.attrib.get("content-desc", ""))
    
    return is_clickable or is_editable or has_text or has_desc


def _extract_element_data(node: ET.Element) -> Optional[Dict]:
    """
    Extracts element data from an XML node.
    
    Args:
        node: XML element node
        
    Returns:
        Dictionary with element data, or None if extraction fails
    """
    bounds = node.attrib.get("bounds")
    if not bounds:
        return None
    
    try:
        x1, y1, x2, y2 = _parse_bounds(bounds)
    except BoundsParseError:
        return None
    
    # Filter out invalid bounds (zero area)
    if not _is_valid_bounds(x1, y1, x2, y2):
        return None
    
    center_x = (x1 + x2) // 2
    center_y = (y1 + y2) // 2
    
    # Extract all relevant fields
    text = node.attrib.get("text", "")
    content_desc = node.attrib.get("content-desc", "")
    resource_id = node.attrib.get("resource-id", "")
    class_name = node.attrib.get("class", "")
    element_type = class_name.split(".")[-1] if class_name else ""
    package = node.attrib.get("package", "")
    hint = node.attrib.get("hint", "")
    
    # Interaction state
    is_clickable = node.attrib.get("clickable") == "true"
    is_long_clickable = node.attrib.get("long-clickable") == "true"
    is_focusable = node.attrib.get("focusable") == "true"
    is_focused = node.attrib.get("focused") == "true"
    is_enabled = node.attrib.get("enabled", "true") == "true"
    is_scrollable = node.attrib.get("scrollable") == "true"
    is_checkable = node.attrib.get("checkable") == "true"
    is_checked = node.attrib.get("checked") == "true"
    is_password = node.attrib.get("password") == "true"
    is_selected = node.attrib.get("selected") == "true"
    
    # Build element data with all relevant fields
    element_data = {
        "id": resource_id,
        "text": text,
        "content-desc": content_desc,
        "type": element_type,
        "bounds": bounds,
        "center": [center_x, center_y],  # Use list for JSON serialization
        "clickable": is_clickable,
        "enabled": is_enabled,
    }
    
    # Add package name if available
    if package:
        element_data["package"] = package
    
    # Add interaction hints
    if is_focusable:
        element_data["focusable"] = True
        if is_focused:
            element_data["focused"] = True
    if is_long_clickable:
        element_data["long-clickable"] = True
    if is_scrollable:
        element_data["scrollable"] = True
    if is_checkable:
        element_data["checkable"] = True
        if is_checked:
            element_data["checked"] = True
    if is_password:
        element_data["password"] = True
    if is_selected:
        element_data["selected"] = True
    if hint:
        element_data["hint"] = hint
    
    # Determine primary action
    if is_clickable:
        element_data["action"] = "tap"
    elif is_focusable:
        element_data["action"] = "focus"
    else:
        element_data["action"] = "read"
    
    return element_data


def get_interactive_elements(xml_content: str) -> List[Dict]:
    """
    Parses Android Accessibility XML and returns a lean list of interactive elements.
    Calculates center coordinates (x, y) for every clickable element.
    
    Args:
        xml_content: XML string from Android accessibility tree
        
    Returns:
        List of dictionaries containing element information
        
    Raises:
        XMLParseError: If XML content cannot be parsed
    """
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        error_msg = "Error parsing XML. The screen might be loading."
        print(f"⚠️ {error_msg}")
        raise XMLParseError(error_msg) from e

    elements = []
    
    # Recursively find all nodes
    for node in root.iter():
        # Skip non-interactive elements
        if not _is_interactive_element(node):
            continue
        
        # Extract element data
        element_data = _extract_element_data(node)
        if element_data:
            elements.append(element_data)

    return elements