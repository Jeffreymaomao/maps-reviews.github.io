import os
import re
import json
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchWindowException
# ------------------------------------------------------------
# Global Variables
driver = None
RUN_IN_BACKGROUND  = False 
MAX_NUM_OF_COMMENT = 5000
CHROME_DRIVER_PATH = '.\\bin\\chromedriver.exe'  # ChromeDriver 驅動器的路徑

SEARCH_USING_PLACE = '嘉義市'
SEARCH_BY_KEY_TYPE = '甜點'
SAVE_DATA_DIR_PATH = '.\\dat\\{}\\'.format(SEARCH_BY_KEY_TYPE)
PROCESSED_DAT_PATH = '.\\dat\\{}-PROCESSED.txt'.format(SEARCH_BY_KEY_TYPE)
LOG_DATA_FILE_PATH = '.\\dat\\{}-LOG.txt'.format(SEARCH_BY_KEY_TYPE)

SEARCH_BY_KEY_WORD = f'{SEARCH_USING_PLACE} {SEARCH_BY_KEY_TYPE}'
# ------------------------------------------------------------
# Logfile & Write File

# ------------------------------------------------------------
# Logfile & Write File

def sanitize_filename(filename):
    # 只保留字母、數字、漢字和一些常見符號
    sanitized = re.sub(r'[^\w\s-]', '', filename)
    sanitized = re.sub(r'[-\s]+', '_', sanitized).strip('_')
    return sanitized

def log_message(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp} - {message}\n"
    with open(LOG_DATA_FILE_PATH, 'a', encoding='utf-8') as f:
        f.write(log_entry)

def save_data_to_file(data, directory, filename):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
            log_message(f"Created directory: {directory}")
        filepath = os.path.join(directory, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            if isinstance(data, str):
                f.write(data)
                log_message(f"Saved text data to {filepath}")
            elif isinstance(data, (dict, list)):
                json.dump(data, f, ensure_ascii=False, indent=4)
                log_message(f"Saved JSON data to {filepath}")
            else:
                log_message("Unsupported data type. Only str, dict, and list are supported.")
                raise ValueError("Unsupported data type. Only str, dict, and list are supported.")
    except Exception as e:
        log_message(f"Error saving data to file: {e}")
        raise

def save_processed_shop_name(shop_name, comments_num):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(PROCESSED_DAT_PATH, 'a', encoding='utf-8') as f:
        f.write(f"{timestamp}\t{comments_num:>8}\t{shop_name}\n")

def read_processed_shop_names():
    processed_shop_names = set()
    if os.path.exists(PROCESSED_DAT_PATH):
        with open(PROCESSED_DAT_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split("\t")
                if len(parts) >= 3:
                    processed_shop_names.add(parts[2])
    return processed_shop_names

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
    try:
        log_message("Finding `panels`")
        panels = wait_until_execute("""
            const panels_jstcache = document.querySelector("#pane").nextSibling.querySelectorAll("div[jstcache]");
            const panels = Array.from(panels_jstcache).slice(-3); /*最後三個按鈕*/
            if(panels.length<3) return null;
            /* 0. 收合頁面按鈕面板、1. 搜尋結果卡片面板、2. 搜尋結果列表面板 */
            return panels;
        """)
        if not panels: raise Exception("Not found panels!")
        (search_list_panel, search_result_panel, _) = panels

        log_message("Found `panels`!")
        return search_result_panel, search_list_panel

    except Exception as e:
        log_message(f"Error when finding panels: {e}")
        raise

def get_search_result_panels(wait=10):
    try:
        log_message("Finding `search_result_panels`")

        search_result_panel, search_list_panel = get_panels()
        search_result = wait_until_execute_on_element("""
            return arguments[0].querySelector("div[role=main]")
        """, search_result_panel, wait)
        log_message("Found `search_result_panels`!")
        
        return search_result_panel

    except Exception as e:
        log_message(f"Error when finding `search_result_panels`: {e}")
        raise
# ------------------------------------------------------------
def get_shops_anchors():
    try:
        log_message("Finding `shops_anchors`")

        _, search_list_panel = get_panels()
        anchors = wait_until_execute_on_element("""
            return Array.from(arguments[0].querySelectorAll("a"))
                .filter(a=>a.href.includes("https://www.google.com/maps/place"));
        """, search_list_panel)

        log_message("Found `shops_anchors`!")
        
        return anchors

    except Exception as e:
        log_message(f"Error when finding `shops_anchors`: {e}")
        raise

def get_shops_list_scroll_panel():
    try:
        log_message("Finding `shops_list_scroll_panel`")

        _, search_list_panel = get_panels()
        scroll_panel = wait_until_execute_on_element("""
            return arguments[0].querySelector(`div[role='feed']`)
        """, search_list_panel)

        log_message("Found `shops_list_scroll_panel`!")
        
        return scroll_panel

    except Exception as e:
        log_message(f"Error when finding `shops_list_scroll_panel`: {e}")
        raise

def get_shop_information(click_button=None, retry_times=3, retry_sleep=1):
    if not click_button:
        raise Exception("Must input the `click_button`!")

    log_message("Finding `shop_information`")

    info = None
    for retry in range(retry_times):
        if info: break
        try:
            log_message(f"Try-{retry+1} to find `shop information`")

            search_result_panel = get_search_result_panels()
            info = wait_until_execute_on_element("""
                const name = arguments[0].querySelector("h1")?.innerText || null;
                if (!name) return null;
                
                const rating = arguments[0].querySelector("[role='img']")?.parentNode?.innerText || null;
                const server = Array.from(arguments[0].querySelectorAll("div[role=group]")).map(g => g?.getAttribute("aria-label") || null);
                const shops_type = arguments[0].querySelector("span > span > button")?.innerText || null;
                
                const shops_other_info = arguments[0].querySelectorAll("div[role=region]")[2];
                if(!shops_other_info) return { name, rating, server, shops_type};
                
                const address = shops_other_info?.querySelector("button[data-item-id='address']")?.innerText.split('\\n').pop() || null;

                const authority = shops_other_info.querySelector("*[data-item-id=authority]")?.href || null;
                const oloc = shops_other_info.querySelector("*[data-item-id=oloc]")?.innerText?.split('\\n').pop() || null;
                const phone = shops_other_info.querySelector("*[data-item-id^=phone]")?.innerText.split('\\n').pop() || null;
                const open_time = shops_other_info.querySelector("table")?.parentNode?.parentNode?.getAttribute("aria-label") || null;

                return { name, rating, server, shops_type, address, authority, oloc, phone, open_time };
            """, search_result_panel, wait=retry_sleep+1)

            log_message(f"Found `shop information`!")

        except TimeoutException as err:
            log_message("Not found `shop information`! retrying...")
            execute_on_element("arguments[0].click();", click_button)

        time.sleep(retry_sleep)
    return info

def get_comments_button(retry_times=3, retry_sleep=1):
    comment_button = None
    for retry in range(retry_times):
        if comment_button: break
        try:
            log_message(f"Try-{retry+1} to find `comment button`")
            search_result_panel = get_search_result_panels()
            # 等待評論按鈕出現，並點擊
            buttons = wait_until_execute_on_element("""
                const buttons = Array.from(arguments[0].querySelectorAll("div[role=tablist] button"));
                if(buttons.length===0) return null;
                return buttons;
            """, search_result_panel, wait=retry_sleep+0.5)

            if buttons and len(buttons)==3:
                comment_button = buttons[1]
                log_message("Found `comment button`!")

        except TimeoutException as err:
            log_message("Not found `comment button`, retrying...")
        time.sleep(retry_sleep)

    return comment_button

def get_radios(wait=10, retry_times=3, retry_sleep=1):
    radiogroup = None
    for retry in range(retry_times):
        if radiogroup: break
        try:
            log_message(f"Try-{retry+1} to find `radiogroup`")
            search_result_panel = get_search_result_panels()
            radiogroup = wait_until_execute_on_element("""
                return arguments[0].querySelector("div[role=radiogroup]");
            """, search_result_panel, wait=retry_sleep+0.5)
        except TimeoutException as err:
            log_message("Not found radiogroup, retrying...")
        time.sleep(retry_sleep)

    if not radiogroup:
        log_message("Failed to find `radiogroup` after multiple retries")
        return None

    log_message("Found `radiogroup`! Finding `radios`")
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

    log_message(f"Found `radios`!")
    return radios
# --------
def get_comments_scroll_panel():
    search_result_panel = get_search_result_panels()
    comments_scroll_panel = wait_until_execute_on_element("""
        return arguments[0].querySelector("div[role=main]").lastChild;
    """, search_result_panel, wait=5)
    return comments_scroll_panel

def get_comments_group(comments_scroll_panel, retry_times=10, retry_sleep=5):
    search_result_panel = get_search_result_panels()
    comments_group = None
    for retry in range(retry_times):
        if comments_group: break
        try:
            log_message(f"Try-{retry+1} to find `comments group`")
            comments_group = wait_until_execute_on_element("""
                /* 會在 role=presentation 的最後一個元素，會是用在評論中做分隔，其父元素為「評論」頁面的群組。 */
                const comments_group = Array.from(arguments[0].querySelectorAll("div[role=presentation]"))?.pop()?.parentNode;
                /* 如果 comments_group 裡面還有role=region，就代表還在「總覽」頁面，還沒到「評論」頁面。 */
                if(comments_group.querySelector("div[role=region]")) return null;

                const comments_blocks_length = Array.from(comments_group.querySelectorAll(':scope > div:not([role=presentation])'))
                    .filter(dom=>dom?.getAttribute("aria-label")).length;
                if(!comments_blocks_length) return null;
                return comments_group;
            """, search_result_panel, wait=retry_sleep+0.5)
        except TimeoutException as err:
            log_message("Not found `comments group`, retrying...")
            scroll_down(comments_scroll_panel, sleep=retry_sleep)
    log_message("Found `comments_group`!")
    return comments_group

def get_comments_blocks(comments_group, retry_times=10, retry_sleep=3):
    comments_blocks = None
    for retry in range(retry_times):
        if comments_blocks: break
        try:
            log_message(f"Try-{retry+1} to find `comments blocks`")
            comments_blocks =  wait_until_execute_on_element("""
                const comments_blocks = Array.from(arguments[0].querySelectorAll(':scope > div:not([role=presentation])'));
                return comments_blocks;
            """, comments_group, wait=retry_sleep+0.5)
        except TimeoutException as err:
            log_message("Not found `comments blocks`, retrying...")
            scroll_down(comments_scroll_panel, sleep=retry_sleep)
    return comments_blocks

def get_comments():
    log_message("Finding comments")
    
    comments_scroll_panel = get_comments_scroll_panel()

    scroll_down(comments_scroll_panel, sleep=1)
    
    comments_group = get_comments_group(comments_scroll_panel, retry_times=10, retry_sleep=5)
    comments_blocks =  get_comments_blocks(comments_group, retry_times=10, retry_sleep=3)

    all_comments_datas = []
    comment_index = 0
    while True:
        if(comment_index > MAX_NUM_OF_COMMENT):
            log_message("Reached max number of comments, stopping")
            break
        no_new_comments = True
        for index, comments_block in enumerate(comments_blocks[comment_index:], start=comment_index):
            no_new_comments = False
            # scroll_down(comments_scroll_panel, sleep=0.5)
            comment_index += 1
            print(f"\rFinding {comment_index}-th comment...", end="")

            expanded_button = None
            for retry in range(3):
                if(expanded_button): break
                try:
                    expanded_button = wait_until_execute_on_element("""
                        const expanded_button = arguments[0].querySelector("button[aria-expanded]");
                        return expanded_button;
                    """, comments_block, wait=0.5)
                except TimeoutException as err:
                    time.sleep(0.5)
                    log_message("Not found `expanded button`, retrying...")

            if(expanded_button):
                execute_on_element("arguments[0].click();", expanded_button)
                try:
                    wait_until_execute("""
                        const expanded_button = document.querySelector("button[aria-expanded]");
                        if(expanded_button) return null;
                        return True;
                    """, wait=2)
                except TimeoutException as err:
                    log_message("`expanded button` did not disappear within the time limit.")

            log_message(f"Finding `comment`-{comment_index+1} in block")
            comments_data = wait_until_execute_on_element("""
                const comments_block = arguments[0];
                if(!comments_block || !comments_block.getAttribute) return null;
                
                let author = comments_block?.getAttribute("aria-label"); /* 評論區塊的 aria-label 是作者名字*/
                if(!author){
                    author = comments_block?.querySelectorAll("button")[1]?.querySelector("div").innerText;
                }
                if(!author)  return null;
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
                log_message("Found `comment` in block!")
                all_comments_datas.append(comments_data)
            else:
                log_message("Not found comment in block")

        if no_new_comments:
            log_message("No new comments found, stopping")
            time.sleep(1)
            break
        
        scroll_down(comments_scroll_panel, sleep=1)

        log_message(f"Re-finding comment_blocks")
        comments_blocks =  wait_until_execute_on_element("""
            const comments_blocks = Array.from(arguments[0].querySelectorAll(':scope > div:not([role=presentation])'));
            return comments_blocks;
        """, comments_group, wait=5)
    print("")
    return all_comments_datas

# ------------------------------------------------------------
# ------------------------------------------------------------
options = webdriver.ChromeOptions()
options.add_argument('--disable-gpu')
options.add_argument('--window-size=3024x1964')
if(RUN_IN_BACKGROUND): options.add_argument('--headless') # 如果要在背景中跑的話

service = Service(CHROME_DRIVER_PATH) # initialize WebDriver
driver = webdriver.Chrome(service=service, options=options)
driver.get('https://www.google.com/maps') # open Google maps

# get search input DOM
search_box = wait_until_execute("return document.querySelector('#searchboxinput');")
search_box.send_keys(SEARCH_BY_KEY_WORD) # searching keys
search_box.send_keys(Keys.RETURN)

log_message(f"search by key word {SEARCH_BY_KEY_WORD}")
print(f"search by key word {SEARCH_BY_KEY_WORD}")

try:
    anchors = get_shops_anchors()
    
    processed_hrefs = set()
    processed_names = read_processed_shop_names()

    while True:
        for anchor in anchors:
            # === START: for anchor loop ========================
            shop_data = {}
            href = execute_on_element("return arguments[0].getAttribute('href');", anchor)
            if href in processed_hrefs: continue
            processed_hrefs.add(href)
            execute_on_element("arguments[0].click();", anchor)

            info = get_shop_information(click_button=anchor, retry_times=3, retry_sleep=2)
            if not info: break
            shop_data.update(info)
            if info['name'] in processed_names:
                print(f"The shop `{info['name']}` name has already been processed!")
                log_message(f"The shop `{info['name']}` name has already been processed!")
                continue
            processed_names.add(info['name'])

            print(f"{'='*30}\n{info['name']}")

            comment_button = get_comments_button(retry_times=3, retry_sleep=1)
            if not comment_button: break
            execute_on_element("arguments[0].click();", comment_button)

            radios = get_radios(wait=10, retry_times=3, retry_sleep=1)
            shop_data['radios'] = radios

            comments = get_comments()
            shop_data['comments'] = comments

            filename = sanitize_filename(info['name'])
            save_data_to_file(shop_data, SAVE_DATA_DIR_PATH, f"{filename}.json")
            save_processed_shop_name(info['name'], len(comments))

            time.sleep(0.5)
            # === END: for anchor loop ========================
        # ------------------------------------------------------------
        scroll_panel = get_shops_list_scroll_panel()
        scroll_down(scroll_panel, sleep=1)
        scroll_down(scroll_panel, sleep=2)

        new_anchors = get_shops_anchors()
        if len(new_anchors) == len(anchors): break

        anchors.extend(new_anchors[len(anchors):])
except NoSuchWindowException as err:
    print(f"\n{'='*30}\nWindow Closed!")
except KeyboardInterrupt as err: 
    print(f"\n{'='*30}\nKey Interrupt => Window Closed!")
finally:
    driver.quit()
    print(f"\n\nDriver Quit")