import os
import sys

import yaml


# CODE QUALITY ISSUE: Mutable default argument (list)
def add_user_to_group(username, group_list=[]):
    group_list.append(username)
    return group_list


# SECURITY ISSUE: Unsafe YAML loading
def parse_config(yaml_string):
    config = yaml.unsafe_load(yaml_string)
    return config


# LOGIC ISSUE: Broad Exception silencing
def read_file(filepath):
    try:
        with open(filepath, "r") as f:
            return f.read()
    except Exception:
        pass
