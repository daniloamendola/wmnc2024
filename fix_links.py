from pathlib import Path

p = Path(r'C:\myworkspace\repos\wmnc2024\www.unive.it\web\en\6439\home.html')
html = p.read_text(encoding='utf-8')

count = html.count('href="../../../')
html = html.replace('href="../../../', 'href="https://www.unive.it/')
p.write_text(html, encoding='utf-8')
print(f'Sostituiti {count} link')
