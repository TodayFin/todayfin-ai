# model.py
import json
import torch
import gc
from transformers import T5Tokenizer, T5ForConditionalGeneration

def load_model(model_name="kdk07718/t5-small-finetuned-cnn-news"):
    # Load tokenizer
    tokenizer = T5Tokenizer.from_pretrained(model_name)

    # Load the model and move to GPU if available
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = T5ForConditionalGeneration.from_pretrained(model_name).to(device)

    # Optimize memory usage by using mixed precision (fp16)
    if torch.cuda.is_available():
        model.half()

    return model, tokenizer, device
