import os
import json
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchWindowException

driver = None
MAX_NUM_OF_COMMENT = 5000
CHROME_DRIVER_PATH = '/usr/local/bin/chromedriver'  # ChromeDriver 驅動器的路徑
SAVE_DAT_FILE_PATH = './dat/'

def save_data_to_file(data, directory, filename):
    if not os.path.exists(directory): os.makedirs(directory)
    filepath = os.path.join(directory, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        if isinstance(data, str):
            f.write(data)
        elif isinstance(data, (dict, list)):
            json.dump(data, f, ensure_ascii=False, indent=4)
        else:
            raise ValueError("Unsupported data type. Only str, dict, and list are supported.")
    return True

# ------------------------------------------------------------
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

def scroll_down(element, sleep=1):
    driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', element)
    time.sleep(sleep)

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
# ------------------------------------------------------------
def get_shops_anchors():
    _, search_list_panel = get_panels()
    anchors = wait_until_execute_on_element("""
        return Array.from(arguments[0].querySelectorAll("a"))
            .filter(a=>a.href.includes("https://www.google.com/maps/place"));
    """, search_list_panel)
    return anchors

def get_shops_list_scroll_panel():
    # 獲取搜尋列表中的 role='feed' 元素，因為這是可以往下滾動的元素，可以更近一步加載網頁內容
    _, search_list_panel = get_panels()
    scroll_panel = wait_until_execute_on_element("""
        return arguments[0].querySelector(`div[role='feed']`)
    """, search_list_panel)
    return scroll_panel


def get_shop_information(click_button=None, retry_times=3, retry_sleep=1):
    if not click_button:
        raise Exception("Must input the `click_button`!")
    info = None
    for retry in range(retry_times):
        if info: break
        try:
            # 重心獲取面板內容，因為網頁元素會重新繪製。
            search_result_panel = get_search_result_panels()
            info = wait_until_execute_on_element("""
                const title = arguments[0].querySelector("h1")?.innerText || null;
                if (!title) return null;
                
                const rating = arguments[0].querySelector("[role='img']")?.parentNode?.innerText || null;
                const server = Array.from(arguments[0].querySelectorAll("div[role=group]")).map(g => g?.getAttribute("aria-label") || null);
                const shops_type = arguments[0].querySelector("span > span > button")?.innerText || null;
                
                const shops_other_info = arguments[0].querySelectorAll("div[role=region]")[2];
                if(!shops_other_info) return { title, rating, server, shops_type};
                
                const address = shops_other_info?.querySelector("button[data-item-id='address']")?.innerText.split('\\n').pop() || null;

                const authority = shops_other_info.querySelector("*[data-item-id=authority]")?.href || null;
                const oloc = shops_other_info.querySelector("*[data-item-id=oloc]")?.innerText?.split('\\n').pop() || null;
                const phone = shops_other_info.querySelector("*[data-item-id^=phone]")?.innerText.split('\\n').pop() || null;
                const open_time = shops_other_info.querySelector("table")?.parentNode?.parentNode?.getAttribute("aria-label") || null;

                return {title, rating, server, shops_type, address, authority, oloc, phone, open_time};
            """, search_result_panel, wait=retry_sleep+2)
        except TimeoutException as err:
            print("Not found info! retrying...")
            execute_on_element("arguments[0].click();", click_button)
            time.sleep(retry_sleep)
    return info

def get_comments_button(retry_times=3, retry_sleep=1):
    comment_button = None
    for retry in range(retry_times):
        if comment_button: break
        try:
            print("try to get comment_button")
            # 重心獲取面板內容，因為網頁元素會重新繪製。
            search_result_panel = get_search_result_panels()
            # 等待評論按鈕出現，並點擊
            buttons = wait_until_execute_on_element("""
                const buttons = Array.from(arguments[0].querySelectorAll("div[role=tablist] button"));
                if(buttons.length===0) return null;
                return buttons;
            """, search_result_panel, wait=retry_sleep+0.5)

            if buttons and len(buttons)==3:
                comment_button = buttons[1]

        except TimeoutException as err:
            print("No comment button, retrying...")
        time.sleep(retry_sleep)
    return comment_button

def get_radios(wait=10, retry_times=3, retry_sleep=1):
    radiogroup = None
    for retry in range(retry_times):
        if radiogroup: break
        try:
            # 重心獲取面板內容，因為網頁元素會重新繪製。
            search_result_panel = get_search_result_panels()
            radiogroup = wait_until_execute_on_element("""
                return arguments[0].querySelector("div[role=radiogroup]");
            """, search_result_panel, wait=retry_sleep+0.5)
        except TimeoutException as err:
            print("No radiogroup, retrying...")
        time.sleep(retry_sleep)

    if not radiogroup: return None
    # 重心獲取面板內容，因為網頁元素會重新繪製。
    search_result_panel = get_search_result_panels()
    radios = wait_until_execute_on_element("""
        const radios = Array.from(arguments[0].querySelectorAll("button[role=radio]"))
            ?.map(b => {
                const spans = b.querySelectorAll("span");
                return spans.length === 2 ? [spans[0].innerText, spans[1].innerText] : null;
            })
            .filter(arr => arr !== null)
            .reduce((obj, item) => {obj[item[0]] = parseInt(item[1], 10);return obj;}, {});
        return radios;
    """, radiogroup, wait=wait)
    return radios

def get_comments():
    # 重心獲取面板內容，因為網頁元素會重新繪製。
    search_result_panel = get_search_result_panels()
    
    # -----------
    comments_scroll_panel = wait_until_execute_on_element("""
        return arguments[0].querySelector("div[role=main]").lastChild;
    """, search_result_panel, wait=5)

    scroll_down(comments_scroll_panel, sleep=1)

    comments_group = None
    for retry in range(3):
        if comments_group: break
        try:
            comments_group = wait_until_execute_on_element("""
                /* 會在 role=presentation 的最後一個元素，會是用在評論中做分隔，其父元素為「評論」頁面的群組。 */
                const comments_group = Array.from(arguments[0].querySelectorAll("div[role=presentation]"))?.pop()?.parentNode;
                /* 如果 comments_group 裡面還有role=region，就代表還在「總覽」頁面，還沒到「評論」頁面。 */
                if(comments_group.querySelector("div[role=region]")) return null;

                const comments_blocks_length = Array.from(comments_group.querySelectorAll(':scope > div:not([role=presentation])'))
                    .filter(dom=>dom?.getAttribute("aria-label")).length;
                if(!comments_blocks_length) return null;
                return comments_group;
            """, search_result_panel, wait=10)
        except TimeoutException as err:
            print("No comments_group, retrying...")
            scroll_down(comments_scroll_panel, sleep=10)
    # -----------
    comments_blocks =  wait_until_execute_on_element("""
        const comments_blocks = Array.from(arguments[0].querySelectorAll(':scope > div:not([role=presentation])'));
        return comments_blocks;
    """, comments_group, wait=5)

    all_comments_datas = []
    comment_index = 0
    while True:
        if(comment_index > MAX_NUM_OF_COMMENT): break
        no_new_comments = True
        for index, comments_block in enumerate(comments_blocks[comment_index:], start=comment_index):
            no_new_comments = False
            # scroll_down(comments_scroll_panel, sleep=0.5)
            comment_index += 1

            expanded_button = None
            try:
                expanded_button = wait_until_execute_on_element("""
                    const expanded_button = arguments[0].querySelector("button[aria-expanded]");
                    return expanded_button;
                """, comments_block, wait=1.0)
            except TimeoutException as err:
                print("Not found expanded button, retrying...")

            if(expanded_button):
                execute_on_element("arguments[0].click();", expanded_button)
                try:
                    wait_until_execute("""
                        const expanded_button = document.querySelector("button[aria-expanded]");
                        if(expanded_button) return null;
                        return True;
                    """, wait=2)
                    print("Button disappeared, continue with next steps.")
                except TimeoutException as err:
                    print("Button did not disappear within the time limit.")

            comments_data = wait_until_execute_on_element("""
                const comments_block = arguments[0];
                const author = comments_block.getAttribute("aria-label"); /* 評論區塊的 aria-label 是作者名字*/
                const stars  = parseInt(comments_block.querySelector("span[role=img]").getAttribute("aria-label").match(/\d+/)[0], 10); /* span[role=img] 是星星數的父層，arial-label 是星數*/ 
                const comments_text_dom = comments_block.querySelector(".MyEned");
                if(!comments_text_dom) return {
                    'author'  : author,
                    'star'    : stars
                };
                const other_info_dom = Array.from(comments_text_dom.querySelectorAll("div[jslog] div")).filter(s=>s.classList.length>0);
                const other_info_arr = other_info_dom.map(div=>Array.from(div.querySelectorAll("span"))?.filter(s=>s.classList.length>0));
                const other_info_obj = other_info_arr.map(arr=>{
                    if(arr.length===2) return arr.map(s=>s.innerText);
                    const boldText = arr[0].querySelector('b')?.innerText || '';
                    const text = arr[0].innerText.replace(boldText, '').trim();
                    return [boldText.replace(/(:|：)/, ''), text];
                }).reduce((obj, item) => {obj[item[0]] = item[1]; return obj;}, { });
                return {
                    'author'  : author,
                    'star'    : stars,
                    'comment' : comments_text_dom.querySelector("span").innerText,
                    'other'   : Object.keys(other_info_obj).length ? other_info_obj : undefined
                };
            """, comments_block, wait=10)
            if(comments_data):
                all_comments_datas.append(comments_data)

        if no_new_comments: break
        
        scroll_down(comments_scroll_panel, sleep=1)

        comments_blocks =  wait_until_execute_on_element("""
            const comments_blocks = Array.from(arguments[0].querySelectorAll(':scope > div:not([role=presentation])'));
            return comments_blocks;
        """, comments_group, wait=5)
    return all_comments_datas

# ------------------------------------------------------------
# ------------------------------------------------------------

options = webdriver.ChromeOptions()
# options.add_argument('--headless') # 如果要在背景中跑的話
options.add_argument('--disable-gpu')
options.add_argument('--window-size=3024x1964')

service = Service(CHROME_DRIVER_PATH) # initialize WebDriver
driver = webdriver.Chrome(service=service, options=options)
driver.get('https://www.google.com/maps') # open Google maps

# get search input DOM
search_box = wait_until_execute("return document.querySelector('#searchboxinput');")
search_box.send_keys('甜點') # searching
search_box.send_keys(Keys.RETURN)

try:
    anchors = get_shops_anchors()
    
    processed_urls = set()  # 處理過的「網址」
    processed_names = set() # 處理過的「店名」

    while True:
        for anchor in anchors:
            # === START: for anchor loop ========================
            href = execute_on_element("return arguments[0].getAttribute('href');", anchor)
            if href in processed_urls: continue # 如果「網址」曾經處理過，則跳過這個循環
            processed_urls.add(href)
            execute_on_element("arguments[0].click();", anchor) # 點擊店面連結

            info = get_shop_information(click_button=anchor, retry_times=3, retry_sleep=5)
            if not info: break

            processed_names.add(info['title'])
            print(f"{'='*30}\n{info}") # 暫時先顯示出獲取到的「店名」、「星星數」，之後需要儲存

            comment_button = get_comments_button(retry_times=3, retry_sleep=1)
            if not comment_button: break
            execute_on_element("arguments[0].click();", comment_button)
            print("Clicked the comment button.")

            radios = get_radios(wait=10, retry_times=3, retry_sleep=1)
            print(radios)

            get_comments()

            time.sleep(0.5)
            # === END: for anchor loop ========================
        # ------------------------------------------------------------
        scroll_panel = get_shops_list_scroll_panel()
        scroll_down(scroll_panel, sleep=1)
        scroll_down(scroll_panel, sleep=2)

        # 重新獲取所有連結
        new_anchors = get_shops_anchors()

        # 如果新的連結長度與原本一樣，則跳出循環，代表沒有搜尋到內容了
        if len(new_anchors) == len(anchors): break

        anchors.extend(new_anchors[len(anchors):])
except NoSuchWindowException as err:
    print("Window Closed!")
except KeyboardInterrupt as err: 
    print("Key Interrupt => Window Closed!")
finally:
    driver.quit()
    print("Driver Quit")