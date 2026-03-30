import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
from selenium.webdriver.common.keys import Keys

# --- Setup Fixture ---
@pytest.fixture(scope="module")
def driver():
    """Sets up a headless Chrome browser for testing."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Runs in background without popping up a window
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    # Automatically fetch and install the correct ChromeDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Implicit wait tells Selenium to try for up to 10 seconds before failing to find an element
    driver.implicitly_wait(10)
    
    yield driver
    
    # Teardown: Close the browser after tests
    driver.quit()

# --- Helper Functions for Streamlit ---
def wait_for_app_to_load(driver):
    """Wait until Streamlit finishes its initial rendering."""
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.TAG_NAME, "h1"))
    )
    # Streamlit sometimes shows a "Running..." overlay. Wait a tiny bit for it to clear.
    time.sleep(2)

def get_input_by_label(driver, label_text):
    """Streamlit inputs are wrapped in divs with labels. This finds the input associated with a label."""
    xpath = f"//div[label[contains(., '{label_text}')]]//input"
    return driver.find_element(By.XPATH, xpath)

# --- Test Cases ---

def test_app_loads_successfully(driver):
    """Test 1: Does the app load and show the correct title?"""
    # 1. Navigate to the local Streamlit app
    driver.get("http://localhost:8501")
    wait_for_app_to_load(driver)

    # 2. Verify the title
    assert "Smart Markdown Optimizer" in driver.title
    
    # 3. Verify the main H1 header is on the page
    h1_tag = driver.find_element(By.TAG_NAME, "h1")
    assert "🛒 Smart Markdown Optimizer" in h1_tag.text

def test_add_new_product_flow(driver):
    """Test 2: Can a user navigate to the Add Product tab and submit the form?"""
    driver.get("http://localhost:8501")
    wait_for_app_to_load(driver)

    # 1. Click the "Add Product" tab
    add_product_tab = driver.find_element(By.XPATH, '//button[.//p[contains(text(), "Add Product")]]')
    add_product_tab.click()
    time.sleep(1) 

    # 2. Create a truly unique ID using the current timestamp
    # This prevents SQLite IntegrityErrors from previous test runs!
    unique_id = f"E2E-{int(time.time())}"

    # 3. Fill out the Product ID (the only field required by the if-statement)
    product_id_input = get_input_by_label(driver, "Product ID")
    product_id_input.send_keys(unique_id)
    time.sleep(0.5)

    # 4. Submit the form by mimicking a human hitting ENTER
    product_id_input.send_keys(Keys.RETURN)

    # 5. Verify the exact unique ID appears in the success message
    success_message = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), '{unique_id}')]"))
    )
    assert "added successfully" in success_message.text.lower()