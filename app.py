import streamlit as st
import pandas as pd
import sqlite3

# --- Helper Functions ---
def get_db_connection():
    # Connects to the SQLite DB. 
    # check_same_thread=False is needed for Streamlit's threading model.
    return sqlite3.connect('smart_markdown.db', check_same_thread=False)

def run_query(query, params=()):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
    conn.close()

# --- App Configuration ---
st.set_page_config(page_title="Smart Markdown Optimizer", layout="wide")
st.title("🛒 Smart Markdown Optimizer")

# --- Fetch Data ---
conn = get_db_connection()
# Load the forecast table to display
df_view = pd.read_sql("SELECT * FROM forecast_data", conn)
conn.close()

# --- UI Layout ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 View Prices", "➕ Add Product", "✏️ Update Price", "❌ Delete Product"])

# 1. READ: View the optimized prices
with tab1:
    st.header("Optimized Price Catalog")
    st.dataframe(
        df_view[['product_id', 'forecast_date', 'predicted_base_price', 'recommended_price', 'final_smart_price', 'markdown_pct']], 
        use_container_width=True,
        hide_index=True
    )

# 2. CREATE: Add a new product forecast
with tab2:
    st.header("Add New Product Forecast")
    with st.form("add_product_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            new_id = st.text_input("Product ID")
            new_date = st.date_input("Forecast Date")
            model = st.selectbox("Model Type", ["Standard", "Aggressive Markdown", "Conservative"])
            base_price = st.number_input("Predicted Base Price", min_value=0.0)
            safety = st.number_input("Safety Floor", min_value=0.0)
        with col2:
            hist_qty = st.number_input("Avg Historical Qty", min_value=0.0)
            demand_ratio = st.number_input("Demand Ratio", min_value=0.0)
            scaling = st.number_input("Scaling Factor", min_value=0.0)
            rec_price = st.number_input("Recommended Price", min_value=0.0)
            smart_price = st.number_input("Final Smart Price", min_value=0.0)
            markdown = st.number_input("Markdown %", min_value=0.0, max_value=100.0)
            
        submitted = st.form_submit_button("Add Product")
        
        if submitted and new_id:
            query = """
                INSERT INTO forecast_data 
                (product_id, forecast_date, forecasted_qty, model_type, predicted_base_price, safety_floor, avg_historical_qty, demand_ratio, scaling_factor, recommended_price, final_smart_price, markdown_pct)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            run_query(query, (new_id, new_date, 0, model, base_price, safety, hist_qty, demand_ratio, scaling, rec_price, smart_price, markdown))
            st.success(f"Product {new_id} added successfully! Refresh the page to see changes.")

# 3. UPDATE: Modify an existing price
with tab3:
    st.header("Update Final Smart Price")
    product_to_update = st.selectbox("Select Product ID to Update", df_view['product_id'].unique())
    
    if product_to_update:
        # Get current values to pre-fill the form
        current_data = df_view[df_view['product_id'] == product_to_update].iloc[0]
        
        with st.form("update_form"):
            new_smart_price = st.number_input("New Final Smart Price", value=float(current_data['final_smart_price']))
            new_markdown = st.number_input("New Markdown %", value=float(current_data['markdown_pct']))
            
            update_submit = st.form_submit_button("Update Price")
            
            if update_submit:
                query = "UPDATE forecast_data SET final_smart_price = ?, markdown_pct = ? WHERE product_id = ?"
                run_query(query, (new_smart_price, new_markdown, product_to_update))
                st.success(f"Updated Product {product_to_update}! Refresh to see changes.")

# 4. DELETE: Remove a product
with tab4:
    st.header("Delete Product")
    product_to_delete = st.selectbox("Select Product ID to Delete", df_view['product_id'].unique())
    
    with st.form("delete_form"):
        st.warning("This action cannot be undone.")
        delete_submit = st.form_submit_button("Delete Data")
        
        if delete_submit:
            run_query("DELETE FROM forecast_data WHERE product_id = ?", (product_to_delete,))
            st.success(f"Product {product_to_delete} deleted. Refresh the page.")