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
options.add_argument('--window-size=3024x1964') # 1080p
# options.add_argument('--window-size=1920x1080')

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
def get_panels():
    panels = wait_until_execute("""
            const panels_jstcache = document.querySelector("#pane").nextSibling.querySelectorAll("div[jstcache]");
            const panels = Array.from(panels_jstcache).slice(-3); /*最後三個按鈕*/
            if(panels.length<3) return null;
            /* 0. 收合頁面按鈕面板、1. 搜尋結果卡片面板、2. 搜尋結果列表面板 */
            return panels;
            """)
    if not panels:
        raise Exception("Not found panels! Need to check the above JavaScript.")

    (search_list_panel, search_result_panel, _) = panels
    return search_result_panel, search_list_panel

def get_search_result_panels(wait=10):
    search_result_panel, search_list_panel = get_panels()
    search_result = wait_until_execute_on_element("""
        return arguments[0].querySelector("div[role=main]")
        """, search_result_panel, wait)
    return search_result_panel

def scroll_down(element, sleep=2):
    driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', element)
    time.sleep(sleep)

# ------------------------------------------------------------
try:
    _, search_list_panel = get_panels()
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

            # 點擊店面連結
            execute_on_element("arguments[0].click();", anchor)

            # 重心獲取面板內容，因為網頁元素會重新繪製
            info = None
            for retry in range(3):
                if info: break
                try:
                    # 重心獲取面板內容，因為網頁元素會重新繪製。
                    search_result_panel = get_search_result_panels()
                    info = wait_until_execute_on_element("""
                        const title  = arguments[0].querySelector("h1")?.innerText || null;
                        if(!title) return null;

                        const rating = arguments[0].querySelector("[role='img']")?.parentNode?.innerText || null;
                        const server = Array.from(arguments[0].querySelectorAll("div[role=group]")).map(g => g.getAttribute("aria-label") || null);

                        return {title, rating, server};
                    """, search_result_panel, wait=5)
                except TimeoutException:
                    execute_on_element("arguments[0].click();", anchor)
                    time.sleep(1)
            
            if not info: break

            processed_names.add(info['title'])
            print("="*30)
            print(f"{info['title']}") # 暫時先顯示出獲取到的「店名」、「星星數」，之後需要儲存

            # 重心獲取面板內容，因為網頁元素會重新繪製。
            comment_button = None
            for retry in range(3):
                if comment_button: break
                try:
                    print("try to get comment_button")
                    search_result_panel = get_search_result_panels()
                    # 等待評論按鈕出現，並點擊
                    buttons = wait_until_execute_on_element("""
                        const buttons = Array.from(arguments[0].querySelectorAll("div[role=tablist] button"));
                        if(buttons.length===0) return null;
                        return buttons;
                    """, search_result_panel, wait=3)

                    if len(buttons)==3:
                        comment_button = buttons[1]
                        print(buttons)

                except TimeoutException:
                    print("no comment button")
                time.sleep(1)

            if not comment_button: break
                
            execute_on_element("arguments[0].click();", comment_button)
            print("Clicked the comment button.")

            time.sleep(0.5)

        # 重心獲取面板內容，因為網頁元素會重新繪製。
        search_result_panel = get_search_result_panels()
        # 獲取搜尋列表中的 role='feed' 元素，因為這是可以往下滾動的元素，可以更近一步加載網頁內容
        scroll_panel = wait_until_execute_on_element("return arguments[0].querySelector(`div[role='feed']`)", search_list_panel)
        scroll_down(scroll_panel, sleep=2)
        scroll_down(scroll_panel, sleep=5)

        # 重新獲取所有連結
        new_anchors = wait_until_execute_on_element("""
                return Array.from(arguments[0].querySelectorAll("a"))
                    .filter(a => a.href.includes("https://www.google.com/maps/place"));
            """, search_list_panel)

        # 如果新的連結長度與原本一樣，則跳出循環，代表沒有搜尋到內容了
        if len(new_anchors) == len(anchors): break

        anchors.extend(new_anchors[len(anchors):])

finally:
    print("quit")
    # driver.quit()