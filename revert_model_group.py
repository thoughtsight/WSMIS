import re
import glob
from datetime import datetime

def format_period(raw):
    try:
        # If it's like 'January-2024', convert to 'Jan-2024'
        if len(raw.split('-')[0]) > 3:
            return datetime.strptime(raw, "%B-%Y").strftime("%b-%Y")
        return raw
    except:
        return raw

def refactor():
    files = [f for f in glob.glob('**/*.py', recursive=True) if 'venv' not in f and '.gemini' not in f]
    for f in files:
        try:
            with open(f, 'r', encoding='utf-8') as file:
                content = file.read()
        except UnicodeDecodeError:
            with open(f, 'r', encoding='utf-16') as file:
                content = file.read()
        
        new_content = content
        
        # Revert Location Group to Location Group
        new_content = new_content.replace('Location Group', 'Location Group')
        new_content = new_content.replace('filter_loc_group', 'filter_loc_group')
        new_content = new_content.replace('"Other"', '"Other"')
        
        if f.endswith('constants.py'):
            def repl(m):
                return f'"{format_period(m.group(1))}"'
            new_content = re.sub(r'"([A-Z][a-z]+-\d{4})"', repl, new_content)
            
        if f.endswith('cleaning.py'):
            new_content = new_content.replace('strftime("%B-%Y")', 'strftime("%b-%Y")')

        if new_content != content:
            with open(f, 'w', encoding='utf-8') as file:
                file.write(new_content)
            print(f"Updated {f}")

if __name__ == '__main__':
    refactor()
