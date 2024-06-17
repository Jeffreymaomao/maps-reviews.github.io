# import os
# import re
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
search_box.send_keys('甜點')
search_box.send_keys(Keys.RETURN)

def execute_on_element(javascript, element):
    return  driver.execute_script(javascript, element)

def wait_until_execute(javascript, wait=20):
    return  WebDriverWait(driver, wait).until(
        lambda driver: driver.execute_script(javascript)
    )

def wait_until_execute_on_element(javascript, element, wait=20):
    return  WebDriverWait(driver, wait).until(
        lambda driver: driver.execute_script(javascript, element)
    )

# ------------------------------------------------------------

def get_search_result_panels():
    panels = wait_until_execute("""
            const panels = document.querySelector("#pane").nextSibling.querySelectorAll("div[jstcache]");
            const n = panels.length;
            if(n<3) return null;
            const panel_last1 = panels[n-1]; /* 收合頁面按鈕面板 */
            const panel_last2 = panels[n-2]; /* 搜尋結果卡片面板*/
            const panel_last3 = panels[n-3]; /* 搜尋結果列表面板 */
            return [panel_last1, panel_last2, panel_last3];
            """)
    if not panels:
        raise Exception("Not found panels! Need to check the above JavaScript.")

    (_, search_result_panel, search_list_panel) = panels
    return search_result_panel, search_list_panel

def scroll_down(element, wait=2):
    driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', element)
    time.sleep(2)

# ------------------------------------------------------------
try:
    search_result_panel, search_list_panel = get_search_result_panels()
    anchors = wait_until_execute_on_element("""
        return Array.from(arguments[0].querySelectorAll("a"))
            .filter(a=>a.href.includes("https://www.google.com/maps/place"));
        """, search_list_panel)

    # 用於儲存曾經處理過的「網址」與「店名」
    processed_urls = set()
    processed_names = set()

    while True:
        for anchor in anchors:
            href = execute_on_element("return arguments[0].getAttribute('href');", anchor)
            if href in processed_urls: continue # 如果「網址」曾經處理過，則跳過這個循環
            processed_urls.add(href)

            # click element
            execute_on_element("arguments[0].click();", anchor)

            title = wait_until_execute_on_element("return arguments[0].querySelector('h1')?.innerText || null;", search_result_panel)
            if not title or title in processed_names: continue # 如果「店名」曾經處理過，則跳過這個循環
            processed_names.add(title)

            # 這裡在跑評分的時候，發現網頁星星數應該可以跟標題一起，所以試試看
            # 而且不知道為什麼星星數有時候抓不到。

            # rating = wait_until_execute_on_element("return arguments[0].querySelector(`span[aria-label][role='img']`)?.parentNode?.innerText || null", search_result_panel, wait=5)

            print(f"{1} - {title}") # 暫時先顯示出獲取到的「店名」、「星星數」，之後需要儲存

            # 重心獲取面板內容，因為網頁元素會重新繪製。
            search_result_panel, search_list_panel = get_search_result_panels()

        # 獲取搜尋列表中的 role='feed' 元素，因為這是可以往下滾動的元素，可以更近一步加載網頁內容
        scroll_panel = wait_until_execute_on_element("return arguments[0].querySelector(`div[role='feed']`)", search_list_panel)
        scroll_down(scroll_panel)

        # 重新獲取所有連結
        new_anchors = wait_until_execute_on_element("""
                return Array.from(arguments[0].querySelectorAll("a"))
                    .filter(a => a.href.includes("https://www.google.com/maps/place"));
            """, search_list_panel)

        # 如果新的連結長度與原本一樣，則跳出循環，代表沒有搜尋到內容了
        if len(new_anchors) == len(anchors): break

        anchors.extend(new_anchors[len(anchors):])

finally:
    driver.quit()