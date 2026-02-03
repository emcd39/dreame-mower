# H20 自清洁功能测试指南

## 背景

通过 API 探索发现：
- **设备型号**: dreame.hold.w2422 (H20 Ultra)
- **功能特性**: `hold_selfClean_selfCleanDeep` - 支持自清洁和深度自清洁
- **bindDomain**: 10000.mt.cn.iot.dreame.tech:19973
- **基本控制** (siid=5): ✅ 工作正常

## 问题

之前使用的 siid=16/17（基站服务）对 H20 手持设备无效。

## 解决方案

H20 是**手持洗地机**，不是机器人洗地机，没有基站。自清洁功能应该直接在设备本身上，而不是基站。

### 已尝试的 siid/aiid 组合

当前代码已更新为使用更可能的值：

```python
# 自清洁 (siid=6 - 常见清洁服务)
HOLD_ACTION_START_SELF_CLEAN = ActionIdentifier(siid=6, aiid=1, name="start_self_clean")
HOLD_ACTION_STOP_SELF_CLEAN = ActionIdentifier(siid=6, aiid=2, name="stop_self_clean")

# 深度清洁 (siid=6, aiid=3)
HOLD_ACTION_START_DEEP_CLEAN = ActionIdentifier(siid=6, aiid=3, name="start_deep_clean")

# 烘干 (siid=7 - 常见烘干服务)
HOLD_ACTION_START_DRYING = ActionIdentifier(siid=7, aiid=1, name="start_drying")
HOLD_ACTION_STOP_DRYING = ActionIdentifier(siid=7, aiid=2, name="stop_drying")
```

## 测试步骤

### 1. 重启 Home Assistant

在 HA 中：**设置 → 系统 → 硬件 → 重启**

### 2. 测试按钮

重启后，你的 H20 设备应该有三个按钮：
- Self Clean
- Deep Clean
- Drying

点击每个按钮，观察：
- 按钮是否消失（表示发送成功）
- 设备是否有响应
- HA 日志中是否有错误

### 3. 查看日志

**设置 → 系统 → 日志**，搜索：
- `dreame_mower`
- `Failed to send`
- `action failed`

### 4. 如果仍然不工作

在 `const.py` 中尝试其他 siid/aiid 组合。已包含注释掉的备选方案：

```python
# 选项 1: siid=4 (状态/模式控制)
HOLD_ACTION_START_SELF_CLEAN = ActionIdentifier(siid=4, aiid=1, name="start_self_clean")

# 选项 2: 使用相同的 siid=5（基本控制）
HOLD_ACTION_START_SELF_CLEAN = ActionIdentifier(siid=5, aiid=3, name="start_self_clean")
```

修改后重启 HA 并重新测试。

## 常见 siid 说明

| siid | 用途 | 可能性 |
|------|------|--------|
| 4 | 设备状态/模式控制 | ⭐⭐⭐ |
| 5 | 主清洁控制（已确认工作） | ⭐⭐ |
| 6 | 清洁/自清洁服务 | ⭐⭐⭐⭐ |
| 7 | 烘干服务 | ⭐⭐⭐⭐ |
| 8 | 刷子/滤网维护 | ⭐⭐ |
| 16-18 | 基站服务（H20 无基站） | ❌ |

## 手动通过 API 测试

如果 HA 测试不方便，可以使用开发工具：

```bash
cd e:\projects\dreame-mower

# 测试单个动作
python -c "
import sys
sys.path.insert(0, '.')
from custom_components.dreame_mower.dreame.cloud.cloud_device import DreameMowerCloudDevice
from custom_components.dreame_mower.dreame.const import ActionIdentifier

device = DreameMowerCloudDevice(
    username='13484216239',
    password='jy01867382',
    country='cn',
    account_type='dreame',
    device_id='-110294569'
)

device.connect(
    message_callback=lambda x: print(f'MQTT: {x}'),
    connected_callback=lambda: print('Connected'),
    disconnected_callback=lambda: print('Disconnected')
)

# 测试动作
action = ActionIdentifier(siid=6, aiid=1, name='test')
result = device.execute_action(action)
print(f'Result: {result}')
"
```

## 通过 App 抓包获取准确信息

如果以上方法都不工作，最可靠的方法是抓包：

1. 安装 mitmproxy: `pip install mitmproxy`
2. 启动代理: `mitmweb -listen-port 8080`
3. 配置手机代理（见 [PACKET_CAPTURE_GUIDE.md](PACKET_CAPTURE_GUIDE.md)）
4. 在 Dreamehome App 中触发自清洁
5. 在 mitmweb 中查找 `action` 请求
6. 找到正确的 siid/aiid

## 预期 MQTT 消息

如果动作成功，你会看到类似这样的 MQTT 消息：

```json
{
  "data": {
    "prop.s_auth_config": "...",
    "prop.s_custom_radio": "false",
    "prop.s_status_code": "5"  # 自清洁状态
  }
}
```

状态码对应：
- 5: 自清洁中 (self_cleaning)
- 6: 烘干中 (drying)
- 26: 热水自清洁 (hot_water_cleaning)
- 27: 深度热水自清洁 (deep_cleaning)

## 成功标志

如果找到正确的 siid/aiid：
1. ✅ 点击按钮后按钮保持可见
2. ✅ 设备开始执行相应的动作
3. ✅ MQTT 收到状态更新消息
4. ✅ HA 日志显示 "✓ SUCCESS" 或没有错误

## 联系方式

如果测试后仍有问题，请提供：
1. HA 日志截图
2. 测试的 siid/aiid 值
3. 设备响应情况
