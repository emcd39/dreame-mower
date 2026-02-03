# 抓包获取设备 siid/aiid 指南

## 方法 1：使用 mitmproxy 抓包（推荐）

### 1. 安装 mitmproxy
```bash
pip install mitmproxy
```

### 2. 启动代理
```bash
mitmproxy -listen-port 8080
```

### 3. 配置手机代理
- iPhone: 设置 → 无线局域网 → HTTP 代理 → 手动 → 服务器: 你的电脑IP, 端口: 8080
- Android: 长按 WiFi → 修改网络 → 高级选项 → 代理 → 手动

### 4. 安装证书
- 在手机浏览器访问: `http://mitm.it`
- 下载并安装证书

### 5. 打开 Dreamehome App
- 执行操作（如自清洁）
- 在 mitmproxy 中查看请求

### 6. 关键接口
查找以下 URL:
- `.../homeroom/get` - 获取房间和设备信息
- `.../deviceprops` - 获取设备属性
- `.../methodlist` - 获取设备方法
- `.../action` - 执行设备操作

---

## 方法 2：使用 mitmweb（图形界面）

```bash
mitmweb -listen-port 8080
```

会自动打开浏览器，可以看到所有请求的详细内容。

---

## 方法 3：从云端获取（最简单）

运行脚本：
```bash
cd e:\projects\dreame-mower
python dev/get_device_methods_from_cloud.py \
  --username "你的邮箱" \
  --password "密码" \
  --country cn \
  --device-id -110294569
```

---

## 要查找的信息

### 在抓包数据中查找：

**1. 查找设备属性**
```json
{
  "siid": 6,
  "piid": 1,
  "name": "SelfCleanState",
  "value": 0
}
```

**2. 查找可执行方法**
```json
{
  "siid": 6,
  "aiid": 1,
  "name": "StartSelfClean"
}
```

**3. 关键词搜索**
- 英文: `clean`, `wash`, `self`, `dry`, `roll`, `mop`
- 中文: `洗`, `自清洁`, `烘干`, `滚刷`

---

## 示例：找到自清洁方法

假设抓包中看到：
```json
{
  "result": [
    {"siid": 6, "aiid": 1, "name": "StartSelfClean"},
    {"siid": 6, "aiid": 2, "name": "StopSelfClean"},
    {"siid": 7, "aiid": 1, "name": "StartDrying"}
  ]
}
```

那么在代码中设置：
```python
HOLD_ACTION_START_SELF_CLEAN = ActionIdentifier(siid=6, aiid=1, name="start_self_clean")
HOLD_ACTION_START_DRYING = ActionIdentifier(siid=7, aiid=1, name="start_drying")
```
