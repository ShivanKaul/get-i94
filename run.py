import time
import json
import re
import base64
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException

options = Options()

# Paths
# binary_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
binary_path = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
chrome_driver_path = "/opt/homebrew/bin/chromedriver"

options.add_argument("--headless=new") # For headless mode
options.binary_location = binary_path
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")

# To change the User Agent: the CBP site appears to block headless user agents.
options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 \
(KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36")

service = Service(chrome_driver_path)
driver = webdriver.Chrome(service=service, options=options)

# Store your i94 details locally in a file called `i94_config.json`
# I've provided a sample file, you'll need to change and rename it.
# !!! DO NOT COMMIT THIS FILE INTO SOURCE CONTROL OR UPLOAD !!!
# The .gitignore ignores all *.json files.
def validate_i94_config(config_data):
    required_fields = ["firstName", "lastName", "birthDate", "countryCode", "documentNumber"]
    
    # 1) Ensure all required fields exist
    for field in required_fields:
        if field not in config_data:
            raise ValueError(f"Missing required field '{field}' in i94_config.json")

    # 2) Validate date format: MM/DD/YYYY
    dob = config_data["birthDate"]
    pattern = r"^\d{2}/\d{2}/\d{4}$"  # Quick and dirty check
    if not re.match(pattern, dob):
        raise ValueError(f"birthDate '{dob}' does not match MM/DD/YYYY.")
    try:
        datetime.strptime(dob, "%m/%d/%Y")
    except ValueError:
        raise ValueError(f"birthDate '{dob}' is invalid or out of range.")
    
    # 3) Check doc number length or format.
    if len(config_data["documentNumber"]) < 2:
        raise ValueError("documentNumber too short (must be at least 2 characters).")
    print("i94_config.json fields validated successfully!")

try:
    with open("i94_config.json", "r") as f:
        i94_data = json.load(f)
    validate_i94_config(i94_data)

    driver.get("https://i94.cbp.dhs.gov/search/recent-search")
    user_agent = driver.execute_script("return navigator.userAgent;")
    print("Current User Agent:", user_agent)

    # Attempt to handle the ToS modal.
    try:
        dialog_content = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "mat-dialog-content.mat-mdc-dialog-content"))
        )

        # Scroll to the bottom.
        driver.execute_script(
            "arguments[0].scrollTop = arguments[0].scrollHeight",
            dialog_content
        )

        # Optional short pause to let the site register the scroll.
        time.sleep(2)

        # Wait for the "I ACKNOWLEDGE AND AGREE" button (#consent-btn) to become clickable.
        acknowledge_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#consent-btn"))
        )
        acknowledge_button.click()
        print("Clicked 'I ACKNOWLEDGE AND AGREE' successfully.")

        # Fill out the fields!
        # Wait for the first-name field to appear.
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, "first-name"))
        )

        driver.find_element(By.ID, "first-name").send_keys(i94_data["firstName"])          
        driver.find_element(By.ID, "last-name").send_keys(i94_data["lastName"])           
        driver.find_element(By.ID, "birth-date").send_keys(i94_data["birthDate"])         
        
        # Country code brings up a dropdown, need to get around that.
        country_field = driver.find_element(By.ID, "mat-input-3")
        country_field.send_keys(i94_data["countryCode"])
        country_field.send_keys(Keys.TAB)  # or Keys.ESCAPE to dismiss the menu

        driver.find_element(By.ID, "document-number").send_keys(i94_data["documentNumber"])

        # The button has id="submit-most-recent" and textContent="Continue".
        try:
            # Wait for the button to become clickable.
            continue_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "submit-most-recent"))
            )
            continue_button.click()
            print("Clicked 'Continue' button. Submitting the form...")

            WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.ID, "print-most-recent-I-94-results"))
            )
            pdf_data = driver.execute_cdp_cmd("Page.printToPDF", {"format": "A4"})
            with open("latest_i94.pdf", "wb") as f:
                f.write(base64.b64decode(pdf_data["data"]))
                print("Saved copy of latest i94 as latest_i94.pdf!")

        except TimeoutException:
            print("The 'Continue' button (#submit-most-recent) never became clickable. Check required fields or validations.")

    except TimeoutException:
        driver.save_screenshot("no_tos_debug.png")
        print("No TOS modal was detected or it didn't appear in time.")

finally:
    driver.quit()
