# 犯罪人網路

_LegalTech Hackathon 2019_

將主辦方提供的歷年判決書整理進 Database ，然後將出現在同一篇判決書的犯罪人建立 Node 和 Edge，並使用網頁呈現犯罪人網路

## System Structure

- 前端：Vanilla JavaScript, jQuery, D3.js
- 後端：Django
- 資料庫：MongoDB

## Rebuild

1. 建立 MongoDB
2. 存入資料 (詳見[`data_processing/README`](data_processing/README.md))
3. 啟動網頁介面 (詳見[`django/README`](django/README.md))

## Credit

The original version of this project lives at [booker2681/LawDjango](https://github.com/booker2681/LawDjango)