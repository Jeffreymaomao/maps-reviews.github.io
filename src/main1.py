
import time
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC

def find_closest_in_parent(driver, element, selector):
    while element:
        try:
            parent = element.find_element(By.XPATH, "..")
            found = parent.find_elements(By.CSS_SELECTOR, selector)
            if found:
                return found[0]
            element = parent
        except Exception as e:
            break
    return None

chrome_driver_path = '/usr/local/bin/chromedriver'  # 替换为实际的ChromeDriver路径
options = webdriver.ChromeOptions()
# options.add_argument('--headless') # Run in background
options.add_argument('--disable-gpu')
options.add_argument('--window-size=1920x1080')

# initialize WebDriver
service = Service(chrome_driver_path)
driver = webdriver.Chrome(service=service, options=options)

# open Google maps
driver.get('https://www.google.com/maps')

# get search input DOM
search_box = driver.find_element(By.ID, 'searchboxinput')

# searching
search_box.send_keys('嘉義火雞肉飯')
search_box.send_keys(Keys.RETURN)

def exctute_on_element(javascript, element):
    return  driver.execute_script(javascript, element)

def wait_untill_exctute(javascript, wait=20):
    return  WebDriverWait(driver, wait).until(
        lambda driver: driver.execute_script(javascript)
    )

def wait_untill_exctute_on_element(javascript, element, wait=20):
    return  WebDriverWait(driver, wait).until(
        lambda driver: driver.execute_script(javascript, element)
    )

try:
    pane_element = wait_untill_exctute("""
        return document.querySelector("#pane");
        """)
    print("PROCESS: #pane element loaded!")

    links = wait_untill_exctute("""
        const pane = document.querySelector("#pane");
        if (pane && pane.nextSibling) {
            return Array.from(pane.nextSibling.querySelectorAll("a"))
                .filter(a=>a.href.includes("https://www.google.com/maps/place"));
        } else {
            return null;
        }
        """)
    print("PROCESS: get <a> tags!")

    for link in links:
        href = exctute_on_element("return arguments[0].getAttribute('href');", link)
        # print(f"{href}\n")

        # click element
        exctute_on_element("arguments[0].click();", link)
        pane = wait_untill_exctute("""
            const panels = document.querySelector("#pane").nextSibling.querySelectorAll("div[jstcache]");
            const n = panels.length;
            const panel_last1 = panels[n];
            const panel_last2 = panels[n-1];
            return 
            """)
        # 突然發現在這樣的搜尋下，可以找到google maps的結構
        # 在網頁底下，會有 id=pane 的下一個元素，會是放搜尋結果的
        # 在這底下開始尋找 div[jstcache] 會有很多東西
        # 但是如果仔細看網頁版的結果，
        # 倒數第一個 會是放「收合頁面按鈕」
        # 倒數第二個 會是放「點擊收尋結果出現的第嘉的」
        # 倒數第三個 會是放「搜尋結果的所有內容」
        # 倒數第四個 ...
        #
        # 因此我接下來想要改成先利用這個結構獲取搜尋的結果
        # 希望Google Maps之後不要做太多的變動

        h1 = wait_untill_exctute("""
            const titles = document.querySelectorAll("h1");
            return titles[1] ? titles[1].innerText : null;
            """)
        print(h1)
        time.sleep(3)

finally:
    driver.quit()