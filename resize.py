from PIL import Image
from pathlib import Path

def resize_to_height(src_folder:  Path, dst_folder: Path, target_h: int):
    src_folder = Path(src_folder)
    dst_folder = Path(dst_folder)
    dst_folder.mkdir(parents=True, exist_ok=True)

    exts = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
    count = 0

    for img_path in src_folder.rglob("*"):
        if img_path.suffix.lower() in exts:
            try:
                img = Image.open(img_path)
                orig_w, orig_h = img.size
                scale = target_h / orig_h
                new_w = int(round(orig_w * scale))
                resized = img.resize((new_w, target_h), Image.LANCZOS)

                dst_path = dst_folder / img_path.name
                resized.save(dst_path)
                print(f"✓ {img_path.name}  →  {new_w}×{target_h}")
                count += 1
            except Exception as e:
                print(f"✗ {img_path.name} 失敗: {e}")
    
    print(f"\n共處理 {count} 張圖片。")

# 使用方法
resize_to_height("tkinter_finalterm-main\\assets_aligned\player", "tkinter_finalterm-main\\assets_aligned\player_re", target_h=596)
