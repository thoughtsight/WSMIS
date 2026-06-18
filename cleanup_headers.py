import glob, re

for f in glob.glob('d:/RKM-INDORE/Reports/WSMIS/views/*.py'):
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    original = content
    # Remove PageHeader calls
    # PageHeader("Title", icon="👤", ...)
    content = re.sub(r'PageHeader\s*\([^)]*\)', '', content)
    content = re.sub(r'from ui\.components import .*PageHeader.*', 'from ui.components import KPIGrid, ChartCard, TableCard', content)
    content = re.sub(r'from ui\.components import .*KPIGrid.*', 'from ui.components import KPIGrid, ChartCard, TableCard', content)
    
    # Clean up duplicate imports
    content = content.replace('from ui.components import KPIGrid, ChartCard, TableCard\nfrom ui.components import KPIGrid, ChartCard, TableCard', 'from ui.components import KPIGrid, ChartCard, TableCard')
    
    # Remove old brand-title and section-title that were used as headers at the top
    content = re.sub(r'st\.markdown\s*\(\s*\'<div class="brand-title".*?\)\s*', '', content, flags=re.DOTALL)
    
    # Also some pages used <div class="section-title"> as a fake header instead of PageHeader, e.g. system_health.py
    # But only if it's the first thing. We'll leave section-titles alone for now and see if any remain.
    # Actually, we should just check the files to make sure there are no other duplicate headers.
    
    if content != original:
        with open(f, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f'Cleaned up headers in {f}')
