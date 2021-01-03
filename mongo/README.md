# Database

使用 Docker Compose 建立 MongoDB + Mongo Express 的環境

**⚠️ Mongo Express 是方便用來 debug 和管理資料庫的，使用 HTTP Basic Auth 實作密碼介面，在非 https 的環境可能會有密碼被監聽的風險，平時應該保持關閉 ⚠️**

## Setup

1. 在主機端建立一個目錄
2. `cd` 進目錄後，放入 `docker-compose.yml`
3. 修改 `docker-compose.yml`

```yaml
...
  mongo:
  	...
    environment:
      MONGO_INITDB_ROOT_USERNAME: "" # 帳號；預設用 "verdict"
      MONGO_INITDB_ROOT_PASSWORD: "" # 密碼；可以用 `openssl rand -base64 32` 產生
 ...
  mongo-express: # 如果要關閉，整個註解掉後再執行一次 4.
  	...
    environment:
      ME_CONFIG_BASICAUTH_USERNAME: "" # HTTP Basic Auth 帳號
      ME_CONFIG_BASICAUTH_PASSWORD: "" # HTTP Basic Auth 密碼
      ME_CONFIG_MONGODB_ADMINUSERNAME: "" # 同 line 8
      ME_CONFIG_MONGODB_ADMINPASSWORD: "" # 同 line 9
...
```

4. 啟動

```shell
docker-compose up --detach
```

