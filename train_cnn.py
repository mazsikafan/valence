"""
CNN Morphology Classification — Production Training Script
Trains EfficientNet-B0, ResNet50, MobileNetV3 on real bovine sperm crops.
Uses focal loss for class imbalance, aggressive augmentation, early stopping.
"""
import os, sys, json, time, random
import numpy as np
import pandas as pd
from pathlib import Path
from collections import Counter

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler
from torchvision import transforms, models
from PIL import Image
from sklearn.metrics import (
    classification_report, confusion_matrix, f1_score,
    balanced_accuracy_score, accuracy_score
)

# ── Config ────────────────────────────────────────────────────────────────────
SEED = 42
DEVICE = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
PROJECT_ROOT = Path("/Users/balintmaroti/Documents/bull_sperm")
CROPS_DIR = PROJECT_ROOT / "data" / "processed" / "morphology_crops"
MANIFEST_PATH = PROJECT_ROOT / "data" / "manifests" / "crops_manifest_with_splits.csv"
MODELS_DIR = PROJECT_ROOT / "models"
REPORTS_DIR = PROJECT_ROOT / "reports"

IMG_SIZE = 128  # Larger than 64x64 for CNN
BATCH_SIZE = 32
NUM_WORKERS = 0
EPOCHS = 50
PATIENCE = 10
LR = 3e-4
WEIGHT_DECAY = 1e-4

random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

print(f"Device: {DEVICE}")
print(f"PyTorch: {torch.__version__}")

# ── Dataset ───────────────────────────────────────────────────────────────────
class SpermCropDataset(Dataset):
    def __init__(self, df, crops_dir, transform=None, class_to_idx=None):
        self.df = df.reset_index(drop=True)
        self.crops_dir = Path(crops_dir)
        self.transform = transform
        self.class_to_idx = class_to_idx or {}

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        img_path = self.crops_dir / row["crop_file"]

        img = Image.open(img_path).convert("RGB")
        if self.transform:
            img = self.transform(img)

        label = self.class_to_idx.get(row["class_name"], 0)
        return img, label

# ── Focal Loss ────────────────────────────────────────────────────────────────
class FocalLoss(nn.Module):
    def __init__(self, alpha=None, gamma=2.0, reduction='mean'):
        super().__init__()
        self.alpha = alpha  # class weights tensor
        self.gamma = gamma
        self.reduction = reduction

    def forward(self, inputs, targets):
        ce_loss = nn.functional.cross_entropy(inputs, targets, weight=self.alpha, reduction='none')
        pt = torch.exp(-ce_loss)
        focal_loss = ((1 - pt) ** self.gamma) * ce_loss
        if self.reduction == 'mean':
            return focal_loss.mean()
        return focal_loss.sum()

# ── Load Data ─────────────────────────────────────────────────────────────────
print("\nLoading data...")
df = pd.read_csv(MANIFEST_PATH)
print(f"Total crops: {len(df)}")

# Build class mapping
class_names = sorted(df["class_name"].unique().tolist())
class_to_idx = {c: i for i, c in enumerate(class_names)}
idx_to_class = {i: c for c, i in class_to_idx.items()}
n_classes = len(class_names)
print(f"Classes ({n_classes}): {class_names}")

train_df = df[df["split"] == "train"].copy()
val_df = df[df["split"] == "val"].copy()
test_df = df[df["split"] == "test"].copy()

print(f"Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")

# Class weights for focal loss
train_counts = train_df["class_name"].value_counts()
total = len(train_df)
class_weights = torch.tensor(
    [total / (n_classes * train_counts.get(c, 1)) for c in class_names],
    dtype=torch.float32
).to(DEVICE)
print(f"Class weights: {dict(zip(class_names, class_weights.cpu().numpy().round(2)))}")

# Weighted sampler for balanced batches
sample_weights = train_df["class_name"].map(
    lambda c: total / (n_classes * train_counts.get(c, 1))
).values
sampler = WeightedRandomSampler(sample_weights, num_samples=len(train_df), replacement=True)

# ── Transforms ────────────────────────────────────────────────────────────────
train_transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.RandomHorizontalFlip(0.5),
    transforms.RandomVerticalFlip(0.5),
    transforms.RandomRotation(30),
    transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.2),
    transforms.RandomAffine(degrees=0, translate=(0.1, 0.1), scale=(0.85, 1.15)),
    transforms.GaussianBlur(kernel_size=3, sigma=(0.1, 1.0)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    transforms.RandomErasing(p=0.1),
])

val_transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])

train_dataset = SpermCropDataset(train_df, CROPS_DIR, train_transform, class_to_idx)
val_dataset = SpermCropDataset(val_df, CROPS_DIR, val_transform, class_to_idx)
test_dataset = SpermCropDataset(test_df, CROPS_DIR, val_transform, class_to_idx)

train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, sampler=sampler, num_workers=NUM_WORKERS)
val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=NUM_WORKERS)
test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=NUM_WORKERS)

# ── Model Definitions ─────────────────────────────────────────────────────────
def create_model(arch, n_classes, pretrained=True):
    if arch == "efficientnet_b0":
        model = models.efficientnet_b0(weights="IMAGENET1K_V1" if pretrained else None)
        model.classifier[1] = nn.Linear(model.classifier[1].in_features, n_classes)
    elif arch == "resnet50":
        model = models.resnet50(weights="IMAGENET1K_V2" if pretrained else None)
        model.fc = nn.Linear(model.fc.in_features, n_classes)
    elif arch == "mobilenet_v3_small":
        model = models.mobilenet_v3_small(weights="IMAGENET1K_V1" if pretrained else None)
        model.classifier[3] = nn.Linear(model.classifier[3].in_features, n_classes)
    else:
        raise ValueError(f"Unknown arch: {arch}")
    return model

# ── Training Loop ─────────────────────────────────────────────────────────────
def train_model(model, arch_name, train_loader, val_loader, n_classes,
                epochs=EPOCHS, lr=LR, patience=PATIENCE):
    model = model.to(DEVICE)
    criterion = FocalLoss(alpha=class_weights, gamma=2.0)
    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=WEIGHT_DECAY)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    best_val_f1 = 0
    best_epoch = 0
    patience_counter = 0
    history = []

    print(f"\n{'='*70}")
    print(f"Training {arch_name} | {n_classes} classes | LR={lr} | Device={DEVICE}")
    print(f"{'='*70}")

    for epoch in range(epochs):
        # Train
        model.train()
        train_loss = 0
        train_correct = 0
        train_total = 0

        for images, labels in train_loader:
            images, labels = images.to(DEVICE), labels.to(DEVICE)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            train_loss += loss.item() * images.size(0)
            _, predicted = outputs.max(1)
            train_total += labels.size(0)
            train_correct += predicted.eq(labels).sum().item()

        scheduler.step()

        train_acc = train_correct / train_total
        train_loss = train_loss / train_total

        # Validate
        model.eval()
        val_preds = []
        val_labels = []
        val_loss = 0

        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(DEVICE), labels.to(DEVICE)
                outputs = model(images)
                loss = criterion(outputs, labels)
                val_loss += loss.item() * images.size(0)
                _, predicted = outputs.max(1)
                val_preds.extend(predicted.cpu().numpy())
                val_labels.extend(labels.cpu().numpy())

        val_acc = accuracy_score(val_labels, val_preds)
        val_bal_acc = balanced_accuracy_score(val_labels, val_preds)
        val_f1 = f1_score(val_labels, val_preds, average='macro', zero_division=0)
        val_loss = val_loss / len(val_labels)

        history.append({
            "epoch": epoch + 1, "train_loss": train_loss, "train_acc": train_acc,
            "val_loss": val_loss, "val_acc": val_acc, "val_bal_acc": val_bal_acc, "val_f1": val_f1,
        })

        if (epoch + 1) % 5 == 0 or epoch == 0:
            print(f"  Epoch {epoch+1:3d}/{epochs} | "
                  f"Train Loss: {train_loss:.4f} Acc: {train_acc:.3f} | "
                  f"Val Loss: {val_loss:.4f} Acc: {val_acc:.3f} BalAcc: {val_bal_acc:.3f} F1: {val_f1:.3f}")

        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            best_epoch = epoch + 1
            patience_counter = 0
            torch.save(model.state_dict(), MODELS_DIR / f"cnn_{arch_name}_best.pt")
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print(f"  Early stopping at epoch {epoch+1} (best F1: {best_val_f1:.4f} at epoch {best_epoch})")
                break

    print(f"  Best val F1: {best_val_f1:.4f} at epoch {best_epoch}")
    return model, history, best_val_f1

# ── Evaluation ────────────────────────────────────────────────────────────────
def evaluate_model(model, test_loader, arch_name):
    model.eval()
    all_preds = []
    all_labels = []
    all_probs = []

    with torch.no_grad():
        for images, labels in test_loader:
            images = images.to(DEVICE)
            outputs = model(images)
            probs = torch.softmax(outputs, dim=1)
            _, predicted = outputs.max(1)
            all_preds.extend(predicted.cpu().numpy())
            all_labels.extend(labels.numpy())
            all_probs.extend(probs.cpu().numpy())

    acc = accuracy_score(all_labels, all_preds)
    bal_acc = balanced_accuracy_score(all_labels, all_preds)
    f1_mac = f1_score(all_labels, all_preds, average='macro', zero_division=0)

    print(f"\n{'='*70}")
    print(f"TEST RESULTS: {arch_name}")
    print(f"{'='*70}")
    print(f"  Accuracy:          {acc:.4f}")
    print(f"  Balanced Accuracy: {bal_acc:.4f}")
    print(f"  F1 Macro:          {f1_mac:.4f}")
    print(f"\n{classification_report(all_labels, all_preds, target_names=class_names, zero_division=0)}")

    return {
        "arch": arch_name,
        "accuracy": round(acc, 4),
        "balanced_accuracy": round(bal_acc, 4),
        "f1_macro": round(f1_mac, 4),
        "predictions": all_preds,
        "labels": all_labels,
        "probabilities": all_probs,
    }

# ── Train All Architectures ──────────────────────────────────────────────────
architectures = ["efficientnet_b0", "resnet50", "mobilenet_v3_small"]
all_results = {}

for arch in architectures:
    print(f"\n\n{'#'*70}")
    print(f"  ARCHITECTURE: {arch}")
    print(f"{'#'*70}")

    model = create_model(arch, n_classes, pretrained=True)
    model, history, best_f1 = train_model(model, arch, train_loader, val_loader, n_classes)

    # Load best weights and evaluate
    model.load_state_dict(torch.load(MODELS_DIR / f"cnn_{arch}_best.pt", weights_only=True))
    model = model.to(DEVICE)
    results = evaluate_model(model, test_loader, arch)
    results["history"] = history
    all_results[arch] = results

# ── Final Comparison ──────────────────────────────────────────────────────────
print(f"\n\n{'='*70}")
print("CNN MODEL COMPARISON — BOVINE SPERM MORPHOLOGY")
print(f"{'='*70}")
print(f"{'Model':<25} {'Accuracy':>10} {'Bal.Acc':>10} {'F1 Macro':>10}")
print("-" * 55)
for arch, r in all_results.items():
    print(f"{arch:<25} {r['accuracy']:>10.4f} {r['balanced_accuracy']:>10.4f} {r['f1_macro']:>10.4f}")

best_arch = max(all_results, key=lambda k: all_results[k]["f1_macro"])
print(f"\nBest model: {best_arch} (F1={all_results[best_arch]['f1_macro']:.4f})")

# Save results
results_summary = {k: {kk: vv for kk, vv in v.items() if kk not in ("predictions", "labels", "probabilities", "history")}
                   for k, v in all_results.items()}
with open(REPORTS_DIR / "cnn_results.json", "w") as f:
    json.dump(results_summary, f, indent=2)

print(f"\nResults saved to {REPORTS_DIR / 'cnn_results.json'}")
print("CNN training complete.")
