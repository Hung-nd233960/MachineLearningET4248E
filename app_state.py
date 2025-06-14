from typing import Optional, List, Dict
from enum import Enum, auto
import pandas as pd
from utils.chooser import train_data_prepare, test_data_prepare
from utils.credential_manager import CredentialManager
from utils.image_set import ImageSet

from set_chooser import SetChooser

CONFIG_PATH = "config.toml"


class Page(Enum):
    GREETING = auto()
    REGISTRATION = auto()
    CONFIGURATION = auto()
    DASHBOARD = auto()
    ANNOTATION = auto()
    VERIFICATION = auto()
    TESTING = auto()


VALID_TRANSITIONS = {
    Page.GREETING: [Page.REGISTRATION, Page.CONFIGURATION, Page.DASHBOARD],
    Page.DASHBOARD: [Page.ANNOTATION],
    Page.REGISTRATION: [Page.GREETING],
    Page.CONFIGURATION: [Page.ANNOTATION],
    Page.ANNOTATION: [Page.GREETING],
    Page.TESTING: [Page.GREETING],
}


def can_transition(from_page: Page, to_page: Page, testing: bool = False) -> bool:
    return to_page in VALID_TRANSITIONS.get(from_page, []) and not testing


class AppState:
    def __init__(
        self,
        set_list: List[str] = None,
        config: Optional[Dict[str, str]] = None,
    ) -> None:
        if set_list is None:
            set_list = [
                "greeting",
                "config",
                "train",
                "test",
                "results",
                "settings",
                "registration",
            ]

        paths: dict = config["paths"]
        self.data_path: str = paths["data_path"]
        self.scan_metadata_path: str = paths["scan_metadata_path"]
        self.image_metadata_path: str = paths["image_metadata_path"]
        self.patient_metadata_path: str = paths["patient_metadata_path"]
        self.num_train_sets: int = 5
        self.num_test_sets: int = 5
        self.annotation_initialized: bool = False
        self.set_greeting()
        self.load_metadata(paths)
        self.dialog: str = ""
        self.testing_initialized: bool = False
        # from utils.trainer import Trainer
        # self.model_trainer: Optional[Trainer] = None

    def set_credential_manager(self, credential_manager: CredentialManager) -> None:
        """Set the credential manager for the application."""
        self.credential_manager = credential_manager

    def set_greeting(self) -> None:
        """Set the current page to greeting."""
        self.logon: bool = False
        self.page: Page = Page.GREETING
        self.current_set = None
        self.doctor_id: str = 0
        self.doctor_role: str = "verifier"
        self.set_index: int = 0
        self.current_set: Optional[ImageSet] = None
        self.set_chooser: Optional[SetChooser] = None
        self.image_metadata: pd.DataFrame
        self.patient_metadata: pd.DataFrame
        self.scan_metadata: pd.DataFrame
        self.training_initialized: bool = False
        self.test_result: Optional[pd.DataFrame] = None

    def set_image_set(self) -> None:
        """Initialize the current annotation and testing sets."""
        self.current_annotation_sets: List[ImageSet] = [
            ImageSet() for _ in range(self.num_train_sets)
        ]
        self.current_testing_sets: List[ImageSet] = [
            ImageSet() for _ in range(self.num_test_sets)
        ]

    def set_annotation_init(self) -> None:
        """Initialize the annotation sets and set the current set."""

        if not self.annotation_initialized:
            self.set_chooser = SetChooser(
                self.patient_metadata,
                self.scan_metadata,
                self.credential_manager,
                self.data_path,
                num_train_sets=self.num_train_sets,
                num_test_sets=self.num_test_sets,
            )

            self.current_annotation_sets = self.set_chooser.dataframe_to_set(
                self.current_annotation_sets
            )
            self.num_train_sets = len(self.current_annotation_sets)
            # self.current_annotation_sets = self.set_chooser.choose_annotation_data(self.num_train_sets, "least_chosen")
            self.current_set = self.current_annotation_sets[self.set_index]
            self.annotation_initialized = True

    def set_verification_init(self) -> None:
        """Initialize the verification sets."""

        if not self.annotation_initialized:
            self.set_chooser = SetChooser(
                self.patient_metadata,
                self.scan_metadata,
                self.credential_manager,
                self.data_path,
                num_train_sets=self.num_train_sets,
                num_test_sets=self.num_test_sets,
            )

            self.current_annotation_sets = self.set_chooser.dataframe_to_set(
                self.current_annotation_sets
            )
            self.num_train_sets = len(self.current_annotation_sets)
            # self.current_annotation_sets = self.set_chooser.choose_annotation_data(self.num_train_sets, "override")
            self.current_set = self.current_annotation_sets[self.set_index]
            self.annotation_initialized = True

    def set_test_init(self) -> None:
        test_data = self.set_chooser.choose_test_data(
            self.num_test_sets, "least_chosen"
        )
        self.current_testing_sets = self.set_chooser.dataframe_to_set(test_data)
        self.test_dataframe = self.test_model_prepare(test_data)
        self.set_index = 0

    def load_metadata(self, paths: Dict[str, str]) -> None:
        """
        Load metadata from CSV files."""
        self.image_metadata = pd.read_csv(paths["image_metadata_path"])
        self.patient_metadata = pd.read_csv(paths["patient_metadata_path"])
        self.scan_metadata = pd.read_csv(paths["scan_metadata_path"])

    def update_scan_metadata(
        self, update_data_set: List[ImageSet], export_csv: bool = True
    ) -> None:
        """
        Update the scan metadata DataFrame with new data.

        Args:
            scan_metadata (pd.DataFrame): New scan metadata DataFrame.
        """
        for s in update_data_set:
            condition = (self.scan_metadata["patient_id"] == s.patient_id) & (
                self.scan_metadata["scan_type"] == s.scan_type
            )
            self.scan_metadata.loc[condition, "num_ratings"] += 1
            self.scan_metadata.loc[
                condition, ["true_irrelevance", "true_disquality"]
            ] = [s.irrelevance, s.disquality]
            self.scan_metadata.loc[
                condition, f"opinion_basel_{self.doctor_id}_{self.doctor_role}"
            ] = s.opinion_basel
            self.scan_metadata.loc[
                condition, f"opinion_corona_{self.doctor_id}_{self.doctor_role}"
            ] = s.opinion_corona
            self.scan_metadata.loc[
                condition, f"opinion_irrelevance_{self.doctor_id}_{self.doctor_role}"
            ] = s.irrelevance
            self.scan_metadata.loc[
                condition, f"opinion_quality_{self.doctor_id}_{self.doctor_role}"
            ] = s.disquality

        if export_csv:
            self.scan_metadata.to_csv(self.scan_metadata_path, index=False)

    def init_trainer(
        self, batch_size: int = 32, num_epochs: int = 1, num_classes: int = 3
    ) -> None:
        """
        Initialize the trainer with the specified parameters.

        Args:
            batch_size (int): Batch size for training.
            num_epochs (int): Number of epochs for training.
            num_classes (int): Number of classes for classification.
        """
        from trainer.trainer import Trainer

        self.model_trainer: Trainer = Trainer(
            batch_size=batch_size, num_epochs=num_epochs, num_classes=num_classes
        )
        training_data_df = self.set_chooser.choose_train_data(self.scan_metadata)
        training_data_image_paths = train_data_prepare(self.data_path, training_data_df)
        self.model_trainer.load_training_data(training_data_image_paths)

    def train_model(self) -> None:
        """Train the model using the initialized trainer."""
        self.model_trainer.train()

    def choose_test_data(self) -> pd.DataFrame:
        """
        Choose the test data based on the set chooser's configuration.

        Returns:
            pd.DataFrame: DataFrame with test data paths and labels.
        """
        test_data = self.set_chooser.choose_test_data(
            self.num_test_sets, "least_chosen"
        )
        return test_data

    def test_model_prepare(self, test_data: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare the test data for evaluation.

        Returns:
            pd.DataFrame: DataFrame with test data paths and labels.
        """
        test_df = test_data_prepare(self.data_path, test_data)
        return test_df

    def test_data_set(self, test_data: pd.DataFrame) -> List[ImageSet]:
        """
        Convert the test data DataFrame to a list of ImageSet objects.

        Args:
            test_data (pd.DataFrame): DataFrame with test data paths and labels.

        Returns:
            List[ImageSet]: List of ImageSet objects for testing.
        """
        return self.set_chooser.dataframe_to_set(test_data)

    def test_model(self, export_csv: bool = True) -> None:
        """
        Prepare the test data for evaluation.

        Args:
            export_csv (bool): Whether to export the test results to a CSV file.
        Returns:
            None.
        """
        self.test_result = self.model_trainer.test(self.test_dataframe)
        if export_csv:
            self.test_result.to_csv("test_results.csv", index=False)
        self.testing_initialized = True
