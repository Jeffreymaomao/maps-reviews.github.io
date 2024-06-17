"""
這段程式碼可以正確的開始跑了，但是現在很冗長，所以我要變成一個函數一個函數的。
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException

chrome_driver_path = '/usr/local/bin/chromedriver'  # ChromeDriver 驅動器的路徑
options = webdriver.ChromeOptions()
# options.add_argument('--headless') # 如果要在背景中跑的話
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

def scroll_down(element, sleep=1):
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
            # === START: for anchor loop ========================
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
                except TimeoutException as err:
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
                    """, search_result_panel, wait=1.5)

                    if buttons and len(buttons)==3:
                        comment_button = buttons[1]

                except TimeoutException as err:
                    print("No comment button, retrying...")
                time.sleep(1)

            if not comment_button: break
                
            execute_on_element("arguments[0].click();", comment_button)
            print("Clicked the comment button.")

            radiogroup = None
            for retry in range(3):
                if radiogroup: break
                try:
                    radiogroup = wait_until_execute_on_element("""
                        return arguments[0].querySelector("div[role=radiogroup]");
                    """, search_result_panel, wait=1.5)
                except TimeoutException as err:
                    print("No radiogroup, retrying...")
                time.sleep(1)

            radios = None
            if radiogroup:
                radios = wait_until_execute_on_element("""
                    const radios = Array.from(arguments[0].querySelectorAll("button[role=radio]"))
                        ?.map(b => {
                            const spans = b.querySelectorAll("span");
                            return spans.length === 2 ? [spans[0].innerText, spans[1].innerText] : null;
                        })
                        .filter(arr => arr !== null)
                        .reduce((obj, item) => {obj[item[0]] = parseInt(item[1], 10);return obj;}, {});
                    return radios;
                """, radiogroup, wait=10)

            comments_group = wait_until_execute_on_element("""
                /* 
                    所有評論的父元素，會在 role=presentation 的最後一個元素的父元素中，
                    因為每個 presentation 的用途會是
                    1. presentation 在評論外用於邊界
                    2. presentation 在評論外用於邊界
                    3. presentation 在評論外用於邊界
                    ...
                    n.   presentation 在評論內用於邊界
                    n+1. presentation 在評論內用於邊界
                    n+2. presentation 在評論內用於邊界
                */
                const comments_group = Array.from(arguments[0].querySelectorAll("div[role=presentation]"))?.pop()?.parentNode;
                /* 
                    如果 comments_group 裡面還有role=region，就代表還在「總覽」頁面，還沒到「評論」頁面。 
                */
                if(comments_group.querySelector("div[role=region]")) return null;
                return comments_group;
            """, search_result_panel, wait=10)

            comments_scroll_panel = wait_until_execute_on_element("""
                return arguments[0].querySelector("div[role=main]").lastChild;
            """, search_result_panel, wait=5)

            comments_blocks =  wait_until_execute_on_element("""
                const comments_blocks = Array.from(arguments[0].querySelectorAll(':scope > div:not([role=presentation])'));
                return comments_blocks;
            """, comments_group, wait=5)
            
            print(f"comments length: {len(comments_blocks)}")

            comment_index = 0
            while True:
                no_new_comments = True
                for index, comments_block in enumerate(comments_blocks[comment_index:], start=comment_index):
                    no_new_comments = False
                    # scroll_down(comments_scroll_panel, sleep=0.5)
                    comment_index += 1

                    expanded_button = None
                    try:
                        expanded_button = wait_until_execute_on_element("""
                            const expanded_button =  arguments[0].querySelector("button[aria-expanded]");
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
                            'other'   : Object.keys(other_info_obj).length?other_info_obj : undefined
                        };
                    """, comments_block, wait=10)
                    if(comments_data):
                        print(comments_data)

                if no_new_comments: break
                
                scroll_down(comments_scroll_panel, sleep=1)

                comments_blocks =  wait_until_execute_on_element("""
                    const comments_blocks = Array.from(arguments[0].querySelectorAll(':scope > div:not([role=presentation])'));
                    return comments_blocks;
                """, comments_group, wait=5)

            time.sleep(0.5)
            # === END: for anchor loop ========================
        # ------------------------------------------------------------
        # 重心獲取面板內容，因為網頁元素會重新繪製。
        search_result_panel = get_search_result_panels()
        # 獲取搜尋列表中的 role='feed' 元素，因為這是可以往下滾動的元素，可以更近一步加載網頁內容
        scroll_panel = wait_until_execute_on_element("return arguments[0].querySelector(`div[role='feed']`)", search_list_panel)
        scroll_down(scroll_panel, sleep=1)
        scroll_down(scroll_panel, sleep=2)

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