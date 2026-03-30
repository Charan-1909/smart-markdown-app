import pytest
import sqlite3
import pandas as pd
import app  # Imports your Streamlit code (app.py)

# --- Fixtures ---

@pytest.fixture
def test_db(tmp_path, monkeypatch):
    """
    Creates a temporary SQLite database with the required schema,
    and forces app.py to use this temporary DB instead of the real one.
    """
    # Create a temporary file path for the test database
    db_path = tmp_path / "test_smart_markdown.db"
    
    # Initialize the database schema
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS forecast_data (
            product_id TEXT PRIMARY KEY,
            forecast_date TEXT,
            forecasted_qty REAL,
            model_type TEXT,
            predicted_base_price REAL,
            safety_floor REAL,
            avg_historical_qty REAL,
            demand_ratio REAL,
            scaling_factor REAL,
            recommended_price REAL,
            final_smart_price REAL,
            markdown_pct REAL
        )
    ''')
    conn.commit()
    conn.close()

    # Mock the get_db_connection function in app.py to return our test DB
    def mock_get_db_connection():
        return sqlite3.connect(db_path, check_same_thread=False)

    monkeypatch.setattr(app, "get_db_connection", mock_get_db_connection)
    
    # Return the path in case a test needs it, though the mock handles the routing
    return db_path


# --- Test Cases ---

def test_insert_product(test_db):
    """Test the CREATE functionality (run_query INSERT)."""
    
    # 1. Execute the insert query using the app's helper function
    query = """
        INSERT INTO forecast_data 
        (product_id, forecast_date, forecasted_qty, model_type, predicted_base_price, 
         safety_floor, avg_historical_qty, demand_ratio, scaling_factor, 
         recommended_price, final_smart_price, markdown_pct)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    app.run_query(query, ('PROD-001', '2023-12-01', 0, 'Standard', 100.0, 80.0, 50, 1.2, 1.0, 95.0, 90.0, 10.0))

    # 2. Verify the data was actually inserted
    conn = app.get_db_connection()
    df = pd.read_sql("SELECT * FROM forecast_data WHERE product_id = 'PROD-001'", conn)
    conn.close()

    assert not df.empty, "Data was not inserted into the database."
    assert df.iloc[0]['product_id'] == 'PROD-001'
    assert df.iloc[0]['model_type'] == 'Standard'
    assert df.iloc[0]['final_smart_price'] == 90.0

def test_update_product(test_db):
    """Test the UPDATE functionality."""
    
    # 1. Setup: Insert initial data
    setup_query = """
        INSERT INTO forecast_data (product_id, final_smart_price, markdown_pct)
        VALUES (?, ?, ?)
    """
    app.run_query(setup_query, ('PROD-002', 50.0, 5.0))

    # 2. Execute update
    update_query = "UPDATE forecast_data SET final_smart_price = ?, markdown_pct = ? WHERE product_id = ?"
    app.run_query(update_query, (40.0, 20.0, 'PROD-002'))

    # 3. Verify update
    conn = app.get_db_connection()
    df = pd.read_sql("SELECT final_smart_price, markdown_pct FROM forecast_data WHERE product_id = 'PROD-002'", conn)
    conn.close()

    assert df.iloc[0]['final_smart_price'] == 40.0
    assert df.iloc[0]['markdown_pct'] == 20.0

def test_delete_product(test_db):
    """Test the DELETE functionality."""
    
    # 1. Setup: Insert initial data
    app.run_query("INSERT INTO forecast_data (product_id) VALUES (?)", ('PROD-003',))

    # 2. Verify it exists before deleting
    conn = app.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM forecast_data WHERE product_id = 'PROD-003'")
    assert cursor.fetchone()[0] == 1

    # 3. Execute delete
    app.run_query("DELETE FROM forecast_data WHERE product_id = ?", ('PROD-003',))

    # 4. Verify it was deleted
    cursor.execute("SELECT COUNT(*) FROM forecast_data WHERE product_id = 'PROD-003'")
    assert cursor.fetchone()[0] == 0
    conn.close()

def test_read_data_view(test_db):
    """Test the READ functionality used by the Streamlit View tab."""
    
    # Insert multiple rows
    app.run_query("INSERT INTO forecast_data (product_id, final_smart_price) VALUES (?, ?)", ('PROD-A', 10.0))
    app.run_query("INSERT INTO forecast_data (product_id, final_smart_price) VALUES (?, ?)", ('PROD-B', 20.0))

    # Simulate the read logic from Tab 1
    conn = app.get_db_connection()
    df_view = pd.read_sql("SELECT * FROM forecast_data", conn)
    conn.close()

    # Assertions
    assert len(df_view) == 2
    assert 'PROD-A' in df_view['product_id'].values
    assert 'PROD-B' in df_view['product_id'].values