import pandas as pd
from scripts.utils_io import load_csv, save_csv
import os

def test_load_and_save_csv(tmp_path):
    test_data = pd.DataFrame({'A': [1, 2], 'B': [3, 4]})
    temp_file = tmp_path / "test.csv"
    
    save_csv(test_data, temp_file)
    loaded = load_csv(temp_file)
    
    assert loaded.equals(test_data)
    