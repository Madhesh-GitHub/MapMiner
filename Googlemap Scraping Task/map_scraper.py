from flask import Flask, render_template, request, send_file
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import StaleElementReferenceException
import pandas as pd
import time

# Flask app initialization
app = Flask(__name__)

# Function to scrape data from Google Maps
def scrape_google_maps(keywords, details_cnt):
    SOURCE = "Google Map"
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option("detach", True)
    driver = webdriver.Chrome(options=chrome_options)
    driver.maximize_window()

    # Navigate to Google Maps
    driver.get("https://www.google.com/maps")
    time.sleep(3)

    # Search for the keyword
    search_box = driver.find_element(By.ID, "searchboxinput")
    search_box.send_keys(keywords)
    search_box.send_keys(Keys.RETURN)
    time.sleep(5)

    data = []
    processed_names = set()
    wait = WebDriverWait(driver, 10)

    def find_businesses(max_retries=3):
        """Find business elements with retry logic"""
        for _ in range(max_retries):
            try:
                return wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "hfpxzc")))
            except:
                time.sleep(2)
        return []

    def scroll_results():
        """Scroll the results panel with error handling"""
        try:
            scrollable_div = driver.find_element(By.CSS_SELECTOR, 'div[role="feed"]')
            last_height = driver.execute_script("return arguments[0].scrollHeight", scrollable_div)

            for _ in range(3):  # Limit scroll attempts
                driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight);", scrollable_div)
                time.sleep(2)

                new_height = driver.execute_script("return arguments[0].scrollHeight", scrollable_div)
                if new_height == last_height:
                    break
                last_height = new_height
        except Exception as e:
            print(f"Scroll error (non-critical): {str(e)}")

    try:
        while len(data) < details_cnt:  # Adjust number of results as needed
            scroll_results()
            business_elements = find_businesses()

            if not business_elements:
                print("No business elements found, retrying...")
                time.sleep(2)
                continue

            for business_element in business_elements:
                if len(data) >= details_cnt:
                    break

                try:
                    # Retry getting business name if stale
                    for _ in range(3):
                        try:
                            current_name = business_element.get_attribute("aria-label")
                            break
                        except StaleElementReferenceException:
                            business_elements = find_businesses()
                            continue

                    if not current_name or current_name in processed_names:
                        continue

                    # Click with retry logic
                    clicked = False
                    for _ in range(3):
                        try:
                            driver.execute_script("arguments[0].click();", business_element)
                            clicked = True
                            break
                        except:
                            try:
                                ActionChains(driver).move_to_element(business_element).click().perform()
                                clicked = True
                                break
                            except:
                                time.sleep(1)
                                continue

                    if not clicked:
                        print(f"Failed to click business element, skipping...")
                        continue

                    time.sleep(3)

                    # Extract details with explicit waits
                    try:
                        name = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "DUwDvf"))).text
                    except:
                        name = ""

                    try:
                        rating = driver.find_element(By.XPATH, '//*[@id="QA0Szd"]/div/div/div[1]/div[3]/div/div[1]/div/div/div[2]/div[2]/div/div[1]/div[2]/div/div[1]/div[2]/span[1]/span[1]').text
                    except:
                        rating = ""

                    try:
                        review_count = driver.find_element(By.XPATH, '//*[@id="QA0Szd"]/div/div/div[1]/div[3]/div/div[1]/div/div/div[2]/div[2]/div/div[1]/div[2]/div/div[1]/div[2]/span[2]/span/span').text
                    except:
                        review_count = ""

                    try:
                        status = driver.find_element(By.XPATH, '//*[@id="QA0Szd"]/div/div/div[1]/div[3]/div/div[1]/div/div/div[2]/div[7]/div[4]/div[1]/div[2]/div/span[1]/span/span[1]').text
                    except:
                        status = ""

                    try:
                        address = driver.find_element(By.XPATH, '//*[@id="QA0Szd"]/div/div/div[1]/div[3]/div/div[1]/div/div/div[2]/div[7]/div[3]/button/div/div[2]/div[1]').text
                    except:
                        address = ""

                    try:
                        phone = driver.find_element(By.XPATH, '//*[@id="QA0Szd"]/div/div/div[1]/div[3]/div/div[1]/div/div/div[2]/div[7]/div[7]/button/div/div[2]/div[1]').text
                    except:
                        phone = ""

                    try:
                        website = driver.find_element(By.XPATH, "//a[@class='CsEnBe']").get_attribute("href")
                    except:
                        website = ""

                    try:
                        area_state = driver.find_element(By.XPATH, '//*[@id="QA0Szd"]/div/div/div[1]/div[3]/div/div[1]/div/div/div[2]/div[7]/div[8]/button/div/div[2]/div[1]').text
                    except:
                        area_state = ""

                    

                    if name:
                        processed_names.add(name)
                        data.append({
                            "Keywords": keywords,
                            "Source": SOURCE,
                            "Name": name,
                            "Address": address,
                            "Phone": phone,
                            "Website": website,
                            "Area and State": area_state,
                            "Rating": rating,
                            "Review Count": review_count,
                            "Status": status
                        })
                        print(f"Successfully scraped {len(data)} companies: {name}")

                    # Go back with retry logic
                    for _ in range(3):
                        try:
                            driver.execute_script("window.history.go(-1)")
                            time.sleep(2)
                            break
                        except:
                            time.sleep(1)

                except Exception as e:
                    print(f"Error processing business (continuing): {str(e)}")
                    try:
                        driver.execute_script("window.history.go(-1)")
                    except:
                        pass
                    time.sleep(2)
                    continue

            if not data:
                print("No data collected yet, retrying...")
                time.sleep(2)

    except Exception as e:
        print(f"Major error: {str(e)}")

    finally:
        driver.quit()
        if data:
            filename = "google_maps_results.csv"
            df = pd.DataFrame(data)
            df.to_csv(filename, index=False)
            return filename
        return None

# Route for the main page
@app.route('/')
def index():
    return render_template('index.html')

# Route to handle the form submission and trigger scraping
@app.route('/scrape', methods=['POST'])
def scrape():
    details_cnt = request.form['details_cnt']
    keywords = request.form['keywords']
    
    # Scrape the data and get the filename
    output_file = scrape_google_maps(keywords, int(details_cnt))
    
    return render_template('download.html', file_name=output_file)
    
# Route to download the file
@app.route('/download/<file_name>')
def download_file(file_name):
    return send_file(file_name, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
