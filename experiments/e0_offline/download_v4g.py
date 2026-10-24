"""Per-file download of a large Kaggle dataset (the whole-dataset zip endpoint returns 404 for it). Lists all files with pagination via the
kaggle API, then downloads each file that is not present yet. Usage: python download_v4g.py <owner/slug> <out_dir>"""
import os, sys, time, subprocess
from kaggle import api
slug, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
files, token = [], None
while True:
    r = api.dataset_list_files(slug, page_token=token, page_size=200) if token else api.dataset_list_files(slug, page_size=200)
    files += [(f.name, getattr(f, "total_bytes", None) or getattr(f, "totalBytes", 0)) for f in r.files]
    token = getattr(r, "next_page_token", None) or getattr(r, "nextPageToken", None)
    if not token: break
print(f"{len(files)} files, {sum(int(s or 0) for _, s in files)/1e9:.2f} GB", flush=True)
done = 0
for name, size in files:
    dest = os.path.join(out, name)
    if os.path.exists(dest) and os.path.getsize(dest) == int(size or 0): done += 1; continue
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    for attempt in range(3):
        rc = subprocess.run([sys.executable, "-m", "kaggle.cli", "datasets", "download", "-d", slug, "-f", name, "-p", os.path.dirname(dest), "--quiet"], capture_output=True, text=True).returncode
        z = dest + ".zip"
        if os.path.exists(z):
            import zipfile; zipfile.ZipFile(z).extractall(os.path.dirname(dest)); os.remove(z)
        if os.path.exists(dest): break
        time.sleep(3)
    done += 1
    if done % 10 == 0: print(f"  {done}/{len(files)} {time.strftime('%H:%M:%S')}", flush=True)
print("DOWNLOAD_V4G_DONE", done, len(files), time.strftime("%H:%M:%S"), flush=True)
