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
                save_path = output_path / img_path.name
                flipped.save(save_path)
                count += 1
            except Exception as e:
                print(f"❌ 無法處理圖片 {img_path.name}: {e}")

    print(f"✅ 已處理 {count} 張圖片，並儲存於 {output_folder}")

# ✅ 使用範例
if __name__ == "__main__":
    src_folder = "assets_aligned\\npc\\woman\\right"       # 原始資料夾
    dst_folder = "assets_aligned\\npc\\woman\\left"        # 儲存翻轉後圖片的資料夾
    flip_images_in_folder(src_folder, dst_folder)
