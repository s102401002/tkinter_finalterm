#!/usr/bin/env python3
import os
import argparse
from PIL import Image
import numpy as np
import torch
from realesrgan import RealESRGANer
from rembg import remove
import cv2
def process_folder(input_dir: str, output_dir: str, scale: int):
    os.makedirs(output_dir, exist_ok=True)

    # 選擇運算裝置
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"使用裝置：{device}, 放大倍數：{scale}x")
    
    # 載入 Real-ESRGAN 模型
    model = RealESRGANer(device, scale=scale)
    model_path = f'RealESRGAN_x{scale}.pth'
    print(f"載入權重：{model_path}")
    model.load_weights(model_path)

    for fname in os.listdir(input_dir):
        if not fname.lower().endswith('.bmp'):
            continue

        in_path = os.path.join(input_dir, fname)
        print(f"處理：{in_path}")
        # 讀圖並轉成 RGB
        img = Image.open(in_path).convert('RGB')

        # 1) 超解析
        sr = model.predict(img)

        # 2) 去背（rembg 接收 numpy array）
        sr_np = np.array(sr)
        fg_np = remove(sr_np)

        # 3) 結果轉回 PIL，並存成 PNG
        out = Image.fromarray(fg_np)
        base = os.path.splitext(fname)[0]
        out_path = os.path.join(output_dir, base + '.png')
        out.save(out_path)
        print(f"輸出：{out_path}\n")

if __name__ == '__main__':
    p = argparse.ArgumentParser(
        description="批次放大 + 去背：Real-ESRGAN + rembg"
    )
    #p.add_argument('input_dir',  help="來源資料夾，放 BMP 檔")
    #p.add_argument('output_dir', help="輸出資料夾，存 PNG 檔")
    #p.add_argument('--scale', type=int, default=1,
    #               help="放大倍數 (預設 4)")
    #args = p.parse_args()
    
    input_dir = "C:/Users/swt/Downloads/oop_game_project-main/oop_game_project-main/RES/girl/normalGirl1/left"
    output_dir = "C:/Users/swt/Downloads/loop_game_project-main/oop_game_project-main/RES/girl/normalGirl1/leftt"
    process_folder(input_dir, output_dir, 1)
