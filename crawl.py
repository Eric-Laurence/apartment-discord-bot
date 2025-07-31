import time
import random
import os
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import shutil
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from config import (
    RESULTS_FILE, MARKDOWN_FILE, TARGET_URL, TARGET_XPATH, 
    PAGE_LOAD_TIMEOUT, WEBDRIVER_WAIT_TIMEOUT, WINDOW_SIZE,
    USER_AGENTS, CHROME_OPTIONS, CHROME_EXPERIMENTAL_OPTIONS
)

def setup_driver():
    chrome_options = Options()
    
    chrome_options.add_argument(f"--user-agent={random.choice(USER_AGENTS)}")
    
    for option in CHROME_OPTIONS:
        chrome_options.add_argument(option)
    
    for key, value in CHROME_EXPERIMENTAL_OPTIONS.items():
        chrome_options.add_experimental_option(key, value)
    
    chrome_options.add_argument(f"--window-size={WINDOW_SIZE}")

    driver = None
   
    # weird hack that ai suggested for getting
    # it to work on a raspberry pi:

    # try system chromedriver first
    system_chromedriver = shutil.which('chromedriver')
    if system_chromedriver:
        try:
            driver = webdriver.Chrome(
                service=Service(system_chromedriver),
                options=chrome_options
            )
            print(f"Using system ChromeDriver at {system_chromedriver}")
        except Exception as e:
            print(f"System ChromeDriver failed: {str(e)[:100]}...")
    
    # and webdriver-manager if that doesn't work
    if driver is None:
        # try chromium first
        try:
            try:
                from webdriver_manager.core.utils import ChromeType
                driver = webdriver.Chrome(
                    service=Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()),
                    options=chrome_options
                )
            except ImportError:
                driver = webdriver.Chrome(
                    service=Service(ChromeDriverManager(chrome_type="chromium").install()),
                    options=chrome_options
                )
            print("Using Chromium browser (webdriver-manager)")
        except Exception as e:
            print(f"Chromium not available: {str(e)[:100]}...")
            
            # and chrome if that doesnt work
            try:
                driver = webdriver.Chrome(
                    service=Service(ChromeDriverManager().install()),
                    options=chrome_options
                )
                print("Using Chrome browser (webdriver-manager)")
            except Exception as e2:
                print(f"Chrome not available: {str(e2)[:100]}...")
                raise Exception("No working browser found. Install Chrome, Chromium, or system ChromeDriver.")
    
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def extract_floor_plans(url, target_xpath):
    driver = None
    try:
        driver = setup_driver()
        driver.get(url)
        time.sleep(PAGE_LOAD_TIMEOUT)
        
        wait = WebDriverWait(driver, WEBDRIVER_WAIT_TIMEOUT)
        container = wait.until(EC.presence_of_element_located((By.XPATH, target_xpath)))
        
        html_content = container.get_attribute('innerHTML')
        soup = BeautifulSoup(html_content, 'html.parser')
        
        floor_plans = []
        plan_rows = soup.find_all(['div', 'tr'], class_=lambda x: x and any(term in x.lower() for term in ['floorplan', 'floor-plan', 'plan', 'unit']))
        
        if not plan_rows:
            plan_rows = soup.find_all('tr')[1:]
        
        if not plan_rows:
            plan_rows = soup.find_all('div', recursive=True)
            plan_rows = [div for div in plan_rows if div.find_all(['span', 'p', 'div']) and len(div.get_text().strip()) > 10]
        
        seen_plans = set()
        
        for i, row in enumerate(plan_rows[:20]):
            try:
                text_content = row.get_text(separator=' | ', strip=True)
                
                if len(text_content) < 10 or any(skip in text_content.lower() for skip in ['navigation', 'menu', 'header', 'footer']):
                    continue
                
                parts = [part.strip() for part in text_content.split(' | ')]
                
                if len(parts) >= 6 and '$' in text_content:
                    first_part = parts[0].strip()
                    if len(first_part) < 2 or first_part.isdigit() or first_part in ['Studio', '1', '2', '3']:
                        continue
                    
                    plan_data = {
                        'name': parts[0],
                        'type': parts[1] if len(parts) > 1 else '',
                        'bedrooms': parts[1] if parts[1] in ['Studio', '1', '2', '3'] else '',
                        'bathrooms': parts[2] if len(parts) > 2 and parts[2].replace('.', '').isdigit() else '1',
                        'sqft': parts[3] if len(parts) > 3 and parts[3].isdigit() else '',
                        'rent': next((part for part in parts if '$' in part), ''),
                        'availability': parts[-1] if len(parts) > 6 and 'contact' not in parts[-1].lower() else 'Contact for availability',
                        'raw_text': text_content
                    }
                    
                    if plan_data['type'] == 'Studio':
                        plan_data['bedrooms'] = 'Studio'
                        plan_data['bathrooms'] = '1'
                    elif plan_data['type'] == '1':
                        plan_data['bedrooms'] = '1 BR'
                        plan_data['bathrooms'] = '1 BA'
                    
                    unique_key = f"{plan_data['name']}-{plan_data['sqft']}-{plan_data['rent']}"
                    if unique_key not in seen_plans:
                        seen_plans.add(unique_key)
                        floor_plans.append(plan_data)
            
            except Exception:
                continue
        
        unique_plans = []
        seen_keys = set()
        for plan in floor_plans:
            key = f"{plan['name']}-{plan['rent']}"
            if key not in seen_keys:
                seen_keys.add(key)
                unique_plans.append(plan)
        
        def get_rent_value(plan):
            rent = plan.get('rent', '$0')
            try:
                return int(''.join(filter(str.isdigit, rent)))
            except:
                return 0
        
        unique_plans.sort(key=get_rent_value)
        return unique_plans
        
    except Exception as e:
        print(f"Error extracting floor plans: {e}")
        return []
    
    finally:
        if driver:
            driver.quit()

def create_markdown_table(floor_plans):
    if not floor_plans:
        return "# Floor Plans\n\nNo floor plans found.\n"
    
    rents = [int(''.join(filter(str.isdigit, plan.get('rent', '$0')))) for plan in floor_plans if plan.get('rent')]
    min_rent = min(rents) if rents else 0
    max_rent = max(rents) if rents else 0
    avg_rent = sum(rents) // len(rents) if rents else 0
    
    markdown = "# Ariel Court Apartments - Floor Plans\n\n"
    markdown += f"Last updated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n\n"
    markdown += f"Pricing range: ${min_rent:,} - ${max_rent:,} (average: ${avg_rent:,})\n\n"
    markdown += f"Total plans available: {len(floor_plans)}\n\n"
    
    rows_data = []
    max_widths = [10, 3, 4, 6, 4, 12]
    
    for plan in floor_plans:
        name = plan.get('name', 'Unknown').replace('|', '\\|')
        bedrooms = plan.get('bedrooms', '').replace('|', '\\|')
        bathrooms = plan.get('bathrooms', '').replace('|', '\\|')
        sqft = plan.get('sqft', '').replace('|', '\\|')
        rent = plan.get('rent', '').replace('|', '\\|')
        availability = plan.get('availability', '').replace('|', '\\|')
        
        if bedrooms == 'Studio':
            type_formatted = "Studio"
        elif '1' in bedrooms:
            type_formatted = "1 Bedroom"
        else:
            type_formatted = bedrooms or "—"
            
        bathroom_formatted = bathrooms if bathrooms else "—"
        sqft_formatted = f"{sqft} ft²" if sqft else "—"
        rent_formatted = rent if rent else "—"
        
        if availability and 'contact' not in availability.lower():
            avail_formatted = availability
        else:
            avail_formatted = "Contact for details"
        
        row_data = [name, type_formatted, bathroom_formatted, sqft_formatted, rent_formatted, avail_formatted]
        rows_data.append(row_data)
        
        for i, cell in enumerate(row_data):
            max_widths[i] = max(max_widths[i], len(str(cell)))
    
    headers = ["Floor Plan", "Bed", "Bath", "Sq.Ft.", "Rent", "Availability"]
    header_row = "| " + " | ".join(f"{headers[i]:<{max_widths[i]}}" for i in range(len(headers))) + " |\n"
    separator_row = "|-" + "-|-".join("-" * max_widths[i] for i in range(len(headers))) + "-|\n"
    
    markdown += header_row
    markdown += separator_row
    
    for row_data in rows_data:
        padded_cells = [f"{row_data[i]:<{max_widths[i]}}" for i in range(len(row_data))]
        markdown += "| " + " | ".join(padded_cells) + " |\n"
    
    return markdown

def load_previous_results():
    if os.path.exists(RESULTS_FILE):
        try:
            with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return None

def save_results(floor_plans):
    try:
        results = {
            'timestamp': datetime.now().isoformat(),
            'floor_plans': floor_plans
        }
        with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving results: {e}")

def compare_results(old_results, new_floor_plans):
    if not old_results:
        return True, False
    
    old_plans = old_results.get('floor_plans', [])
    
    if len(old_plans) != len(new_floor_plans):
        return True, False
    
    has_changes = False
    availability_opened = False
    
    for i, (old_plan, new_plan) in enumerate(zip(old_plans, new_floor_plans)):
        for key in ['name', 'bedrooms', 'bathrooms', 'sqft', 'rent', 'availability']:
            old_val = old_plan.get(key, '')
            new_val = new_plan.get(key, '')
            if old_val != new_val:
                has_changes = True
                
                # check if availability changed from contact to a number (new availability!)
                if key == 'availability':
                    old_is_contact = 'contact' in old_val.lower()
                    new_has_number = new_val.replace('Availability', '').strip().isdigit()
                    if old_is_contact and new_has_number:
                        availability_opened = True
    
    return has_changes, availability_opened

def crawl_apartments():
    url = TARGET_URL
    xpath = TARGET_XPATH
    
    print("Starting apartment crawler...")
    previous_results = load_previous_results()
    floor_plans = extract_floor_plans(url, xpath)
    
    if not floor_plans:
        print("No floor plans extracted")
        return [], False
    
    print(f"Extracted {len(floor_plans)} floor plans")
    has_changes, availability_opened = compare_results(previous_results, floor_plans)
    
    if availability_opened:
        print("🚨 APARTMENT AVAILABLE!")
    elif has_changes:
        print("🔥 Changes detected!")
    else:
        print("✅ No changes detected")
    
    save_results(floor_plans)
    
    markdown_content = create_markdown_table(floor_plans)
    try:
        with open(MARKDOWN_FILE, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        print(f"Results saved to {MARKDOWN_FILE}")
    except Exception as e:
        print(f"Error saving markdown: {e}")
    
    return floor_plans, has_changes, availability_opened

def main():
    floor_plans, has_changes, availability_opened = crawl_apartments()
    
    if floor_plans:
        print("\n" + "="*60)
        print("CURRENT FLOOR PLANS")
        print("="*60)
        
        markdown_content = create_markdown_table(floor_plans)
        print(markdown_content)
    
if __name__ == "__main__":
    main()
