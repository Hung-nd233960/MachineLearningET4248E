from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class ImageSet:
    folder: str = ""
    scan_type: str = ""
    patient_id: str = ""
    num_images: int = 0
    image_list: List[str] = field(default_factory=list)
    image_index: int = 0
    irrelevance: int = 0
    disquality: int = 0
    opinion_basel: int = 1
    opinion_thalamus: int = 1
    patient_metadata: Dict[str, int] = field(default_factory=dict)
