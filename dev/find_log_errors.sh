# Home Assistant 日志位置

# Docker 安装：
docker logs homeassistant -f --tail 100 | grep -i "dreame\|error\|failed"

# 或者查看完整日志文件：
# 日志通常在：/config/home-assistant.log

# 查找最近的错误：
tail -100 /config/home-assistant.log | grep -i "self.*clean\|siid\|aiid"
