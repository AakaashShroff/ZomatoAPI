import os
import json
import time
import traceback
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
    ElementClickInterceptedException
)

COOKIES_FILE = 'login_cookies.json'

restaurant_dict = {
    "Beijing Bites": ["Chicken Tikka Pizza", "Beijing Duck"],
    "Little Italy": ["Margherita Pizza", "Pasta Carbonara"],
    "Shandong": ["Beef Noodles", "Chicken Tikka Pizza"],
    "Quattro - The Leela Bhartiya City Bengaluru": ["Paneer Tikka", "Chicken Tikka Pizza"],
    "Chung Wah": ["Spring Rolls", "Chicken Tikka Pizza"],
}

def save_cookies(driver, path):
    try:
        with open(path, 'w') as file:
            json.dump(driver.get_cookies(), file)
    except Exception as e:
        print(f"Failed to save cookies. Exception: {e}")

def load_cookies(driver, path):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return False
    try:
        with open(path, 'r') as file:
            cookies = json.load(file)
        for cookie in cookies:
            cookie.pop('sameSite', None)
            try:
                driver.add_cookie(cookie)
            except WebDriverException as e:
                print(f"Failed to add cookie. Exception: {e}")
        return True
    except Exception as e:
        print(f"Failed to load cookies. Exception: {e}")
        return False

def is_logged_in(driver):
    try:
        driver.find_element(By.LINK_TEXT, 'Log in')
        return False
    except NoSuchElementException:
        return True

def manual_login(driver):
    timeout = 300
    poll_interval = 5
    elapsed_time = 0
    while elapsed_time < timeout:
        time.sleep(poll_interval)
        elapsed_time += poll_interval
        if is_logged_in(driver):
            return True
    return False

def close_popups(driver):
    try:
        wait = WebDriverWait(driver, 10)
        close_buttons = wait.until(EC.presence_of_all_elements_located(
            (By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), 'Close')]")
        ))
        for btn in close_buttons:
            try:
                btn.click()
                time.sleep(0.5)
            except (ElementClickInterceptedException, WebDriverException):
                pass
    except TimeoutException:
        pass

def select_address(driver, address_details):
    try:
        wait = WebDriverWait(driver, 15)
        close_popups(driver)
        input_field = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//input[@placeholder='Bengaluru']")
        ))
        input_field.click()
        address_xpath = f"//p[contains(text(), '{address_details}')]"
        address_element = wait.until(EC.element_to_be_clickable((By.XPATH, address_xpath)))
        address_element.click()
    except Exception as e:
        print(f"Failed to select the address. Exception: {e}")

def click_first_order_now(driver):
    try:
        wait = WebDriverWait(driver, 20)
        order_now_xpath = "//button[@role='button' and (not(@aria-disabled) or @aria-disabled='false') and .//span[text()='Order Now']]"
        order_now_buttons = wait.until(EC.presence_of_all_elements_located(
            (By.XPATH, order_now_xpath)
        ))
        if order_now_buttons:
            first_button = order_now_buttons[0]
            driver.execute_script("arguments[0].scrollIntoView(true);", first_button)
            time.sleep(0.5)
            try:
                first_button.click()
            except WebDriverException:
                driver.execute_script("arguments[0].click();", first_button)
    except Exception as e:
        print(f"Failed to click the 'Order Now' button. Exception: {e}")

def main():
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()

    try:
        driver.get('https://www.zomato.com')
        time.sleep(3)

        if load_cookies(driver, COOKIES_FILE):
            driver.refresh()
            time.sleep(3)
            if not is_logged_in(driver):
                os.remove(COOKIES_FILE)
                driver.quit()
                main()
                return
        else:
            try:
                login_button = driver.find_element(By.LINK_TEXT, 'Log in')
                login_button.click()
            except NoSuchElementException:
                driver.quit()
                return

            if manual_login(driver):
                save_cookies(driver, COOKIES_FILE)
            else:
                driver.quit()
                return

        select_address(driver, '50406')

        try:
            search_bar = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//input[@placeholder='Search for restaurant, cuisine or a dish']")
                )
            )
        except TimeoutException:
            driver.quit()
            return

        dish_name = input("Enter the dish you want to search for: ").strip()
        
        if dish_name:
            matching_restaurants = [
                restaurant for restaurant, dishes in restaurant_dict.items()
                if dish_name.lower() in (dish.lower() for dish in dishes)
            ]
            if not matching_restaurants:
                driver.quit()
                return
            
            restaurant_to_search = matching_restaurants[0]
            try:
                search_bar.clear()
                search_bar.send_keys(restaurant_to_search)
                try:
                    search_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
                        (By.XPATH, "//button[@type='submit' or contains(@aria-label, 'Search')]")
                    ))
                    search_button.click()
                except TimeoutException:
                    search_bar.send_keys(Keys.RETURN)
                time.sleep(3)
                click_first_order_now(driver)
            except Exception as e:
                print(f"Failed to search and navigate. Exception: {e}")
        else:
            print("No dish name entered.")

    except KeyboardInterrupt:
        print("Script interrupted.")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
