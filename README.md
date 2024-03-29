# qb-ban-vampire-docker

本项目是 https://gist.github.com/Sg4Dylan/cb2c1d0ddb4559c2c46511de31ca3251 的 Docker 封装，并同时修复了当 WebAPI 超时会导致进程退出的问题。

## Docker Hub

https://hub.docker.com/r/ghostchu/qb-ban-vampire-docker

```
docker pull ghostchu/qb-ban-vampire-docker:v1.1.2
```

## 环境变量 

* API_PREFIX 填写 QB 地址如 http://192.168.0.105:8085
* API_VERIFY_HTTPS_CERT 如果你使用HTTPS自签名证书或通过局域网IP而非证书相关联的域名访问，则设置为 false 以跳过证书检查
* API_USERNAME 填写 QB 用户名
* API_PASSWORD 填写 QB 密码
* BASICAUTH_ENABLED 如果前面套了一层基础验证（浏览器弹窗输入用户名密码），则设为 true
* BASICAUTH_USERNAME 输入弹窗中要输入的用户名
* BASICAUTH_PASSWORD 输入弹窗中要输入的密码
* INTERVAL_SECONDS 检测间隔，太长封禁Peer会有较大延迟，太小会导致 QB WEBUI 无响应，推荐值为 15
* HTTP_REQUEST_RETRIES API超时重试次数限制
* HTTP_REQUEST_READ_TIMEOUT API响应超时时间，单位：秒。如果QB响应较慢，则增大此值。默认为 30 秒
* HTTP_REQUEST_CONNECTION_TIMEOUT API连接超时时间，单位：秒。如果网络拥塞或延迟较大，则增大此值。默认为 10 秒
* DEFAULT_TIMEZONE 显示时间格式化的时区，默认中国标准时间 Asia/Shanghai
* DEFAULT_LOG_LEVEL 指定日志输出级别，级别越小输出日志量越多 CRITICAL > ERROR > WARNING > INFO > DEBUG
* DEFAULT_BAN_SECONDS 封禁时间长度，默认 3600，单位为秒
* BAN_XUNLEI 是否封禁迅雷，默认 true
* BAN_PLAYER 是否封禁各类BT播放器，默认 true
* BAN_OTHER 是否封禁其他未知 BT 客户端
* BAN_WITHOUT_RADIO_CHECK 小部分版本迅雷客户端下载 BT 资源时会正常上传，此选项控制封禁BAN掉这类迅雷客户端之前是否检查其分享率。此选项设置为 true 时，不检查分享率直接封禁BAN掉客户端；设置为 false 时，封禁BAN掉客户端前先查验其分享率
