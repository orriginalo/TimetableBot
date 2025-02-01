import os


files = os.listdir("./data/changes/")
files.sort()
png_files = []
for f in files:
  if f.endswith(".pdf"):
    f = f.replace(".pdf", "").replace("changes_", "")
    print(f)
    for f2 in files:
      if f in f2 and f2.endswith(".png"):
        png_files.append(f2)
    break