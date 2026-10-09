"""Module for secure XML parsing and user command evaluation."""

import ast
import os
from typing import Any

import defusedxml.ElementTree as ET

# Fetch secrets securely from environment variables
PAYMENT_GATEWAY_KEY = os.environ.get("PAYMENT_GATEWAY_KEY", "")


def parse_user_xml(xml_string: str) -> ET.Element:
    """Parse XML string safely using defusedxml to prevent XXE attacks."""
    return ET.fromstring(xml_string)


def execute_user_command(user_input: str) -> Any:
    """Safely evaluate literal Python expressions using ast.literal_eval."""
    try:
        return ast.literal_eval(user_input)
    except (ValueError, SyntaxError) as err:
        raise ValueError("Invalid or unsafe literal command provided.") from err
