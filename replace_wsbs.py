import os
import glob

def refactor():
    files = [f for f in glob.glob('**/*.py', recursive=True) if 'venv' not in f and '.gemini' not in f]
    for f in files:
        try:
            with open(f, 'r', encoding='utf-8') as file:
                content = file.read()
        except UnicodeDecodeError:
            with open(f, 'r', encoding='utf-16') as file:
                content = file.read()
        
        new_content = content.replace('"MP"', '"MP"')
        new_content = new_content.replace('"PB"', '"PB"')
        new_content = new_content.replace("'MP'", "'MP'")
        new_content = new_content.replace("'PB'", "'PB'")
        
        if new_content != content:
            with open(f, 'w', encoding='utf-8') as file:
                file.write(new_content)
            print(f"Updated {f}")

if __name__ == '__main__':
    refactor()
