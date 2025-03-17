from xiaozhiM10.src.iot.thing import Thing


class Lamp(Thing):
    def __init__(self):
        super().__init__("Lamp", "一个测试用的灯")
        self.power = False

        print(f"[虚拟设备] 灯设备初始化完成")

        # 定义属性
        self.add_property("power", "灯是否打开", lambda: self.power)

        # 定义方法
        self.add_method("TurnOn", "开灯", [],
                        lambda params: self.TurnOn())

        self.add_method("TurnOff", "关灯", [],
                        lambda params: self.TurnOff())

    def TurnOn(self):
        self.power = True
        print(f"[虚拟设备] 灯已打开")
        return {"status": "success", "message": "灯已打开"}

    def TurnOff(self):
        self.power = False
        print(f"[虚拟设备] 灯已关闭")
        return {"status": "success", "message": "灯已关闭"}