import torch, platform, sys
import realesrgan, importlib.metadata, inspect
print("realesrgan version:", importlib.metadata.version("realesrgan"))
print("Has RealESRGAN?   ", hasattr(realesrgan, "RealESRGAN"))
print("Has RealESRGANer? ", hasattr(realesrgan, "RealESRGANer"))