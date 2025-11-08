#!/usr/bin/env python3
"""
Selenium script to automate downloading archive files from a webpage.
Based on Puppeteer recording, this script:
1. Opens the webpage and handles "Agree" popup
2. Clicks the Archives button once
3. Gets all available years from the dropdown
4. For each year: selects it, chooses Excel format, and downloads
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
import time
import os
import sys


def wait_for_download(download_dir, files_before, timeout=60):
    """Wait for a new file to appear in the download directory."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        files_after = len([f for f in os.listdir(download_dir) 
                          if os.path.isfile(os.path.join(download_dir, f))])
        if files_after > files_before:
            return True
        time.sleep(0.5)
    return False


def safe_click(driver, element, description="element"):
    """Safely click an element, trying multiple methods if needed."""
    try:
        # Try regular click first
        element.click()
        return True
    except ElementClickInterceptedException:
        # If intercepted, try scrolling into view and using ActionChains
        try:
            driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(0.3)
            ActionChains(driver).move_to_element(element).click().perform()
            return True
        except Exception as e:
            print(f"  ⚠ Warning: Could not click {description}: {e}")
            return False
    except Exception as e:
        print(f"  ⚠ Warning: Error clicking {description}: {e}")
        return False


def get_all_years(driver, wait_timeout=10):
    """
    Get all available years from the dropdown menu.
    Returns a list of year strings (e.g., ['2023', '2022', ...])
    """
    try:
        # Find the year dropdown and click it to open
        year_dropdown = WebDriverWait(driver, wait_timeout).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-test-id="yearDropdown"]'))
        )
        
        # Click the dropdown to open it
        safe_click(driver, year_dropdown, "year dropdown")
        time.sleep(0.5)
        
        # Wait for the dropdown menu to appear
        # Try multiple selectors for the listbox/menu
        listbox = None
        listbox = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'ul[role="listbox"]'))
        )
        
        # Find all menu items with year data-test-id attributes
        menu_items = listbox.find_elements(By.CSS_SELECTOR, 'a[role="menuitem"], li[role="menuitem"]')
        
        years = []
        for item in menu_items:
            # Get the year from data-test-id attribute (e.g., "2023")
            year = item.get_attribute('data-test-id')
            if year and year.isdigit():  # Ensure it's a valid year
                years.append(year)
            else:
                # Fallback: try to get from text content
                text = item.text.strip()
                if text and text.isdigit():
                    years.append(text)
        
        # Close dropdown by clicking outside or pressing Escape
        driver.execute_script("arguments[0].blur();", year_dropdown)
        time.sleep(0.3)
        
        return sorted(years, reverse=True)  # Most recent years first
        
    except Exception as e:
        print(f"  ⚠ Error getting years: {e}")
        return []


def download_archives(url, download_dir=None, headless=False):
    """
    Download archive files for all available years.
    
    Args:
        url: The URL of the webpage
        download_dir: Directory to save downloads (default: ./downloads)
        headless: Run browser in headless mode (default: False)
    """
    # Set up download directory
    if download_dir is None:
        download_dir = os.path.join(os.getcwd(), "downloads")
    os.makedirs(download_dir, exist_ok=True)
    print(f"Download directory: {os.path.abspath(download_dir)}")
    
    # Configure Chrome options for downloads
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    
    # Set download preferences
    prefs = {
        "download.default_directory": os.path.abspath(download_dir),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    options.add_experimental_option("prefs", prefs)
    
    driver = None
    try:
        # Initialize the driver
        print("Initializing browser...")
        driver = webdriver.Chrome(options=options)
        driver.set_window_size(658, 917)  # Match viewport from recording
        driver.implicitly_wait(5)
        
        # Navigate to the page
        print(f"Navigating to {url}...")
        driver.get(url)
        time.sleep(2)  # Allow page to load
        
        # Handle "Agree" popup (initial step not shown in recording)
        print("Looking for 'Agree' button...")
        
        agree_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-test-id="consentButton"]'))
                )
        safe_click(driver, agree_button, "Agree button")
        time.sleep(1)
        
        # Click Archives button (only once)
        print("Clicking Archives button...")
        archives_button = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-test-id="archivesButton"]'))
        )
        safe_click(driver, archives_button, "Archives button")
        
        # Wait for popup/dialog to appear
        print("Waiting for dialog to appear...")
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.bp5-dialog-body'))
        )
        time.sleep(1)  # Brief pause for dialog to fully render
        
        # Get all available years from the dropdown
        available_years = get_all_years(driver)
        
        print(f"Found {len(available_years)} years: {', '.join(available_years)}")
        #clicking to close the dropdown
        year_dropdown = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-test-id="yearDropdown"]'))
        )
        safe_click(driver, year_dropdown, f"year dropdown")
        
        # Process each year
        successful_downloads = 0
        failed_downloads = []
    
        for idx, year in enumerate(available_years, 1):
            
            print(f"\n[{idx}/{len(available_years)}] Processing year {year}...")
            
            # Step 1: Click year dropdown to open it
            year_dropdown = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-test-id="yearDropdown"]'))
            )
            safe_click(driver, year_dropdown, f"year dropdown for {year}")
            time.sleep(0.5)
            
            # Step 2: Wait for dropdown menu and click the specific year
            # Try to find the listbox/menu
            listbox = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'ul[role="listbox"]'))
            )

            # Find and click the specific year menu item
            year_menu_item = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, f'a[data-test-id="{year}"][role="menuitem"], li[data-test-id="{year}"][role="menuitem"]'))
            )
            safe_click(driver, year_menu_item, f"year {year} menu item")
            time.sleep(0.8)  # Wait for selection to register
            
            # Step 3: Select Excel format checkbox (label:nth-of-type(2) > span)
            print(f"  Selecting Excel format...")
            excel_checkbox_span = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'label:nth-of-type(2) > span'))
            )
            # Check if already selected, if not, click it
            try:
                checkbox_input = driver.find_element(By.CSS_SELECTOR, 'label:nth-of-type(2) input[type="checkbox"]')
                if not checkbox_input.is_selected():
                    safe_click(driver, excel_checkbox_span, "Excel checkbox")
            except NoSuchElementException:
                # If checkbox not found, just click the span
                safe_click(driver, excel_checkbox_span, "Excel checkbox")
            time.sleep(0.5)
            
            # Step 4: Count files before download
            files_before = len([f for f in os.listdir(download_dir) 
                               if os.path.isfile(os.path.join(download_dir, f))])
            
            # Step 5: Click download button
            print(f"  Clicking download button...")
            download_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-test-id="downloadReportButton"] > span, [data-test-id="downloadReportButton"]'))
            )
            safe_click(driver, download_button, "download button")
            
            # Wait for download to complete
            print(f"  Waiting for download to complete...")
            if wait_for_download(download_dir, files_before, timeout=60):
                print(f"  ✓ Download completed for year {year}")
                successful_downloads += 1
            else:
                print(f"  ⚠ Warning: Download may not have completed for year {year}")
                failed_downloads.append(year)
            
            # Brief pause between downloads
            time.sleep(1)
        # Summary
        print(f"\n{'='*60}")
        print(f"Download Summary:")
        print(f"  Total years: {len(available_years)}")
        print(f"  Successful: {successful_downloads}")
        print(f"  Failed: {len(failed_downloads)}")
        if failed_downloads:
            print(f"  Failed years: {', '.join(failed_downloads)}")
        print(f"  Files saved to: {os.path.abspath(download_dir)}")
        print(f"{'='*60}")
        
    except TimeoutException as e:
        print(f"✗ Timeout error: {str(e)}")
        print("The page may have taken too long to load, or elements may not be found.")
        sys.exit(1)
    except NoSuchElementException as e:
        print(f"✗ Element not found: {str(e)}")
        print("Please verify the webpage structure and data-test-id attributes.")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if driver:
            print("\nClosing browser...")
            driver.quit()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Download archive files from a webpage using Selenium',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  python download_archives_selenium.py https://doe417.pnnl.gov/ -d ./my_downloads
        """
    )
    parser.add_argument('url', help='URL of the webpage')
    parser.add_argument('-d', '--download-dir', default=None, 
                       help='Directory to save downloads (default: ./downloads)')
    parser.add_argument('--headless', action='store_true',
                       help='Run browser in headless mode')
    
    args = parser.parse_args()
    
    download_archives(args.url, args.download_dir, args.headless)

