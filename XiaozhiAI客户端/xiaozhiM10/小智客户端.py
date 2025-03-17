import json
import requests
import threading
import pyaudio
import opuslib
import websocket
from pynput import keyboard as pynput_keyboard
import logging
from xiaozhiM10.src.iot.thing_manager import ThingManager

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class WebSocketClient:
    """WebSocket客户端类，处理连接、消息收发和事件回调"""
    def __init__(self, url, headers, message_handler):
        """
        初始化WebSocket客户端
        :param url: WebSocket服务器地址
        :param headers: 连接头信息
        :param message_handler: 消息处理回调函数
        """
        self.ws = None
        self.url = url
        self.headers = headers
        self.message_handler = message_handler
        self.is_connected = False
        self.thread = None

    def connect(self):
        """建立WebSocket连接并启动监听线程"""
        self.ws = websocket.WebSocketApp(
            self.url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
            header=self.headers
        )
        self.thread = threading.Thread(target=self.ws.run_forever)
        self.thread.start()

    def disconnect(self):
        """主动关闭WebSocket连接"""
        if self.ws:
            self.ws.close()

    def send_message(self, message,frame_base64=None):
        """
        发送消息（支持文本和二进制）
        :param message: 要发送的消息内容（字典或字节）
        """
        try:
            if frame_base64 is not None:
                if  '192' in config['ws_url']:
                    # 构造消息
                    vl_message = {
                        "type": "VL",
                        "image": frame_base64,
                        'text': message,
                        "version": 1,
                        "transport": "websocket",
                        "audio_params": {
                            "format": "opus",
                            "sample_rate": 16000,
                            "channels": 1,
                            "frame_duration": 60
                        }
                    }
                    self.ws.send(json.dumps(vl_message))
                else:
                    pass
            else:
                if isinstance(message, dict):
                    self.ws.send(json.dumps(message))
                    logging.info(f"Sent JSON message: {message}")
                elif isinstance(message, bytes):
                    self.ws.send(message, opcode=websocket.ABNF.OPCODE_BINARY)
        except Exception as e:
            logging.error(f"发送消息失败: {e}")

    def _on_open(self, ws):
        """连接建立回调"""
        self.is_connected = True
        logging.info("WebSocket连接已建立")
        # 发送初始化握手消息
        hello_msg = {
            "type": "hello",
            "version": 1,
            "transport": "websocket",
            "audio_params": {
                "format": "opus",
                "sample_rate": 16000,
                "channels": 1,
                "frame_duration": 60
            }
        }
        self.send_message(hello_msg)

    def _on_message(self, ws, message):
        """消息接收回调"""
        self.message_handler(message)

    def _on_error(self, ws, error):
        """错误处理回调"""
        logging.error(f"WebSocket错误: {error}")

    def _on_close(self, ws, close_status_code, close_msg):
        """连接关闭回调"""
        self.is_connected = False
        logging.info("WebSocket连接已关闭")


class AudioHandler:
    """音频处理类，负责音频输入输出和编解码"""
    def __init__(self, sample_rate=16000, channels=1, chunk_size=960):
        """
        初始化音频处理器
        :param sample_rate: 采样率（默认16000Hz）
        :param channels: 声道数（默认单声道）
        :param chunk_size: 每次处理的音频块大小（默认960 samples/60ms）
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.pyaudio = pyaudio.PyAudio()
        self.input_stream = None
        self.output_stream = None
        self.encoder = opuslib.Encoder(sample_rate, channels, opuslib.APPLICATION_AUDIO)
        self.decoder = opuslib.Decoder(sample_rate, channels)

    def open_input_stream(self):
        """打开音频输入流"""
        self.input_stream = self.pyaudio.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size
        )

    def open_output_stream(self):
        """打开音频输出流"""
        self.output_stream = self.pyaudio.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=self.sample_rate,
            output=True,
            frames_per_buffer=self.chunk_size
        )

    def encode_audio(self, pcm_data):
        """将PCM数据编码为OPUS格式"""
        return self.encoder.encode(pcm_data, self.chunk_size)

    def decode_audio(self, opus_data):
        """将OPUS数据解码为PCM格式"""
        return self.decoder.decode(opus_data, self.chunk_size)

    def close(self):
        """释放所有音频资源"""
        if self.input_stream:
            self.input_stream.stop_stream()
            self.input_stream.close()
        if self.output_stream:
            self.output_stream.stop_stream()
            self.output_stream.close()
        self.pyaudio.terminate()


class VoiceAssistant:
    """语音助手主控制类"""
    def __init__(self, config):
        """
        初始化语音助手
        :param config: 配置字典，包含访问令牌、设备信息等
        """
        # 初始化配置参数
        self.config = config
        self.is_manual_mode = config.get('manual_mode', False)
        self.session_id = None
        self.tts_state = "idle"
        self.listen_state = "stop"
        self.key_state = "release"

        # 初始化组件
        self.audio_handler = AudioHandler()
        self.ws_client = WebSocketClient(
            url=config['ws_url'],
            headers={
                "Authorization": f"Bearer {config['access_token']}",
                "Protocol-Version": "1",
                "Device-Id": config['device_mac'],
                "Client-Id": config['device_uuid']
            },
            message_handler=self.handle_message
        )
        self.keyboard_listener = pynput_keyboard.Listener(
            on_press=self.on_key_press,
            on_release=self.on_key_release
        )
        # 启动音频设备
        self.audio_handler.open_input_stream()
        self.audio_handler.open_output_stream()
        self.thing_manager=ThingManager.get_instance()

    def start(self):
        """启动语音助手服务"""
        # 检查固件版本
        self.check_ota_version()
        # 连接WebSocket服务器
        self.ws_client.connect()
        # 启动键盘监听
        self.keyboard_listener.start()
        # 启动音频发送线程
        self.audio_send_thread = threading.Thread(target=self.send_audio)
        self.audio_send_thread.start()
        #初始化IOT设备
        self._initialize_iot_devices()

    def check_ota_version(self):
        """检查OTA固件版本"""
        try:
            response = requests.post(
                self.config['ota_url'],
                headers={'Device-Id': self.config['device_mac']},
                json=self.config['ota_data']
            )
            data = response.json()
            logging.info(f"当前固件版本: {data['firmware']['version']}")
        except Exception as e:
            logging.error(f"OTA检查失败: {e}")

    def send_audio(self):
        """音频发送线程主循环"""
        while True:
            if self.listen_state != "start" or not self.ws_client.is_connected:
                continue

            try:
                # 读取并编码音频数据
                pcm_data = self.audio_handler.input_stream.read(self.audio_handler.chunk_size)
                opus_data = self.audio_handler.encode_audio(pcm_data)
                # 发送二进制音频数据
                self.ws_client.send_message(opus_data)
            except Exception as e:
                logging.error(f"音频发送失败: {e}")

    def handle_message(self, message):
        """处理来自服务器的消息"""
        try:
            # 二进制消息处理（音频数据）
            if isinstance(message, bytes):
                #print('收到服务端语音消息')
                pcm_data = self.audio_handler.decode_audio(message)
                self.audio_handler.output_stream.write(pcm_data)
                return
            # 文本消息处理
            msg = json.loads(message)
            logging.info(f"收到服务器消息: {msg}")
            # 处理会话初始化消息
            if msg['type'] == 'hello':
                self.session_id = msg['session_id']
                self.start_listening()
            # 处理TTS状态更新
            elif msg['type'] == 'tts':
                self.tts_state = msg['state']
                if msg['state'] == 'stop':
                    self.start_listening()
            # 处理会话终止消息
            elif msg['type'] == 'goodbye':
                self.session_id = None
                self.listen_state = "stop"
            elif msg['type'] == 'iot':
                print('iot处理')
                self._handle_iot_message(msg)
        except json.JSONDecodeError:
            logging.error("收到非JSON格式消息")

    def start_listening(self):
        """启动语音监听"""
        if not self.is_manual_mode and self.ws_client.is_connected:
            self.listen_state = "start"
            self.ws_client.send_message({
                "session_id": self.session_id,
                "type": "listen",
                "state": "start",
                "mode": "auto"
            })

    def on_key_press(self, key):
        """键盘按下事件处理"""
        if key == pynput_keyboard.Key.space:
            self.handle_space_key()

    def on_key_release(self, key):
        """键盘释放事件处理"""
        if key == pynput_keyboard.Key.space:
            self.key_state = "release"
            if self.is_manual_mode:
                self.stop_listening()

    def handle_space_key(self):
        """处理空格键操作"""
        if self.key_state == "press":
            return
        self.key_state = "press"

        # 需要重新连接的情况
        if not self.ws_client.is_connected:
            self.ws_client.connect()
            return

        # 打断当前语音播放
        if self.tts_state in ["start", "sentence_start"]:
            self.ws_client.send_message({"type": "abort"})

        # 手动模式开始录音
        if self.is_manual_mode:
            self.listen_state = "start"
            self.ws_client.send_message({
                "session_id": self.session_id,
                "type": "listen",
                "state": "start",
                "mode": "manual"
            })

    def stop_listening(self):
        """停止语音监听"""
        if self.ws_client.is_connected:
            self.listen_state = "stop"
            self.ws_client.send_message({
                "session_id": self.session_id,
                "type": "listen",
                "state": "stop"
            })



    def _handle_iot_message(self, data):
        """处理物联网消息"""
        from src.iot.thing_manager import ThingManager
        thing_manager = ThingManager.get_instance()

        commands = data.get("commands", [])
        print(commands)
        for command in commands:
            try:
                result = thing_manager.invoke(command)
                print(f"执行物联网命令结果: {result}")

                # 命令执行后更新设备状态
                self._update_iot_states()
            except Exception as e:
                print(f"执行物联网命令失败: {e}")

    def _update_iot_states(self):
        """更新物联网设备状态"""
        from src.iot.thing_manager import ThingManager
        thing_manager = ThingManager.get_instance()

        # 获取当前设备状态
        states_json = thing_manager.get_states_json()
        print(states_json)
        # 发送状态更新
        self.send_iot_states(states_json)
        print("物联网设备状态已更新")

    def send_iot_descriptors(self, descriptors):
        """发送物联网设备描述信息"""
        message = {
            "session_id": self.session_id,
            "type": "iot",
            "descriptors": json.loads(descriptors) if isinstance(descriptors, str) else descriptors
        }
        print(message)
        self.ws_client.send_message(message)

    def send_iot_states(self, states):
        """发送物联网设备状态信息"""
        message = {
            "session_id": self.session_id,
            "type": "iot",
            "states": json.loads(states) if isinstance(states, str) else states
        }
        self.ws_client.send_message(message)

    def _initialize_iot_devices(self):
        """初始化物联网设备"""
        from src.iot.thing_manager import ThingManager
        from src.iot.things.lamp import Lamp
        from src.iot.things.speaker import Speaker
        from src.iot.things.Camera import Camera
        # 获取物联网设备管理器实例
        thing_manager = ThingManager.get_instance()
        # 添加设备
        thing_manager.add_thing(Lamp())
        thing_manager.add_thing(Speaker())
        thing_manager.add_thing(Camera())
        self.send_iot_descriptors(thing_manager.get_descriptors_json())

    def shutdown(self):
        """关闭所有资源"""
        self.ws_client.disconnect()
        self.audio_handler.close()
        self.keyboard_listener.stop()

if __name__ == "__main__":
    # 配置参数（建议从配置文件读取）
    config = {
        'access_token': 'test-token',
        'device_mac': '04:68:74:27:12:c8',
        'device_uuid': 'test-uuid',
        'ws_url': 'wss://api.tenclass.net/xiaozhi/v1/',# 小智官方
        #'ws_url': 'ws://192.168.10.9:8000',           #自定义服务端https://github.com/vonweller/xiaozhi-esp32-server
        'ota_url': 'https://api.tenclass.net/xiaozhi/ota/',
        'manual_mode': False,
    }
    assistant = VoiceAssistant(config)
    try:
        assistant.start()
        assistant.keyboard_listener.join()  # 保持主线程运行
    except KeyboardInterrupt:
        assistant.shutdown()