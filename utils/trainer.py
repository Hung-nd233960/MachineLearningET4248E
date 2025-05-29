"""Trainer class for training a PyTorch model on image data."""
from typing import Optional
import pandas as pd
from sklearn.model_selection import train_test_split
from PIL import Image

import torch
from torch.utils.data import DataLoader
from torch import nn
from torch import optim

from torchvision import models
from torchvision import transforms
from utils.image_label_dataset import ImageLabelDataset

class Trainer():
    df_train: Optional[pd.DataFrame]
    df_val: Optional[pd.DataFrame]
    test_data: Optional[pd.DataFrame]
    training_data: Optional[pd.DataFrame]
    model: Optional[torch.nn.Module]
    criterion: nn.Module
    optimizer: Optional[optim.Optimizer]
    transform: transforms.Compose
    batch_size: int
    num_epochs: int
    num_classes: int
    device: torch.device
    """
    A class to handle the training of a model using PyTorch."""
    def __init__(self, batch_size: int = 32, num_epochs: int = 1, num_classes: int = 3):
        
      
        self.df_train: pd.DataFrame = None
        self.df_val: pd.DataFrame = None
        self.model: models = None
        self.criterion = nn.CrossEntropyLoss()
        self.optimizer: Optional[optim.Adam] = None
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        self.test_data: pd.DataFrame = None
        self.batch_size = batch_size
        self.num_epochs = num_epochs
        self.num_classes = num_classes
        self.training_data: pd.DataFrame = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def load_training_data(self, chosen_data: pd.DataFrame = None):
        """Load training data from a Dataframe and filter it based on the chosen data."""
        self.training_data = chosen_data.copy()
        # Filter labels if needed
        self.training_data = self.training_data[self.training_data['label']
                                                .isin(['None', 'BasalGanglia', 'Thalamus'])]
        # Split into train and validation sets
        self.df_train, self.df_val = train_test_split(self.training_data, 
                                            test_size=0.2, stratify=self.training_data['label'], random_state=42)
    
    def load_test_data(self, test_data: pd.DataFrame):
        """Load test data from a Dataframe."""
        self.test_data = test_data.copy()
    
    def create_dataloaders(self, df_train, df_val):
        """Create DataLoader objects for training and validation datasets."""
        
        transform = self.transform
        label_to_idx = {label: i for i, label in enumerate(['None', 'BasalGanglia', 'Thalamus'])}

        # Create datasets
        train_ds = ImageLabelDataset(df_train, transform=transform, label_to_idx=label_to_idx)
        val_ds = ImageLabelDataset(df_val, transform=transform, label_to_idx=label_to_idx)

        # Create dataloaders
        train_loader = DataLoader(train_ds, batch_size=self.batch_size, shuffle=True)
        val_loader = DataLoader(val_ds, batch_size=self.batch_size, shuffle=False)

        return train_loader, val_loader, train_ds, val_ds

    def train_init(self):
        """Initialize the training process by loading data and setting up the model."""
        train_loader, val_loader, train_ds, val_ds = self.create_dataloaders(self.df_train, self.df_val)
        # --- Model (Pretrained ResNet) ---
        self.model = models.resnet34(pretrained=True)
        self.model.fc = nn.Linear(self.model.fc.in_features, self.num_classes)
        self.model = self.model.to(self.device)
        self.optimizer = optim.Adam(self.model.parameters(), lr=1e-4)
        
        return train_loader, val_loader, train_ds, val_ds
        # --- Training ---
    def train(self):
        """Train the model using the training data."""
        train_loader, val_loader, train_ds, val_ds =  self.train_init()

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
            print(f"Epoch {epoch+1}/{self.num_epochs} - Train loss: {epoch_loss:.4f} - Acc: {epoch_acc:.4f}")

            # Validation
            self.model.eval()
            val_correct = 0
            with torch.no_grad():
                for images, labels in val_loader:
                    images, labels = images.to(self.device), labels.to(self.device)
                    outputs = self.model(images)
                    _, preds = torch.max(outputs, 1)
                    val_correct += (preds == labels).sum().item()

            val_acc = val_correct / len(val_ds)
            print(f"            → Val acc: {val_acc:.4f}")

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
                image_path = row['path']
                try:
                    image = Image.open(image_path).convert('RGB')
                    image = transform(image).unsqueeze(0).to(self.device)

                    output = self.model(image)
                    probs = softmax(output).squeeze().cpu().numpy()

                    # Add prediction scores to results
                    results.append({
                        **row,  # Original row data
                        'prob_None': float(probs[0]) * 100,
                        'prob_BasalGanglia': float(probs[1]) * 100,
                        'prob_Thalamus': float(probs[2]) * 100
                    })

                except Exception as e:
                    print(f"Error processing {image_path}: {e}")
                    # Add fallback zero probabilities
                    results.append({
                        **row,
                        'prob_None': 0.0,
                        'prob_BasalGanglia': 0.0,
                        'prob_Thalamus': 0.0
                    })

        self.test_data = pd.DataFrame(results)
        self.test_data.to_csv("test_results.csv", index=False)
        print("Test results saved to 'test_results.csv'")
        print(self.test_data.head())
        return self.test_data
    
if __name__ == "__main__":
    trainer = Trainer(batch_size=32, num_epochs=1, num_classes=3)
    # Example usage:
    # Load your training data into a DataFrame
    # df_train = pd.read_csv('path_to_your_training_data.csv')
    # trainer.load_training_data(df_train)
    # trainer.train()
    # Load your test data into a DataFrame
    # df_test = pd.read_csv('path_to_your_test_data.csv')
    # results = trainer.test(df_test)
    # print(results.head())
