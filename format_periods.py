import re
from datetime import datetime

def format_period(raw):
    try:
        return datetime.strptime(raw, "%b-%y").strftime("%B-%Y")
    except:
        return raw

def refactor_constants():
    with open('utils/constants.py', 'r', encoding='utf-8') as f:
        content = f.read()

    def repl(m):
        return f'"{format_period(m.group(1))}"'
        
    content = re.sub(r'"([A-Z][a-z]{2}-\d{2})"', repl, content)
    
    with open('utils/constants.py', 'w', encoding='utf-8') as f:
        f.write(content)

def refactor_cleaning():
    with open('utils/cleaning.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    target = "if 'Month Name' in df.columns:"
    replacement = """if 'Month Name' in df.columns:
        df['Month Name'] = df['Month Name'].apply(lambda x: __import__('datetime').datetime.strptime(x, "%b-%y").strftime("%B-%Y") if isinstance(x, str) and '-' in x else x)
"""
    if "strptime" not in content:
        content = content.replace(target, replacement)
        with open('utils/cleaning.py', 'w', encoding='utf-8') as f:
            f.write(content)

if __name__ == '__main__':
    refactor_constants()
    refactor_cleaning()
    print("Done")
