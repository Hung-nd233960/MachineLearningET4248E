from typing import Optional, List, Dict
import os
import pandas as pd
from utils.settings_loader import load_toml_config
from utils.chooser import choose_train_data, choose_test_data, train_data_prepare, test_data_prepare
from utils.image_set import ImageSet
from utils.trainer import Trainer


CONFIG_PATH = "config.toml"


class AppState:
    def __init__(
        self,
        doctor_id: int = 1,
        set_list: List[str] = None,
    ) -> None:
        if set_list is None:
            set_list = ["greeting", "config", "train", "test"]

        self.doctor_id: int = doctor_id
        self.page: str = "greeting"
        self.set_index: int = 0
        self.current_set: Optional[ImageSet] = None

        config: dict = load_toml_config(CONFIG_PATH)
        paths: dict = config["paths"]

        self.data_path: str = paths["data_path"]
        self.image_metadata: pd.DataFrame
        self.patient_metadata: pd.DataFrame
        self.scan_metadata: pd.DataFrame
        self.scan_metadata_path: str = paths["scan_metadata_path"]
        self.image_metadata_path: str = paths["image_metadata_path"]
        self.patient_metadata_path: str = paths["patient_metadata_path"]    
        self.load_metadata(paths)

        self.num_train_sets: int = 5
        self.num_test_sets: int = 5
        self.current_training_sets: List[ImageSet] = [ImageSet() for _ in range(self.num_train_sets)]
        self.current_testing_sets: List[ImageSet] = [ImageSet() for _ in range(self.num_test_sets)]
        self.set_chooser: Optional["SetChooser"] = None
        self.model_trainer: Optional[Trainer] = None

    def load_metadata(self, paths: Dict[str, str]) -> None:
        """
        Load metadata from CSV files."""
        self.image_metadata = pd.read_csv(paths["image_metadata_path"])
        self.patient_metadata = pd.read_csv(paths["patient_metadata_path"])
        self.scan_metadata = pd.read_csv(paths["scan_metadata_path"])

    def update_scan_metadata(self, update_data_set: List[ImageSet], export_csv: bool = True) -> None:
        """
        Update the scan metadata DataFrame with new data.
        
        Args:
            scan_metadata (pd.DataFrame): New scan metadata DataFrame.
        """
        for s in update_data_set:
            condition = (self.scan_metadata["patient_id"] == s.patient_id) & (self.scan_metadata["scan_type"] == s.scan_type)
            self.scan_metadata.loc[condition, "num_ratings"] += 1
            self.scan_metadata.loc[condition, ["true_irrelevance", "true_disquality"]] = [s.irrelevance, s.disquality]
            self.scan_metadata.loc[condition, f"opinion_basel_doctor{self.doctor_id}"] = s.opinion_basel
            self.scan_metadata.loc[condition, f"opinion_thalamus_doctor{self.doctor_id}"] = s.opinion_thalamus
            self.scan_metadata.loc[condition, f"opinion_irrelevance_doctor{self.doctor_id}"] = s.irrelevance
            self.scan_metadata.loc[condition, f"opinion_quality_doctor{self.doctor_id}"] = s.disquality
        if export_csv:
            self.scan_metadata.to_csv(self.scan_metadata_path, index=False)

    def init_trainer(self, batch_size: int = 32, num_epochs: int = 10, num_classes: int = 3) -> None:
        """
        Initialize the trainer with the specified parameters.
        
        Args:
            batch_size (int): Batch size for training.
            num_epochs (int): Number of epochs for training.
            num_classes (int): Number of classes for classification.
        """
        self.model_trainer = Trainer(batch_size=batch_size, num_epochs=num_epochs, num_classes=num_classes)
        training_data_df = self.set_chooser.choose_train_data(self.num_train_sets, "least_chosen")
        training_data_image_paths = train_data_prepare(self.data_path, training_data_df)
        self.model_trainer.load_training_data(training_data_image_paths)
    
    def train_model(self) -> None:
        """Train the model using the initialized trainer."""
        self.model_trainer.train()
    
    def test_model_prepare(self) -> pd.DataFrame:
        """
        Prepare the test data for evaluation.
        
        Returns:
            pd.DataFrame: DataFrame with test data paths and labels.
        """
        test_data = self.set_chooser.choose_test_data(self.num_test_sets, "least_chosen")
        test_df = test_data_prepare(self.data_path, test_data)
        return test_df
    
    def test_model(self, test_data: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare the test data for evaluation.
        
        Args:
            test_data (pd.DataFrame): DataFrame with a 'path' column for test image paths.
        
        Returns:
            pd.DataFrame: DataFrame with predictions.
        """
        return self.model_trainer.test(test_data)

    
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
            s = ImageSet(folder = folder_path,
                         scan_type = str(row['scan_type']),
                         patient_id = str(row['patient_id']),
                         num_images = int(row['num_images']),
                         image_list = os.listdir(folder_path),
                         image_index = 0,
                         irrelevance = int(row['true_irrelevance']),
                         disquality = int(row['true_disquality']),
                         patient_metadata= self.patient_metadata[
                         self.patient_metadata['patient_id'] == str(row['patient_id'])].to_dict(orient='records'))
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

        

if __name__ == "__main__":
    app_state = AppState()
    set_chooser = SetChooser(app_state.patient_metadata,
                             app_state.scan_metadata,
                             app_state.data_path)
    train_sets = set_chooser.choose_train_data(sample_number=5, mode="least_chosen")
    print("Training Sets:")
    for s in train_sets:
        print(f"Patient ID: {s.patient_id}, Scan Type: {s.scan_type}, Number of Images: {s.num_images}")