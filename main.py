import sys

import terminal
import ui

if __name__ == "__main__":
    # 如果加上'-C'或'--cmd'参数，则进入命令行模式
    if len(sys.argv) > 1 and (sys.argv[1] == '-C' or sys.argv[1] == '--cmd'):
        terminal.run()
    else:
        ui.run()