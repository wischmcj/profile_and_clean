# Archive Download Automation Script
A script that automates the process of downloading DOE outage files from this url - https://doe417.pnnl.gov/.

### Installation

1. Install Selenium and ChromeDriver:
```bash
pip install selenium
```

2. Install ChromeDriver:
   - **Linux**: `sudo apt-get install chromium-chromedriver` or download from https://chromedriver.chromium.org/
   - **macOS**: `brew install chromedriver`
   - **Windows**: Download from https://chromedriver.chromium.org/ and add to PATH

### Usage

```bash
python download_archives.py <URL> [options]
```

**Options:**
- `-d, --download-dir <directory>`: Directory to save downloads (default: `./downloads`)
- `--headless`: Run browser in headless mode (no GUI)

**Example:**
```bash
python download_archives.py https://example.com/reports --download-dir ./my_downloads
```

## How It Works
The script uses a browser driver to:
1. Open the specified webpage
2. Click the button with `data-test-id="archivesButton"`
3. Wait for the popup to appear
4. For each year available in the dropdown (`data-test-id="yearDropdown"`):
   - Select the year
   - Ensure the Excel checkbox (`data-test-id="excelCheckbox"`) is selected
   - Click the download button (`data-test-id="downloadReportButton"`)
   - Wait for the download to complete
5. Save all files to the specified download directory

