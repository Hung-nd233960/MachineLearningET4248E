""" Load brain slice images and their labels from a CSV file """
from typing import Optional, Dict, Callable, Tuple
from torch.utils.data import Dataset
from PIL import Image
import pandas as pd

class ImageLabelDataset(Dataset):
    """
    A flexible PyTorch Dataset that loads images and labels from a pandas DataFrame.

    Args:
        df (pd.DataFrame): DataFrame containing at least 'path' and 'label' columns.
        transform (Optional[Callable], optional): A function/transform to apply to the images.
            Defaults to None.
        label_to_idx (Optional[Dict[str, int]], optional): Mapping from string labels to integer indices.
            If None, the mapping will be generated automatically from the DataFrame labels.

    Attributes:
        df (pd.DataFrame): The dataframe with image paths and labels.
        transform (Optional[Callable]): The image transform function.
        label_to_idx (Dict[str, int]): Mapping from labels to indices.

    Methods:
        __len__(): Returns the number of samples.
        __getitem__(idx): Loads and returns the image and its label index at the given index.
    """

    def __init__(
        self, 
        df: pd.DataFrame, 
        transform: Optional[Callable] = None, 
        label_to_idx: Optional[Dict[str, int]] = None
    ):
        self.df = df.reset_index(drop=True)
        self.transform = transform
        self.label_to_idx = label_to_idx or {
            label: i for i, label in enumerate(sorted(self.df['label'].unique()))
        }

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, idx: int) -> Tuple:
        img_path = self.df.loc[idx, 'path']
        label_str = self.df.loc[idx, 'label']
        label_idx = self.label_to_idx[label_str]

        image = Image.open(img_path).convert("RGB")
        if self.transform:
            image = self.transform(image)

        return image, label_idx
