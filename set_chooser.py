import os
from typing import List
import pandas as pd
from utils.chooser import choose_train_data, choose_test_data
from utils.image_set import ImageSet

class SetChooser:
    """
    A class to handle the selection of training and testing data sets."""
    def __init__(self,
                 patient_metadata: pd.DataFrame,
                 scan_metadata: pd.DataFrame,
                 data_path: str,
                 num_train_sets: int = 5,
                 num_test_sets: int = 5) -> None:
        if num_train_sets < 1 or num_test_sets < 1:
            raise ValueError("Number of training and testing sets must be at least 1.")

        self.patient_metadata = patient_metadata
        self.scan_metadata = scan_metadata
        self.num_train_sets = num_train_sets
        self.num_test_sets = num_test_sets
        self.data_path = data_path

    def dataframe_to_set(self, chosen_data: pd.DataFrame) -> List[ImageSet]:
        """
        Convert the chosen training data to a list of ImageSet objects. Now only works for training data.
        """
        image_sets = []
        for _, row in chosen_data.iterrows():
            folder_path = os.path.join(self.data_path, str(row['patient_id']), str(row['scan_type']))
            temp_list = os.listdir(folder_path)
            temp_list.sort()  # Sort the list of images
            s = ImageSet(folder = folder_path,
                         scan_type = str(row['scan_type']),
                         patient_id = str(row['patient_id']),
                         num_images = int(row['num_images']),
                         image_list = temp_list,
                         image_index = 0,
                         irrelevance = int(row['true_irrelevance']),
                         disquality = int(row['true_disquality']),
                         patient_metadata = (self.patient_metadata[
                         self.patient_metadata['patient_id'] == str(row['patient_id'])].to_dict(orient='records'))[0])
            # [0] to get the first (and only) record, since we expect one patient_id per row
            image_sets.append(s)
        return image_sets
    
    def choose_train_data(self, sample_number: int = 5, mode: str = "least_chosen") -> List[ImageSet]:
        """
        Choose a set of training data based on the specified mode.
        
        Args:
            sample_number (int): Number of training sets to choose.
            mode (str): Mode for choosing the training data. Options are "least_chosen" or "random".
        
        Returns:
            List[ImageSet]: List of chosen training entries as ImageSet objects.
        """
        chosen_data = choose_train_data(self.scan_metadata, sample_number, mode)
        return self.dataframe_to_set(chosen_data)
    
    def choose_test_data(self, sample_number: int = 5, mode: str = "least_chosen") -> List[ImageSet]:
        """
        Choose a set of testing data based on the specified mode.
        
        Args:
            sample_number (int): Number of testing sets to choose.
            mode (str): Mode for choosing the testing data. Options are "least_chosen" or "random".
        
        Returns:
            List[ImageSet]: List of chosen testing entries as ImageSet objects.
        """
        chosen_data = choose_test_data(self.scan_metadata, sample_number, mode)
        return self.dataframe_to_set(chosen_data)
    