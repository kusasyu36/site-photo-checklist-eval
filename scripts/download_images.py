"""data/manifest.jsonl の画像を data/images/ に取得する（Wikimedia Commons、1024px版）。"""
from spce.data import download_images, load_manifest

if __name__ == "__main__":
    paths = download_images(load_manifest())
    print(f"downloaded {len(paths)} images")
