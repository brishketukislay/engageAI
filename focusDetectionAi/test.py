import torch
from transformers import AutoImageProcessor, TimesformerForVideoClassification

print("Loading TimeSformer model configurations...")
try:
    # We use the base Kinetics-400 video model checkpoint as our foundation
    model_name = "facebook/timesformer-base-finetuned-kinetics400"
    processor = AutoImageProcessor.from_pretrained(model_name)
    model = TimesformerForVideoClassification.from_pretrained(model_name)
    print("\n✅ Success! TimeSformer loaded perfectly and is ready to classify video frames.")
except Exception as e:
    print(f"\n❌ An error occurred while loading the model: {e}")