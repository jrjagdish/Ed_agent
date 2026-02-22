import os
import re

def sanitize_public_id(filename: str) -> str:
    name, _ = os.path.splitext(filename)
    name = name.lower()
    name = re.sub(r'[^a-z0-9_-]', '_', name)  # replace invalid chars
    return name