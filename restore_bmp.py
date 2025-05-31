#!/usr/bin/env python3
import os
import argparse
from PIL import Image
import numpy as np
import torch
from realesrgan import RealESRGANer
from rembg import remove
import cv2
from realesrgan import RealESRGANer
from basicsr.archs.rrdbnet_arch import RRDBNet
import torch, cv2, os

def process_folder(input_dir, output_dir, scale=2):
    device = torch.device('cpu')        # 你的環境是 CPU 版 torch
    os.makedirs(output_dir, exist_ok=True)

    # 1. 建網路殼
    rrdbnet = RRDBNet(
        num_in_ch   = 3,
        num_out_ch  = 3,
        num_feat    = 64,
        num_block   = 23,
        num_grow_ch = 32,
        scale       = scale
    )

    # 2. 建 RealESRGANer，**device 用關鍵字**，CPU 請 half=False
    upsampler = RealESRGANer(
        scale       = scale,
        model_path  = f"C:/Users/swt/Downloads/Real-ESRGAN-0.3.0/Real-ESRGAN-0.3.0/weights/RealESRGAN_x4plus.pth",
        model       = rrdbnet,
        device      = device,
        half        = False              # CPU 不支援 fp16
    )

    for root, dirs, files in os.walk(input_dir):
        for name in files:
            if not name.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                continue

            # 原圖完整路徑
            src_path = os.path.join(root, name)

            # 計算對應的輸出路徑（保留子目錄結構）
            rel_path = os.path.relpath(src_path, input_dir)
            dst_path = os.path.join(output_dir, rel_path)

            os.makedirs(os.path.dirname(dst_path), exist_ok=True)

            # 讀圖 → 放大 → 寫回
            src = cv2.imread(src_path)[:, :, ::-1]  # BGR → RGB
            sr, _ = upsampler.enhance(src, outscale=scale)
            cv2.imwrite(dst_path, sr[:, :, ::-1])   # RGB → BGR


if __name__ == '__main__':
    p = argparse.ArgumentParser(
        description="批次放大 + 去背：Real-ESRGAN + rembg"
    )
    #p.add_argument('input_dir',  help="來源資料夾，放 BMP 檔")
    #p.add_argument('output_dir', help="輸出資料夾，存 PNG 檔")
    #p.add_argument('--scale', type=int, default=1,
    #               help="放大倍數 (預設 4)")
    #args = p.parse_args()
    
    input_dir = "C:/Users/swt/Downloads/oop_game_project-main/oop_game_project-main/RES/source"
    output_dir = "C:/Users/swt/Downloads/oop_game_project-main/oop_game_project-main/RESs/source"
    process_folder(input_dir, output_dir, 4)
