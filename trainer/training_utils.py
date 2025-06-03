from typing import Optional
import torch
from torch import nn, optim
from torchvision import models as tv_models
from torchvision import transforms

MODEL_REGISTRY = {
    "ResNet18": tv_models.resnet18,
    "ResNet34": tv_models.resnet34,
    "ResNet50": tv_models.resnet50,
    "ResNet101": tv_models.resnet101,
    "ResNet152": tv_models.resnet152,
    "ResNext50_32x4d": tv_models.resnext50_32x4d,
    "ResNext101_32x8d": tv_models.resnext101_32x8d,
}

def load_model(model_name: Optional[str], pretrained: bool, num_classes: int):
    """Load a pretrained model from the registry and modify it for the specified number of classes."""
    if model_name not in MODEL_REGISTRY:
        raise ValueError(f"Model '{model_name}' not found. Options: {list(MODEL_REGISTRY.keys())}")
    
    model = MODEL_REGISTRY[model_name](pretrained=pretrained)
    model.fc = nn.Linear(model.fc.in_features, num_classes)
    return model

def get_transforms(train=True):
    """Get the appropriate transforms for training or validation."""
    base = [
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ]
    if train:
        augment = [transforms.RandomHorizontalFlip(), transforms.ColorJitter()]
        return transforms.Compose(augment + base)
    return transforms.Compose(base)

def get_criterion(loss_type="crossentropy"):
    if loss_type == "crossentropy":
        return nn.CrossEntropyLoss()
    else:
        raise ValueError("Unsupported loss")

def get_optimizer(params, lr=1e-4, opt_type="adam"):
    if opt_type == "adam":
        return optim.Adam(params, lr=lr)
    elif opt_type == "sgd":
        return optim.SGD(params, lr=lr, momentum=0.9)
    else:
        raise ValueError("Unsupported optimizer")

def get_scheduler(optimizer, scheduler_name="StepLR", **kwargs):
    """
    Returns a PyTorch learning rate scheduler based on the name.
    
    Args:
        optimizer (torch.optim.Optimizer): The optimizer to attach the scheduler to.
        scheduler_name (str): Name of the scheduler. Options:
            - "StepLR"
            - "ReduceLROnPlateau"
            - "ExponentialLR"
            - "CosineAnnealingLR"
            - "OneCycleLR"
        **kwargs: Additional scheduler-specific arguments.
    
    Returns:
        torch.optim.lr_scheduler._LRScheduler or ReduceLROnPlateau
    """
    name = scheduler_name.lower()

    if name == "steplr":
        return torch.optim.lr_scheduler.StepLR(optimizer, 
                                               step_size=kwargs.get("step_size", 10), 
                                               gamma=kwargs.get("gamma", 0.1))
    if name == "reducelronplateau":
        return torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, 
                                                          mode=kwargs.get("mode", "min"),
                                                          factor=kwargs.get("factor", 0.1),
                                                          patience=kwargs.get("patience", 5))
    if name == "exponentiallr":
        return torch.optim.lr_scheduler.ExponentialLR(optimizer, 
                                                      gamma=kwargs.get("gamma", 0.9))
    if name == "cosineannealinglr":
        return torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, 
                                                          T_max=kwargs.get("T_max", 50))
    if name == "onecyclelr":
        return torch.optim.lr_scheduler.OneCycleLR(optimizer, 
                                                   max_lr=kwargs.get("max_lr", 0.01),
                                                   steps_per_epoch=kwargs.get("steps_per_epoch",
                                                                               100),
                                                   epochs=kwargs.get("epochs", 10))
    raise ValueError(f"Unsupported scheduler: {scheduler_name}")

def decision_logic(output: torch.Tensor, mode="safe", threshold=0.7, margin=0.1) -> int:
    """
    Decide which class to return or return -1 if decision is inconclusive.

    Args:
        output (torch.Tensor): Raw logits output from the model (1D tensor).
        mode (str): Decision mode: 'max', 'threshold', 'margin', '50percent', or 'safe'.
        threshold (float): Probability threshold for decision confidence.
        margin (float): Required difference between top-1 and top-2 probabilities.

    Returns:
        int: Predicted class index or -1 if inconclusive.
    """
    softmax = torch.nn.Softmax(dim=1)
    probs = softmax(output.unsqueeze(0)).squeeze()  # shape: (num_classes,)

    top_vals, top_idxs = torch.topk(probs, 2)
    top_val, top_idx = top_vals[0], top_idxs[0]
    second_val = top_vals[1]

    if mode == "max":
        return int(top_idx.item())

    elif mode == "threshold":
        return int(top_idx.item() if top_val >= threshold else -1)

    elif mode == "margin":
        return int(top_idx.item() if (top_val - second_val) >= margin else -1)

    elif mode == "50percent":
        return int(top_idx.item() if top_val >= 0.5 else -1)

    elif mode == "safe":
        if top_val >= threshold and (top_val - second_val) >= margin:
            return int(top_idx.item())
        else:
            return -1

    else:
        raise ValueError(f"Unsupported mode '{mode}'. Choose from 'max', 'threshold', 'margin', '50percent', or 'safe'.")
