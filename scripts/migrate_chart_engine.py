import os
import re

repo_dir = r"d:\RKM-INDORE\Reports\WSMIS"

def fix_imports_and_usage():
    for root, _, files in os.walk(repo_dir):
        if "venv" in root or ".git" in root or "__pycache__" in root:
            continue
        for file in files:
            if not file.endswith(".py"):
                continue
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            new_content = content
            
            # Remove apply_chart from ui.helpers import
            new_content = re.sub(r"from ui\.helpers import(.*?)\bapply_chart\b,?\s*(.*)", r"from ui.helpers import\1\2\nfrom views.components.chart_engine import ChartEngine", new_content)
            
            # Clean up empty imports like "from ui.helpers import "
            new_content = new_content.replace("from ui.helpers import \n", "\n")
            new_content = new_content.replace("from ui.helpers import  \n", "\n")

            # Replace direct ChartEngine.apply_chart( calls with ChartEngine.ChartEngine.apply_chart(
            if file != "chart_engine.py":
                new_content = re.sub(r"\bapply_chart\(", "ChartEngine.ChartEngine.apply_chart(", new_content)

            # Fix ui.components.charts import if any
            new_content = re.sub(r"from ui\.components\.charts import(.*?)\bapply_chart\b,?\s*(.*)", r"from ui.components.charts import\1\2\nfrom views.components.chart_engine import ChartEngine", new_content)

            if file == "discount.py" and "ChartEngine.apply_chart" in new_content and "from views.components.chart_engine import ChartEngine" not in new_content:
                new_content = "from views.components.chart_engine import ChartEngine\n" + new_content

            if file == "helpers.py" and "ChartEngine.apply_chart" in new_content and "from views.components.chart_engine import ChartEngine" not in new_content:
                new_content = "from views.components.chart_engine import ChartEngine\n" + new_content

            if file == "charts.py" and "ui\\components" in root:
                if "ChartEngine.apply_chart" in new_content and "from views.components.chart_engine import ChartEngine" not in new_content:
                    new_content = "from views.components.chart_engine import ChartEngine\n" + new_content

            if new_content != content:
                # clean up trailing commas from regex replace
                new_content = new_content.replace("from ui.helpers import ", "from ui.helpers import ")
                new_content = new_content.replace("import clean_hover", "import clean_hover")
                new_content = new_content.replace("import clean_hover,", "import clean_hover,")
                new_content = new_content.replace("from ui.helpers import \nfrom", "from")

                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Updated {filepath}")

if __name__ == "__main__":
    fix_imports_and_usage()
