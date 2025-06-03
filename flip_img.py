'''
from pathlib import Path
from PIL import Image, ImageOps
import shutil

def flip_images_in_folder(input_folder: str, output_folder: str):
    input_path = Path(input_folder)
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)

    # 支援的圖片格式
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}

    count = 0
    for img_path in input_path.iterdir():
        if img_path.suffix.lower() in image_extensions:
            try:
                img = Image.open(img_path)
                flipped = ImageOps.mirror(img)
                save_path = output_path / f"{count}.png"  # ← 改成連號命名
                #save_path = output_path / img_path.name
                flipped.save(save_path)
                count += 1
            except Exception as e:
                print(f"❌ 無法處理圖片 {img_path.name}: {e}")

    print(f"✅ 已處理 {count} 張圖片，並儲存於 {output_folder}")

# ✅ 使用範例
if __name__ == "__main__":
    src_folder = r"assets_aligned\player\right\reinforcing"       # 原始資料夾
    dst_folder = r"assets_aligned\player\left\reinforcing"        # 儲存翻轉後圖片的資料夾
    flip_images_in_folder(src_folder, dst_folder)
'''
from pathlib import Path
from PIL import Image, ImageOps
import re

def flip_images_in_folder(input_folder: str, output_folder: str):
    input_path = Path(input_folder)
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)

    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}

    pattern = re.compile(r"(\d+)")  # 尋找檔名中的數字

    count = 0
    for img_path in sorted(input_path.iterdir()):
        if img_path.suffix.lower() in image_extensions:
            try:
                img = Image.open(img_path)
                flipped = ImageOps.mirror(img)

                # 嘗試從檔名中抓出第一個數字
                match = pattern.search(img_path.stem)
                if match:
                    number = match.group(1)
                    save_name = f"{number}.png"
                else:
                    save_name = f"unknown_{count}.png"
                    count += 1  # 避免覆蓋

                save_path = output_path / save_name
                flipped.save(save_path)
            except Exception as e:
                print(f"❌ 無法處理圖片 {img_path.name}: {e}")

    print(f"✅ 圖片已翻轉並依數字命名儲存於：{output_folder}")

# ✅ 使用範例
if __name__ == "__main__":
    src_folder = r"C:\Users\swt\tkinter_finalterm\assets_aligned\player\left\reinforcing"
    dst_folder = r"C:\Users\swt\tkinter_finalterm\assets_aligned\player\right\reinforcing"
    flip_images_in_folder(src_folder, dst_folder)
