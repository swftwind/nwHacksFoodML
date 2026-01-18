import sys
print("Checkpoint 1: Script started")

try:
    import torch
    print(f"Checkpoint 2: Torch loaded (Version: {torch.__version__})")
    
    from torchvision import models
    print("Checkpoint 3: Torchvision models loaded")
    
    print("Checkpoint 4: Attempting to load ResNet50 weights...")
    model = models.resnet50(pretrained=True)
    model.eval()
    print("Checkpoint 5: Model is in memory")
    
    print("\n*** ALL SYSTEMS GO: Ready for Fridge ML ***")

except Exception as e:
    print(f"\n!!! ERROR AT CHECKPOINT !!!\n{e}")
    sys.exit(1)