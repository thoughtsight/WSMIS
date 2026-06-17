import os
import re

app_path = "d:/RKM-INDORE/Reports/WSMIS/app.py"
with open(app_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace prints with logger.info
content = re.sub(r'print\((.*?)\)', r'logger.info(\1)', content)

# Inject error handler and logger imports
imports = """from services.logger import logger
from services.error_handler import safe_render
"""
content = content.replace("from ui.formatters import *", imports + "from ui.formatters import *")

# Replace render(...) with safe_render(render, ...)
content = re.sub(r'from pages\.([a-zA-Z0-9_]+) import render; render\((.*?)\)', r'from pages.\1 import render; safe_render(render, \2)', content)

with open(app_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Applied safe_render and logger to app.py")
