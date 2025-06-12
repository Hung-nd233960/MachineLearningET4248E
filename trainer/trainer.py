"""Trainer class for training a PyTorch model on image data."""

from typing import Optional, Callable, Tuple
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from PIL import Image

import torch
from torch.utils.data import DataLoader
from torch import nn
from torch import optim
from torchvision import transforms

from utils.image_label_dataset import ImageLabelDataset
from trainer.training_utils import (
    load_model,
    decision_logic,
    get_transforms,
    get_criterion,
    get_optimizer,
    get_scheduler,
)
from trainer.sampling import oversample_dataframe, undersample_dataframe


class Trainer:
    df_train: Optional[pd.DataFrame]
    df_val: Optional[pd.DataFrame]
    test_data: Optional[pd.DataFrame]
    training_data: Optional[pd.DataFrame]
    model: Optional[torch.nn.Module]
    criterion: nn.Module
    optimizer: Optional[optim.Optimizer]
    scheduler: Optional[torch.optim.lr_scheduler._LRScheduler]
    transform: transforms.Compose
    batch_size: int
    num_epochs: int
    num_classes: int
    device: torch.device
    decision_mode: str
    decision_fn: Callable
    train_transform: transforms.Compose
    augmentation: bool
    """
    A class to handle the training of a model using PyTorch."""

    def __init__(
        self,
        batch_size: int = 32,
        num_epochs: int = 1,
        num_classes: int = 3,
        decision_mode: str = "safe",
        decision_fn: Callable = decision_logic,
    ):
        self.df_train: Optional[pd.DataFrame] = None
        self.df_val: Optional[pd.DataFrame] = None
        self.model: Optional[torch.nn.Module] = None
        self.criterion = nn.CrossEntropyLoss()
        self.optimizer: Optional[optim.Adam] = None
        self.transform = None
        self.decision_mode = decision_mode
        self.decision_fn = decision_fn
        self.test_data: Optional[pd.DataFrame] = None
        self.batch_size = batch_size
        self.num_epochs = num_epochs
        self.num_classes = num_classes
        self.training_data: Optional[pd.DataFrame] = None
        self.augmentation = True
        self.train_transform = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def load_training_data(
        self,
        chosen_data: Optional[pd.DataFrame] = None,
        balance_method: Optional[str] = None,
    ):
        """
        Load and optionally balance training data from a DataFrame.

        Args:
            chosen_data (pd.DataFrame): Input data to load.
            balance_method (str): 'oversample', 'undersample', or None.
        """
        self.training_data = chosen_data.copy()

        # Filter relevant labels
        self.training_data = self.training_data[
            self.training_data["label"].isin(["None", "BasalGanglia", "CoronaRadiata"])
        ]

        # Split FIRST to preserve natural distribution in validation
        self.df_train, self.df_val = train_test_split(
            self.training_data,
            test_size=0.2,
            stratify=self.training_data["label"],
            random_state=42,
        )

        # Apply sampling ONLY to the training set
        if balance_method == "oversample":
            self.df_train = oversample_dataframe(self.df_train)
        elif balance_method == "undersample":
            self.df_train = undersample_dataframe(self.df_train)

    def load_test_data(self, test_data: pd.DataFrame):
        """Load test data from a Dataframe."""
        self.test_data = test_data.copy()

    def create_dataloaders(
        self, df_train, df_val
    ) -> Tuple[DataLoader, DataLoader, ImageLabelDataset, ImageLabelDataset]:
        """Create DataLoader objects for training and validation datasets.
        One problem in augmentation is augmentation leakage, if we only augment the minority class,
          the model will not learn to generalize well."""
        label_to_idx = {
            label: i
            for i, label in enumerate(["None", "BasalGanglia", "CoronaRadiata"])
        }

        # Create datasets
        train_ds = ImageLabelDataset(
            df_train, transform=self.train_transform, label_to_idx=label_to_idx
        )
        val_ds = ImageLabelDataset(
            df_val, transform=self.transform, label_to_idx=label_to_idx
        )

        # Create dataloaders
        train_loader = DataLoader(train_ds, batch_size=self.batch_size, shuffle=True)
        val_loader = DataLoader(val_ds, batch_size=self.batch_size, shuffle=False)

        return train_loader, val_loader, train_ds, val_ds

    def toolchain_init(
        self,
        augmentation: bool = True,
        criterion_name: str = "crossentropy",
        optimizer_name: str = "adam",
        scheduler_name: Optional[str] = None,
        lr: float = 1e-4,
        scheduler_kwargs: Optional[dict] = None,
    ):
        """
        Initialize loss function, optimizer, and optionally learning rate scheduler.

        Args:
            criterion_name (str): Loss function to use. Default is 'crossentropy'.
            optimizer_name (str): Optimizer to use. Options: 'adam', 'sgd'.
            scheduler_name (Optional[str]): Scheduler to use. Options: 'StepLR', 'ReduceLROnPlateau', etc.
            lr (float): Learning rate.
            scheduler_kwargs (Optional[dict]): Extra keyword arguments for the scheduler.
        """
        # Transform (default to training)
        self.transform = get_transforms(train=False)
        self.train_transform = get_transforms(train=augmentation)
        self.augmentation = augmentation
        # Criterion (loss function)
        self.criterion = get_criterion(criterion_name)

        # Optimizer (requires model parameters to be already loaded)
        if self.model is None:
            raise ValueError("Model must be initialized before calling toolchain_init.")

        self.optimizer = get_optimizer(
            self.model.parameters(), lr=lr, opt_type=optimizer_name
        )

        # Scheduler (optional)
        self.scheduler = None
        if scheduler_name:
            scheduler_kwargs = scheduler_kwargs or {}
            self.scheduler = get_scheduler(
                self.optimizer, scheduler_name=scheduler_name, **scheduler_kwargs
            )

    def train_init(
        self, model_name: Optional[str] = "ResNet34", pretrained: bool = True
    ):
        """Initialize the training process by loading data and setting up the model."""
        train_loader, val_loader, train_ds, val_ds = self.create_dataloaders(
            self.df_train, self.df_val
        )
        # --- Model (Pretrained ResNet) ---
        self.model = load_model(
            model_name=model_name, pretrained=pretrained, num_classes=self.num_classes
        )
        self.model.fc = nn.Linear(self.model.fc.in_features, self.num_classes)
        self.model = self.model.to(self.device)
        self.optimizer = optim.Adam(self.model.parameters(), lr=1e-4)

        return train_loader, val_loader, train_ds, val_ds

    def train(self):
        train_loader, val_loader, train_ds, val_ds = self.train_init()

        for epoch in range(self.num_epochs):
            self.model.train()
            running_loss = 0.0
            correct = 0

            for images, labels in train_loader:
                images, labels = images.to(self.device), labels.to(self.device)

                self.optimizer.zero_grad()
                outputs = self.model(images)
                loss = self.criterion(outputs, labels)
                loss.backward()
                self.optimizer.step()

                running_loss += loss.item() * images.size(0)
                _, preds = torch.max(outputs, 1)
                correct += (preds == labels).sum().item()

            epoch_loss = running_loss / len(train_ds)
            epoch_acc = correct / len(train_ds)
            print(
                f"Epoch {epoch+1}/{self.num_epochs} - Train loss: {epoch_loss:.4f} - Acc: {epoch_acc:.4f}"
            )

            # --- Validation with inconclusive counting and classification report ---
            self.model.eval()
            val_preds = []
            val_labels = []
            inconclusive_count = 0

            with torch.no_grad():
                for images, labels in val_loader:
                    images, labels = images.to(self.device), labels.to(self.device)
                    outputs = self.model(images)

                    for i in range(images.size(0)):
                        pred = self.decision_fn(
                            outputs[i], mode=self.decision_mode
                        )  # Your decision logic function
                        val_preds.append(pred)
                        val_labels.append(labels[i].item())
                        if pred == -1:
                            inconclusive_count += 1

            total = len(val_preds)
            print(
                f"            → Inconclusive predictions: {inconclusive_count}/{total} ({inconclusive_count/total:.1%})"
            )

            # Filter out inconclusive (-1) for metrics
            preds_filtered = [p for p in val_preds if p != -1]
            labels_filtered = [l for p, l in zip(val_preds, val_labels) if p != -1]

            if preds_filtered:
                print("            → Classification Report (excluding inconclusive):")
                print(
                    classification_report(
                        labels_filtered,
                        preds_filtered,
                        target_names=["None", "BasalGanglia", "CoronaRadiata"],
                    )
                )
                print("            → Confusion Matrix:")
                print(confusion_matrix(labels_filtered, preds_filtered))
            else:
                print(
                    "            → All predictions were inconclusive; no classification report available."
                )

    def test(self, test_data: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare and evaluate the test data, returning a DataFrame with predictions.

        Args:
            test_data (pd.DataFrame): DataFrame with a 'path' column for test image paths.

        Returns:
            pd.DataFrame: Original DataFrame with added columns for predicted probabilities.
        """
        self.load_test_data(test_data)

        self.model.eval()
        results = []

        transform = self.transform
        softmax = nn.Softmax(dim=1)

        with torch.no_grad():
            for i, row in self.test_data.iterrows():
                image_path = row["path"]
                try:
                    image = Image.open(image_path).convert("RGB")
                    image = transform(image)
                    image = image.unsqueeze(0).to(self.device)

                    output = self.model(image)
                    probs = softmax(output).squeeze().cpu().numpy()

                    # Add prediction scores to results
                    results.append(
                        {
                            **row,  # Original row data
                            "prob_None": float(probs[0]) * 100,
                            "prob_BasalGanglia": float(probs[1]) * 100,
                            "prob_CoronaRadiata": float(probs[2]) * 100,
                        }
                    )

                except Exception as e:
                    print(f"Error processing {image_path}: {e}")
                    # Add fallback zero probabilities
                    results.append(
                        {
                            **row,
                            "prob_None": 0.0,
                            "prob_BasalGanglia": 0.0,
                            "prob_CoronaRadiata": 0.0,
                        }
                    )

        self.test_data = pd.DataFrame(results)
        return self.test_data

    def export_results(self, filename: str = "test_results.csv", path="results/"):
        """Export the test results to a CSV file."""
        if self.test_data is not None:
            self.test_data.to_csv(f"{path}{filename}", index=False)
            print(f"Results exported to {path}{filename}")
        else:
            print("No test data available. Please run the test method first.")

    def export_model(self, model_path: str):
        """Export the trained model to a file."""
        if self.model is not None:
            torch.save(self.model.state_dict(), model_path)
            print(f"Model exported to {model_path}")
        else:
            print("No model to export. Please train the model first.")


if __name__ == "__main__":
    trainer = Trainer(batch_size=32, num_epochs=1, num_classes=3)
