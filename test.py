import os
from datetime import datetime

files = os.listdir("./data/changes/")
pdf_files = []

# Собираем все PDF файлы и парсим даты
for f in files:
    if f.startswith("changes_") and f.endswith(".pdf"):
        date_str = f.replace("changes_", "").replace(".pdf", "")
        try:
            date = datetime.strptime(date_str, "%d.%m.%y")
            pdf_files.append((date, f))
        except ValueError:
            continue

# Сортируем PDF файлы по дате в убывающем порядке
pdf_files.sort(reverse=True, key=lambda x: x[0])

if pdf_files:
    latest_date = pdf_files[0][0].strftime("%d.%m.%y")
    print(f"Last date file: {latest_date}")
    
    # Ищем соответствующие PNG файлы
    png_files = [f for f in files 
                if f.startswith(latest_date) and f.endswith(".png")]
    
    print("PNG files:")
    for png in sorted(png_files):
        print(png)
else:
    print("No PDF files found")
    
