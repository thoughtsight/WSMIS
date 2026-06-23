import os

repo_dir = r"d:\RKM-INDORE\Reports\WSMIS"
views_dir = os.path.join(repo_dir, "views")

# Prefixes of lines to strip out
strip_prefixes = (
    "import streamlit", "import pandas", "import numpy", 
    "import plotly", "import json", "from io", "from datetime",
    "from services.financial_service", "from services.audit_service",
    "from utils.calculations.", "from utils.aggregations", 
    "from utils.filters", "from utils.constants", 
    "from ui.formatters", "from ui.components", "from ui.tables",
    "from ui.helpers", "from ui.export_buttons",
    "from views.components.chart_engine", "from views.components.kpi_engine",
    "from views.shared", "from views.dashboard_common"
)

def rewrite():
    for f in os.listdir(views_dir):
        if not f.endswith(".py") or f in ["shared.py", "__init__.py"]:
            continue
            
        path = os.path.join(views_dir, f)
        with open(path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            
        new_lines = [
            "from views.shared import *\n",
            "from views.components.kpi_engine import KPIEngine\n",
            "from views.components.chart_engine import ChartEngine\n",
            "\n"
        ]
        
        in_multiline = False
        
        for line in lines:
            stripped = line.strip()
            
            # Start of a multiline import?
            if any(stripped.startswith(p) for p in strip_prefixes):
                if "(" in stripped and ")" not in stripped:
                    in_multiline = True
                continue
                
            if in_multiline:
                if ")" in stripped:
                    in_multiline = False
                continue
                
            # If it's an empty line right after we skipped imports, we can skip it to avoid huge gaps
            # But let's just keep it simple
            
            new_lines.append(line)
            
        with open(path, 'w', encoding='utf-8') as file:
            file.writelines(new_lines)
        print(f"Rewrote imports for {f}")

if __name__ == "__main__":
    rewrite()
