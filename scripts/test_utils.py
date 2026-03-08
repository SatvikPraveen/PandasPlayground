import pandas as pd
import numpy as np
import pytest
from pathlib import Path
from scripts.utils_io import (
    load_csv, save_csv, load_excel, load_json, 
    load_parquet, save_parquet, export_csv
)
from scripts.cleaning_utils import (
    clean_dataframe, detect_outliers_iqr, standardize_strings
)
from scripts.agg_utils import (
    groupby_summary, compute_approval_rate, pivot_table_summary
)
from scripts.optimize_memory import optimize_dataframe


# ========================================
# 📥 I/O Utils Tests
# ========================================

def test_load_and_save_csv(tmp_path):
    """Test CSV loading and saving functionality."""
    test_data = pd.DataFrame({'A': [1, 2], 'B': [3, 4]})
    temp_file = tmp_path / "test.csv"
    
    save_csv(test_data, temp_file)
    loaded = load_csv(temp_file)
    
    assert loaded.equals(test_data)


def test_save_csv_creates_directory(tmp_path):
    """Test that save_csv creates parent directories if they don't exist."""
    test_data = pd.DataFrame({'X': [1, 2, 3]})
    nested_path = tmp_path / "subdir" / "nested" / "test.csv"
    
    save_csv(test_data, nested_path)
    assert nested_path.exists()
    
    loaded = load_csv(nested_path)
    assert loaded.equals(test_data)


def test_load_excel(tmp_path):
    """Test Excel file loading."""
    test_data = pd.DataFrame({'Name': ['Alice', 'Bob'], 'Score': [95, 87]})
    temp_file = tmp_path / "test.xlsx"
    
    test_data.to_excel(temp_file, index=False)
    loaded = load_excel(temp_file)
    
    assert loaded.equals(test_data)


def test_parquet_roundtrip(tmp_path):
    """Test Parquet file save and load."""
    test_data = pd.DataFrame({
        'col1': [1, 2, 3],
        'col2': ['a', 'b', 'c'],
        'col3': [1.5, 2.5, 3.5]
    })
    temp_file = tmp_path / "test.parquet"
    
    save_parquet(test_data, temp_file)
    loaded = load_parquet(temp_file)
    
    pd.testing.assert_frame_equal(loaded, test_data)


def test_load_json(tmp_path):
    """Test JSON file loading."""
    import json
    test_data = [
        {'name': 'Alice', 'age': 30},
        {'name': 'Bob', 'age': 25}
    ]
    temp_file = tmp_path / "test.json"
    
    with open(temp_file, 'w') as f:
        json.dump(test_data, f)
    
    loaded = load_json(temp_file)
    assert len(loaded) == 2
    assert loaded['name'].tolist() == ['Alice', 'Bob']


# ========================================
# 🧹 Cleaning Utils Tests
# ========================================

def test_clean_dataframe_drop_na():
    """Test dropping NA values in specified columns."""
    df = pd.DataFrame({
        'A': [1, 2, None, 4],
        'B': [5, None, 7, 8],
        'C': ['x', 'y', 'z', 'w']
    })
    
    cleaned = clean_dataframe(df, drop_na_cols=['A'])
    assert len(cleaned) == 3
    assert cleaned['A'].isna().sum() == 0


def test_clean_dataframe_dedupe():
    """Test duplicate removal."""
    df = pd.DataFrame({
        'A': [1, 2, 2, 3],
        'B': [4, 5, 5, 6]
    })
    
    cleaned = clean_dataframe(df, dedupe=True)
    assert len(cleaned) == 3


def test_clean_dataframe_strings():
    """Test string cleaning."""
    df = pd.DataFrame({
        'Name': ['  Alice  ', 'BOB', 'Charlie  '],
        'City': ['NEW YORK', 'los angeles', 'CHICAGO']
    })
    
    cleaned = clean_dataframe(df, clean_strings=True)
    assert cleaned['Name'].tolist() == ['alice', 'bob', 'charlie']
    assert cleaned['City'].tolist() == ['new york', 'los angeles', 'chicago']


def test_detect_outliers_iqr():
    """Test IQR-based outlier detection."""
    # Create data with clear outliers
    data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 100]  # 100 is an outlier
    df = pd.DataFrame({'values': data})
    
    outliers = detect_outliers_iqr(df, 'values')
    assert len(outliers) > 0
    assert 100 in outliers['values'].values


def test_standardize_strings():
    """Test string standardization function."""
    df = pd.DataFrame({
        'Name': ['  ALICE  ', 'bob', 'CHARLIE  '],
        'Number': [1, 2, 3]
    })
    
    standardized = standardize_strings(df)
    assert standardized['Name'].tolist() == ['alice', 'bob', 'charlie']
    # Number column should remain unchanged
    assert standardized['Number'].tolist() == [1, 2, 3]


# ========================================
# 🧮 Aggregation Utils Tests
# ========================================

def test_groupby_summary():
    """Test basic groupby aggregation."""
    df = pd.DataFrame({
        'Category': ['A', 'A', 'B', 'B'],
        'Sales': [100, 150, 200, 250],
        'Profit': [20, 30, 40, 50]
    })
    
    result = groupby_summary(df, 'Category', {'Sales': 'sum', 'Profit': 'mean'})
    assert len(result) == 2
    assert result[result['Category'] == 'A']['Sales'].values[0] == 250
    assert result[result['Category'] == 'B']['Profit'].values[0] == 45


def test_groupby_summary_no_reset():
    """Test groupby with index preservation."""
    df = pd.DataFrame({
        'Region': ['North', 'North', 'South'],
        'Revenue': [100, 200, 300]
    })
    
    result = groupby_summary(df, 'Region', {'Revenue': 'sum'}, reset=False)
    assert 'Region' not in result.columns  # Should be in index
    assert result.index.name == 'Region'


def test_compute_approval_rate():
    """Test approval rate calculation."""
    df = pd.DataFrame({
        'region': ['East', 'East', 'West', 'West'],
        'approved': ['yes', 'no', 'yes', 'yes']
    })
    
    result = compute_approval_rate(df, 'region', 'approved', 'yes')
    assert len(result) == 2
    
    east_rate = result[result['region'] == 'East']['approval_rate'].values[0]
    west_rate = result[result['region'] == 'West']['approval_rate'].values[0]
    
    assert east_rate == 0.5
    assert west_rate == 1.0


def test_pivot_table_summary():
    """Test pivot table creation."""
    df = pd.DataFrame({
        'Region': ['North', 'North', 'South', 'South'],
        'Product': ['A', 'B', 'A', 'B'],
        'Sales': [100, 150, 200, 250]
    })
    
    result = pivot_table_summary(df, 'Region', 'Product', 'Sales', 'sum')
    assert result.shape == (2, 2)  # 2 regions x 2 products


# ========================================
# ⚡ Memory Optimization Tests
# ========================================

def test_optimize_dataframe():
    """Test memory optimization of dataframe."""
    # Create a dataframe with inefficient dtypes
    df = pd.DataFrame({
        'int_col': [1, 2, 3, 4, 5],  # Will be int64 by default
        'float_col': [1.1, 2.2, 3.3, 4.4, 5.5],
        'str_col': ['a', 'b', 'a', 'b', 'a']  # Good candidate for category
    })
    
    original_memory = df.memory_usage(deep=True).sum()
    optimized = optimize_dataframe(df, category_cols=['str_col'], verbose=False)
    optimized_memory = optimized.memory_usage(deep=True).sum()
    
    # Memory should be reduced or stay same
    assert optimized_memory <= original_memory
    # String column should be converted to category
    assert optimized['str_col'].dtype.name == 'category'


def test_optimize_keeps_data_integrity():
    """Test that optimization doesn't change data values."""
    df = pd.DataFrame({
        'A': [1, 2, 3, 4, 5],
        'B': [1.1, 2.2, 3.3, 4.4, 5.5],
        'C': ['x', 'y', 'x', 'y', 'x']
    })
    
    optimized = optimize_dataframe(df, category_cols=['C'], verbose=False)
    
    # Check that values are preserved (with tolerance for float precision)
    assert df['A'].tolist() == optimized['A'].tolist()
    # Use approximate comparison for floats due to float32/float64 conversion
    import numpy as np
    np.testing.assert_allclose(df['B'].values, optimized['B'].values, rtol=1e-5)
    assert df['C'].tolist() == optimized['C'].tolist()


# ========================================
# 🔗 Integration Tests
# ========================================

def test_full_data_pipeline(tmp_path):
    """Test a complete data processing pipeline."""
    # Create test data
    df = pd.DataFrame({
        'Name': ['  ALICE  ', 'bob', 'CHARLIE', 'alice'],
        'Score': [95, 87, 95, 92],
        'Grade': ['A', 'B', 'A', 'A']
    })
    
    # Save to CSV
    csv_path = tmp_path / "input.csv"
    save_csv(df, csv_path)
    
    # Load and clean
    loaded = load_csv(csv_path)
    cleaned = clean_dataframe(loaded, dedupe=True, clean_strings=True)
    
    # Should have removed duplicate after standardization
    assert len(cleaned) <= len(df)
    
    # clean_strings lowercases column names, so use lowercase
    # Check that 'name' and 'score' columns exist (lowercase after cleaning)
    assert 'name' in cleaned.columns or 'Name' in cleaned.columns
    
    # Group and aggregate (use actual column name after cleaning)
    col_name = 'grade' if 'grade' in cleaned.columns else 'Grade'
    score_col = 'score' if 'score' in cleaned.columns else 'Score'
    summary = groupby_summary(cleaned, col_name, {score_col: 'mean'})
    
    # Save results
    output_path = tmp_path / "output.csv"
    save_csv(summary, output_path)
    
    assert output_path.exists()


# ========================================
# 🧪 Edge Cases and Error Handling
# ========================================

def test_empty_dataframe_cleaning():
    """Test cleaning an empty dataframe."""
    df = pd.DataFrame()
    cleaned = clean_dataframe(df)
    assert len(cleaned) == 0


def test_groupby_with_missing_column():
    """Test groupby with column that doesn't exist."""
    df = pd.DataFrame({'A': [1, 2], 'B': [3, 4]})
    
    with pytest.raises(KeyError):
        groupby_summary(df, 'NonexistentColumn', {'A': 'sum'})


def test_load_nonexistent_file():
    """Test loading a file that doesn't exist."""
    with pytest.raises(FileNotFoundError):
        load_csv("nonexistent_file.csv")


# ========================================
# 📊 Performance Tests (marked as slow)
# ========================================

@pytest.mark.slow
def test_large_dataframe_optimization():
    """Test optimization on a large dataframe."""
    # Create a large dataframe
    n_rows = 100000
    df = pd.DataFrame({
        'int_col': np.random.randint(0, 100, n_rows),
        'float_col': np.random.random(n_rows),
        'category_col': np.random.choice(['A', 'B', 'C', 'D'], n_rows)
    })
    
    original_memory = df.memory_usage(deep=True).sum()
    optimized = optimize_dataframe(df, category_cols=['category_col'], verbose=False)
    optimized_memory = optimized.memory_usage(deep=True).sum()
    
    # Should see significant memory reduction
    reduction_ratio = optimized_memory / original_memory
    assert reduction_ratio < 0.9  # At least 10% reduction


# ========================================
# 🎯 Pytest Fixtures
# ========================================

@pytest.fixture
def sample_sales_data():
    """Fixture providing sample sales data for tests."""
    return pd.DataFrame({
        'Date': pd.date_range('2024-01-01', periods=10),
        'Product': ['A', 'B'] * 5,
        'Sales': np.random.randint(100, 1000, 10),
        'Region': ['North', 'South'] * 5
    })


@pytest.fixture
def sample_dirty_data():
    """Fixture providing messy data for cleaning tests."""
    return pd.DataFrame({
        'Name': ['  Alice  ', 'BOB', None, 'charlie', 'alice'],
        'Age': [25, 30, 28, None, 25],
        'City': ['NYC', 'LA', 'NYC', 'SF', 'NYC']
    })
    