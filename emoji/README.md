# Unicode Emoji
> © 2023 Unicode®, Inc.
> Unicode and the Unicode Logo are registered trademarks of Unicode, Inc. in the U.S. and other countries.
> For terms of use, see https://www.unicode.org/terms_of_use.html

This directory contains final data files for Unicode Emoji, Version 15.1

Public/emoji/15.1/

- emoji-sequences.txt
- emoji-zwj-sequences.txt
- emoji-test.txt

The following related files are found in the UCD for Version 15.1

Public/15.1.0/ucd/emoji/

- emoji-data.txt
- emoji-variation-sequences.txt

For documentation, see UTS #51 Unicode Emoji, Version 15.1

---

# Chinese Emoji

> https://tw.piliapp.com/emoji/list/

```js
// 選擇所有包含emoji和描述的元素
let emojiElements = Array.from(document.querySelectorAll(".content span.emoji, .content span.name"));

// 初始化一個空對象來存儲emoji和描述
let emojiToText = {};

// 遍歷所有元素，提取emoji和描述
emojiElements.forEach((element, index) => {
    let emojiChar = element.getAttribute('data-c');
    let description = element.getAttribute('title');
    if(!emojiChar) return;
    emojiToText[emojiChar] = description;
});

// 將對象轉換為JSON格式
let emojiToTextJson = JSON.stringify(emojiToText, null, 4);

// 將JSON數據輸出到控制台
console.log(emojiToTextJson);

// 可選：將JSON數據導出到文件（僅在瀏覽器支持的情況下）
let blob = new Blob([emojiToTextJson], { type: 'application/json' }); let url = URL.createObjectURL(blob);
let a = document.createElement('a');
a.href = url; a.download = 'emoji_to_text_cn.json'; document.body.appendChild(a); a.click();
document.body.removeChild(a); URL.revokeObjectURL(url);
```

