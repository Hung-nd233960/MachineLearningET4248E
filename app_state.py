from typing import Optional, List, Dict

import pandas as pd
from utils.chooser import train_data_prepare, test_data_prepare
from utils.image_set import ImageSet

from set_chooser import SetChooser

CONFIG_PATH = "config.toml"


class AppState:
    def __init__(
        self,
        set_list: List[str] = None,
        config: Optional[Dict[str, str]] = None,
    ) -> None:
        if set_list is None:
            set_list = ["greeting", "config", "train", "test", "results", "settings", "registration"]

        paths: dict = config["paths"]
        self.data_path: str = paths["data_path"]
        self.scan_metadata_path: str = paths["scan_metadata_path"]
        self.image_metadata_path: str = paths["image_metadata_path"]
        self.patient_metadata_path: str = paths["patient_metadata_path"]    
        self.num_train_sets: int = 5
        self.num_test_sets: int = 5
        self.training_initialized: bool = False
        self.set_greeting()
        self.load_metadata(paths)
        # from utils.trainer import Trainer
        # self.model_trainer: Optional[Trainer] = None
        
    
    def set_greeting(self) -> None:
        """Set the current page to greeting."""
        self.logon: bool = False
        self.page: str = "greeting"
        self.set_index = 0
        self.current_set = None
        self.doctor_id: str = 0
        self.page: str = "greeting"
        self.set_index: int = 0
        self.current_set: Optional[ImageSet] = None
        self.set_chooser: Optional["SetChooser"] = None
        self.image_metadata: pd.DataFrame
        self.patient_metadata: pd.DataFrame
        self.scan_metadata: pd.DataFrame

    
    def set_image_set(self) -> None:
        """Initialize the current training and testing sets."""
        self.current_training_sets: List[ImageSet] = [ImageSet() for _ in range(self.num_train_sets)]
        self.current_testing_sets: List[ImageSet] = [ImageSet() for _ in range(self.num_test_sets)]

    def set_training_init(self) -> None:
        """Initialize the training sets and set the current set."""
        if not self.training_initialized:
            self.set_chooser = SetChooser(
                self.patient_metadata,
                self.scan_metadata,
                self.data_path,
                num_train_sets=self.num_train_sets,
                num_test_sets=self.num_test_sets
            )
            self.set_image_set()
            self.current_training_sets = self.set_chooser.choose_train_data(self.num_train_sets, "least_chosen")
            self.current_set = self.current_training_sets[self.set_index]
            self.training_initialized = True

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
        from utils.trainer import Trainer
        self.model_trainer: Trainer = Trainer(batch_size=batch_size, num_epochs=num_epochs, num_classes=num_classes)
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

if __name__ == "__main__":
    from utils.settings_loader import load_toml_config
    config = load_toml_config(CONFIG_PATH)
    app_state = AppState(config=config)
    set_chooser = SetChooser(app_state.patient_metadata,
                             app_state.scan_metadata,
                             app_state.data_path)
    train_sets = set_chooser.choose_train_data(sample_number=5, mode="least_chosen")
    print("Training Sets:")
    for s in train_sets:
        print(f"Patient ID: {s.patient_id}, Scan Type: {s.scan_type}, Number of Images: {s.num_images}")
        print(f"Image List: {s.image_list[:5]}...")  # Print first 5 images for brevity
        print(f"Metadata: {s.patient_metadata}")
        print(type(s.patient_metadata))