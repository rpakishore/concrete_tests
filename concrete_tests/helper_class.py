from dataclasses import dataclass
from datetime import datetime
import pandas as pd
from typing import Optional

@dataclass
class CompanyPatterns:
    name : str
    test_data: str
    specified_str: str
    set_data: str
    report_date: str
    air: str
    slump: str
    mix: str
    volume: str
    
@dataclass
class TestData:
    filename: Optional[str]
    filepath: Optional[str]
    company: Optional[str]
    report_date: Optional[datetime]
    data: Optional[pd.DataFrame]
    set_num: Optional[str]
    specimen: Optional[int]
    cast_date: Optional[datetime]
    transport_date: Optional[datetime]
    specified_str: Optional[int]
    specified_str_days: Optional[int]
    admixtures: Optional[list[str]]
    mix_num: Optional[str]
    load_vol: Optional[float]
    slump: Optional[int]
    specified_slump: Optional[list[int]]
    air: Optional[float]
    specified_air: Optional[list[float]]
    location_comments: Optional[list[str]]
    other_comments: Optional[list[str]]
    errors: Optional[pd.DataFrame]
    