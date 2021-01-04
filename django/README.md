# Django Server

犯罪人網路前端 + 後端

## Setup

1. Git Clone

```sh
git clone https://github.com/NCHU-NLU-Lab/LegalTech-Hackathon.git
cd LegalTech-Hackathon/2019/django
```

2. 在`docker-compose.yml`中輸入資料庫設定

```yaml
...
    environment:
      - MONGO_HOST=  #資料庫IP
      - MONGO_PORT=  #資料庫Port
      - MONGO_USERNAME=  #資料庫帳號
      - MONGO_PASSWORD=  #資料庫密碼
      - MONGO_DB=Law  #database名稱
      - MONGO_NODE=Civil_Node_2019  #節點collection名稱
      - MONGO_EDGE=Civil_Edge_2019  #邊collection名稱
      - MONGO_VERDICT=Civil_Verdict_2019  #判決書collection名稱
...
```

3. 啟動

```sh
docker-compose up --build --detach
```

