#!/usr/bin/env python3
"""
Script để trích xuất model_state_dict từ checkpoint fine-tuning CLIP.
Tạo một file model.pt mới chỉ chứa state_dict của mô hình.
"""

import os
import torch
import argparse
from pathlib import Path

def extract_model_state_dict(checkpoint_path, output_path=None):
    """
    Trích xuất model_state_dict từ checkpoint và lưu thành file riêng.
    
    Args:
        checkpoint_path: Đường dẫn đến file checkpoint
        output_path: Đường dẫn để lưu model_state_dict
    """
    print(f"Đang tải checkpoint từ {checkpoint_path}...")
    checkpoint = torch.load(checkpoint_path, map_location=torch.device('cpu'))
    
    if not isinstance(checkpoint, dict):
        print(f"Không hỗ trợ định dạng checkpoint: {type(checkpoint)}")
        return False
    
    if 'model_state_dict' not in checkpoint:
        print("Không tìm thấy model_state_dict trong checkpoint")
        print(f"Các khóa có trong checkpoint: {list(checkpoint.keys())}")
        return False
    
    model_state_dict = checkpoint['model_state_dict']
    
    if output_path is None:
        output_dir = os.path.dirname(checkpoint_path)
        base_name = os.path.splitext(os.path.basename(checkpoint_path))[0]
        output_path = os.path.join(output_dir, f"{base_name}_model_only.pt")
    
    print(f"Đang lưu model_state_dict vào {output_path}...")
    torch.save(model_state_dict, output_path)
    print("Đã lưu thành công!")
    return True

def main():
    parser = argparse.ArgumentParser(description="Trích xuất model_state_dict từ checkpoint")
    parser.add_argument("--checkpoint", "-c", required=True, help="Đường dẫn đến file checkpoint")
    parser.add_argument("--output", "-o", help="Đường dẫn để lưu model_state_dict (tùy chọn)")
    
    args = parser.parse_args()
    success = extract_model_state_dict(args.checkpoint, args.output)
    
    if success:
        print("Hoàn thành trích xuất model_state_dict!")
    else:
        print("Không thể trích xuất model_state_dict từ checkpoint.")

if __name__ == "__main__":
    main() 