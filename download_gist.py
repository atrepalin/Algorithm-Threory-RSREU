import argparse
import os
import re
import sys
from urllib.parse import urlparse
import requests

GITHUB_API = "https://api.github.com/gists/{}"

def extract_gist_id(url_or_id: str) -> str:
    if re.fullmatch(r"[0-9a-fA-F]+", url_or_id):
        return url_or_id

    try:
        p = urlparse(url_or_id)
        if not p.scheme:
            url_or_id = "https://" + url_or_id
            p = urlparse(url_or_id)
        path = p.path.strip("/")
        parts = path.split("/")
        if parts:
            candidate = parts[-1]
            if re.fullmatch(r"[0-9a-fA-F]+", candidate):
                return candidate
        raise ValueError("Не удалось извлечь id из URL.")
    except Exception as e:
        raise ValueError(f"Неверный URL/ID: {e}")

def fetch_gist_metadata(gist_id: str, token: str = None) -> dict:
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"
    url = GITHUB_API.format(gist_id)
    r = requests.get(url, headers=headers, timeout=15)
    if r.status_code == 404:
        raise RuntimeError("Gist не найден (404). Проверьте id/URL и доступность гиста.")
    if r.status_code == 403:
        raise RuntimeError(f"Доступ запрещён или превышен лимит: {r.status_code} {r.text}")
    r.raise_for_status()
    return r.json()

def download_file(raw_url: str, dest_path: str, token: str = None):
    headers = {}
    if token:
        headers["Authorization"] = f"token {token}"
    with requests.get(raw_url, headers=headers, stream=True, timeout=30) as r:
        r.raise_for_status()
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        with open(dest_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

def sanitize_filename(name: str) -> str:
    return name.replace("/", "_").replace("\\", "_")

def main():
    p = argparse.ArgumentParser(description="Скачать все файлы из Gist (по URL или ID).")
    p.add_argument("gist", help="URL или ID Gist-а")
    p.add_argument("--out-dir", "-o", default=None, help="Папка для сохранения (по умолчанию: gist_<id>)")
    p.add_argument("--token", "-t", default=None, help="GitHub token (optional)")
    args = p.parse_args()

    try:
        gist_id = extract_gist_id(args.gist)
    except ValueError as e:
        print("Ошибка:", e, file=sys.stderr)
        sys.exit(2)

    try:
        meta = fetch_gist_metadata(gist_id, token=args.token)
    except Exception as e:
        print("Не удалось получить метаданные gist:", e, file=sys.stderr)
        sys.exit(3)

    owner = meta.get("owner", {}).get("login") or "anonymous"
    description = meta.get("description") or ""
    files = meta.get("files", {})
    if not files:
        print("В Gist нет файлов.", file=sys.stderr)
        sys.exit(4)

    out_dir = args.out_dir or f"gist_{gist_id}"
    safe_dir = f"{out_dir}".strip()
    os.makedirs(safe_dir, exist_ok=True)

    print(f"Скачиваем gist {gist_id} от {owner}. Описание: {description!r}")
    print(f"Файлов: {len(files)}. Сохраняем в папку: {safe_dir}")

    for fname, info in files.items():
        raw_url = info.get("raw_url")
        size = info.get("size")
        language = info.get("language")
        if not raw_url:
            print(f"Пропускаем {fname} — нет raw_url.")
            continue
        safe_name = sanitize_filename(fname)
        dest = os.path.join(safe_dir, safe_name)
        try:
            print(f"  -> {fname} (lang={language} size={size}) ... ", end="", flush=True)
            download_file(raw_url, dest, token=args.token)
            print("готово")
        except Exception as e:
            print(f"ошибка: {e}")

    print("Готово.")

if __name__ == "__main__":
    main()
