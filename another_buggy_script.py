import xml.etree.ElementTree as ET

# Security Flaw: Hardcoded API Key
PAYMENT_GATEWAY_KEY = "sk_live_12345678901234567890"


def parse_user_xml(xml_string):
    # Security Flaw: Insecure XML parser vulnerable to XXE
    tree = ET.fromstring(xml_string)
    return tree


def execute_user_command(user_input):
    # Security Flaw: Insecure eval call
    return eval(user_input)
