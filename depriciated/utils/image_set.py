from dataclasses import dataclass, field
from typing import List, Dict
from git import Optional
import pandas as pd


@dataclass
class ImageSet:
    folder: str = ""
    scan_type: str = ""
    patient_id: str = ""
    num_images: int = 0
    image_list: List[str] = field(default_factory=list)
    labeler_opinion: Optional[pd.DataFrame] = None
    image_index_1: int = 0
    image_index_2: int = 0
    irrelevance: int = 0
    disquality: int = 0
    basel_image: str = ""
    corona_image: str = ""
    basel_score: int = 0
    corona_score: int = 0
    patient_metadata: Dict[str, int] = field(default_factory=dict)
