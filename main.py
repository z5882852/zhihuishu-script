import sys

import terminal
import ui

if __name__ == "__main__":
    # 如果加上'-C'或'--cmd'参数，则进入命令行模式
    if len(sys.argv) > 1 and (sys.argv[1] == '-C' or sys.argv[1] == '--cmd'):
        speed = 1  # 默认速度为1
        while True:
            try:
                speed = int(input("请输入视频观看速度(1-20)："))
                if speed < 1 or speed > 10:
                    raise ValueError
                break
            except ValueError:
                print("输入错误，请重新输入")
        # 运行命令行模式
        terminal.run(speed=speed)
    else:
        ui.run()