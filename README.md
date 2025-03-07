# 语音助手项目

## 项目简介

这是一个基于小智AI项目的嵌入式Py设备客户端项目，添加了摄像头控制、图像、视频识别等功能。
项目将持续完善py嵌入式设备的IOT控制能力，更加大模型能力同步升级

## 功能特性

- **语音识别**：通过WebSocket实时传输音频流，支持语音指令识别。
- **语音合成**：接收服务器返回的TTS（文本到语音）数据并播放。
- **摄像头控制**：支持打开/关闭摄像头，并拍照进行图像识别。
- **图像识别**：通过API对摄像头捕获的图像进行分析，支持场景识别、物体识别等功能。
- **键盘控制**：支持通过空格键手动控制语音识别的开始和结束。
- **OTA检查**：支持检查设备固件版本。

## 项目结构

```
voice-assistant/
│
├── README.md                   # 项目说明文件
├── main.py                     # 主程序入口
├── Camera.py                   # 摄像头管理模块
├── VL.py                       # 图像识别模块
├── requirements.txt            # 项目依赖
└── config.json                 # 配置文件（示例）
```

## 依赖库

- `pyaudio`：用于音频输入输出。
- `opuslib`：用于音频编解码。
- `websocket-client`：用于WebSocket通信。
- `pynput`：用于键盘事件监听。
- `requests`：用于HTTP请求。
- `logging`：用于日志记录。

## 安装与运行

### 1. 克隆项目

```bash
git clone https://github.com/your-username/voice-assistant.git
cd voice-assistant
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置

在 `config.json` 中填写你的配置信息，例如：

```json
{
    "access_token": "your-access-token",
    "device_mac": "your-device-mac",
    "device_uuid": "your-device-uuid",
    "ws_url": "wss://api.tenclass.net/xiaozhi/v1/",
    "ota_url": "https://api.tenclass.net/xiaozhi/ota/",
    "manual_mode": false
}
```

### 4. 运行项目

```bash
python main.py
```

## 使用说明

- **语音指令**：通过语音指令控制设备，例如“打开摄像头”、“拍照”、“识别场景”等。
- **键盘控制**：
  - **空格键**：在手动模式下，按下空格键开始录音，释放空格键停止录音并发送音频数据。
  - **打断TTS**：在TTS播放过程中按下空格键可以打断当前播放。

## 配置文件说明

- `access_token`：访问令牌，用于身份验证。
- `device_mac`：设备的MAC地址。
- `device_uuid`：设备的唯一标识符。
- `ws_url`：WebSocket服务器地址。
- `ota_url`：OTA检查的API地址。
- `manual_mode`：是否启用手动模式，默认为`false`。

## 贡献

欢迎提交Issue和Pull Request来帮助改进项目。

## 许可证

本项目采用MIT许可证，详情请参阅[LICENSE](LICENSE)文件。

## 致谢

感谢所有为该项目做出贡献的开发者和测试人员。

---

**注意**：本项目仅为示例代码，实际使用时请根据需求进行修改和优化。
