"""Merge a trained LoRA adapter into Whisper large-v3 and convert it to CTranslate2 for faster-whisper (live mode).

    ~/venvs/train/bin/python dataset/convert_to_ct2.py /mnt/storage/models/whisper-yue-lora /mnt/storage/models/whisper-yue-ct2
"""

import os
import shutil
import subprocess
import sys
import tempfile

import torch
from peft import PeftModel
from transformers import WhisperForConditionalGeneration, WhisperProcessor

BASE_MODEL = "openai/whisper-large-v3"


def main(adapter_folder, output_folder):
    merged_folder = tempfile.mkdtemp(prefix="whisper-merged-", dir="/mnt/storage/models")
    base = WhisperForConditionalGeneration.from_pretrained(BASE_MODEL, torch_dtype=torch.float16)
    merged = PeftModel.from_pretrained(base, adapter_folder).merge_and_unload()
    merged.save_pretrained(merged_folder)
    WhisperProcessor.from_pretrained(BASE_MODEL).save_pretrained(merged_folder)
    converter = os.path.join(os.path.dirname(sys.executable), "ct2-transformers-converter")
    subprocess.run([converter, "--model", merged_folder, "--output_dir", output_folder, "--force",
                    "--quantization", "float16", "--copy_files", "tokenizer.json", "preprocessor_config.json"], check=True)
    shutil.rmtree(merged_folder)
    print("converted:", output_folder, os.listdir(output_folder))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
