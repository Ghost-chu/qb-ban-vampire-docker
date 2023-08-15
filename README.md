# qb-ban-vampire-docker

本项目是 https://gist.github.com/Sg4Dylan/cb2c1d0ddb4559c2c46511de31ca3251 的 Docker 封装，并同时修复了当 WebAPI 超时会导致进程退出的问题。

## Docker Hub

https://hub.docker.com/r/ghostchu/qb-ban-vampire-docker

```
docker pull ghostchu/qb-ban-vampire-docker:1.1
```

## 环境变量 

* API_PREFIX 填写 QB 地址如 http://192.168.0.105:8085
* API_USERNAME 填写 QB 用户名
* API_PASSWORD 填写 QB 密码
* BASICAUTH_ENABLED 如果前面套了一层基础验证（浏览器弹窗输入用户名密码），则设为 true
* BASICAUTH_USERNAME 输入弹窗中要输入的用户名
* BASICAUTH_PASSWORD 输入弹窗中药输入的密码
* INTERVAL_SECONDS 检测间隔，太长封禁Peer会有较大延迟，太小会导致 QB WEBUI 无响应，推荐值为 15
* DEFAULT_BAN_SECONDS 封禁时间长度，默认 3600，单位为秒
* BAN_XUNLEI 是否封禁迅雷，默认 true
* BAN_PLAYER 是否封禁各类BT播放器，默认 true
* BAN_OTHER 是否封禁其他未知 BT 客户端
* BAN_WITHOUT_RADIO_CHECK 小部分版本迅雷客户端下载 BT 资源时会正常上传，此选项控制封禁BAN掉这类迅雷客户端之前是否检查其分享率
