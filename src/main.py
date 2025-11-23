import glob
import os
import re
import json
import subprocess
from openai import OpenAI
from resources import *
import ctypes
import time
import ctypes
import time

# 初始化对话历史
chated = [
    {'role': 'system', 'content': '''
- 你是一个AI智能体，你可以使用工具来操作电脑，一次只能调用一个工具(注意!!!只能调用一个工具!!!)
- 使用工具时要用<AgentToolsCall></AgentToolsCall>包裹
工具介绍:
# 列出目录：
## 调用方式
{
    "name":"ListDir",
    "Path":"<要查看的目录>",
}
# 读取文件：
## 调用方式
{
    "name":"ReadFile",
    "Path":"<要读取的文件路径>",
}
# 写入文件（使用diff方式）：
## 调用方式
{
    "name":"WriteFileDiff",
    "Path":"<要写入的文件路径>",
    "Content":"<要写入的内容>",
    "Mode":"append" 或 "replace"
}
# 文件搜索：
## 调用方式
{
    "name":"SearchFile",
    "Path":"<要搜索的目录>",
    "Pattern":"<搜索模式>",
}
# 文件内容搜索：
## 调用方式
{
    "name":"SearchContent",
    "Path":"<要搜索的文件路径>",
    "Pattern":"<搜索模式>",
}
# 运行 cmd 命令：
## 调用方式
{
    "name":"RunCmd",
    "Command":"<要执行的命令>",
}
# 完成任务
## 调用方式
{
    "name":"TaskDone",
    "msg":"<完成任务后的总结>"
}
注:
- 调用工具时，必须包裹在<AgentToolsCall></AgentToolsCall>中
- 一次只能调用一个工具
- 调用完成后，必须等待工具执行完成，才能继续调用下一个工具
- 一次只能调用一个工具
- 调用完成后，必须等待工具执行完成，才能继续调用下一个工具
- 一次只能调用一个工具
- 调用完成后，必须等待工具执行完成，才能继续调用下一个工具
- 调用TaskDone后，任务完成，对话结束
- 任务完成后，必须使用TaskDone工具结束任务，否则对话将继续进行
- 任务完成后，必须使用TaskDone工具提交任务报告，否则任务将被视为未完成
- 任务完成后，必须使用TaskDone工具结束任务，否则对话将继续进行
- 任务完成后，必须使用TaskDone工具提交任务报告，否则任务将被视为未完成
- 任务完成后，必须使用TaskDone工具结束任务，否则对话将继续进行
- 任务完成后，必须使用TaskDone工具提交任务报告，否则任务将被视为未完成
'''}
]

def GetAgentCall(text):
    # 使用正则表达式匹配 <AgentToolsCall> 和 </AgentToolsCall> 之间的内容
    pattern = r'<AgentToolsCall>(.*?)</AgentToolsCall>'
    match = re.search(pattern, text, re.DOTALL)

    if match:
        content = match.group(1).strip()
        return 1, content
    else:
        return 0, None

def ReadFile(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        return {"status": "success", "content": content}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def WriteFileDiff(path, content, mode="append"):
    try:
        if mode == "append":
            with open(path, 'r', encoding='utf-8') as f:
                existing_content = f.read()
            new_content = existing_content + "\n" + content
        elif mode == "replace":
            new_content = content
        else:
            return {"status": "error", "message": "无效的模式: 必须是 'append' 或 'replace'"}

        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return {"status": "success", "message": "文件已成功写入"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def SearchFile(path, pattern):
    try:
        files = glob.glob(os.path.join(path, pattern))
        return {"status": "success", "files": files}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def SearchContent(path, pattern):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        matches = re.findall(pattern, content)
        return {"status": "success", "matches": matches}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def RunCmd(command):
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=True
        )
        return {
            "status": "success",
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except subprocess.CalledProcessError as e:
        return {
            "status": "error",
            "stdout": e.stdout,
            "stderr": e.stderr
        }

def get_response(chated):
    client = OpenAI(
        api_key=api_key,
        base_url=api_url,
    )

    completion = client.chat.completions.create(
        model=modelID,
        messages=chated,
        stream=True,
        stream_options={"include_usage": True}
    )

    RUS = ""

    for chunk in completion:
        if hasattr(chunk, "choices") and len(chunk.choices) > 0:
            choice = chunk.choices[0]
            if hasattr(choice, "delta") and hasattr(choice.delta, "content"):
                RUS += choice.delta.content
                print(choice.delta.content, end='', flush=True)
    
    return RUS

def color_print(text, color_code):
    """打印带颜色的文本"""
    print(f"\033[{color_code}m{text}\033[0m")

def show_notification(title, message):
    """在Windows右下角显示弹出通知"""
    # 简化的NOTIFYICONDATA结构体
    class NOTIFYICONDATA(ctypes.Structure):
        _fields_ = [
            ('cbSize', ctypes.c_uint),
            ('hWnd', ctypes.c_void_p),
            ('uID', ctypes.c_uint),
            ('uFlags', ctypes.c_uint),
            ('uCallbackMessage', ctypes.c_uint),
            ('hIcon', ctypes.c_void_p),
            ('szTip', ctypes.c_wchar * 128),
            ('dwState', ctypes.c_uint),
            ('dwStateMask', ctypes.c_uint),
            ('szInfo', ctypes.c_wchar * 256),
            ('uTimeoutOrVersion', ctypes.c_uint),
            ('szInfoTitle', ctypes.c_wchar * 64),
            ('dwInfoFlags', ctypes.c_uint)
        ]
    
    # 定义常量
    NIM_ADD = 0x00000000
    NIF_INFO = 0x00000010
    NIF_ICON = 0x00000002
    NIF_TIP = 0x00000001
    
    # 创建结构体实例
    nid = NOTIFYICONDATA()
    nid.cbSize = ctypes.sizeof(nid)
    nid.hWnd = 0
    nid.uID = 100  # 使用固定ID便于识别
    nid.uFlags = NIF_ICON | NIF_TIP | NIF_INFO
    
    # 使用默认应用程序图标
    try:
        nid.hIcon = ctypes.windll.user32.LoadIconW(0, 32512)  # IDI_APPLICATION图标
    except Exception:
        nid.hIcon = 0  # 如果无法加载图标，设为0
    
    # 设置通知内容
    nid.szTip = "AI 助手通知"  # 托盘图标悬停提示
    nid.szInfoTitle = title  # 通知标题
    nid.szInfo = message    # 通知内容
    nid.uTimeoutOrVersion = 5000  # 通知显示时间（毫秒）
    
    # 显示通知（不立即删除，让它自然消失）
    ctypes.windll.shell32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(nid))

if __name__ == '__main__':
    show_notification("AI 助手", "欢迎使用AI助手")
    while True:
        user_input = input("Agent ??>@ ")
        if user_input == "exit":
            break
        chated.append({'role': 'user', 'content': user_input})
        while True:
            chatedmsg = get_response(chated=chated)
            
            retID, tool_msg = GetAgentCall(chatedmsg)
            rus_to_agent = ""
            
            if retID == 1:
                try:
                    tool_msg = json.loads(tool_msg)
                    if tool_msg["name"] == "ListDir":
                        # 在需要用户确认的操作前显示通知
                        show_notification("需要您的确认", f"AI想要列出 {tool_msg['Path']} 目录下的文件")
                        user_return = input(f"\nAI想列出 {tool_msg['Path']} 目录下的文件是否同意 (y/n): ")

                        if user_return == "y":
                            try:
                                rus1 = os.listdir(tool_msg["Path"])
                                rus2 = {
                                    "path": tool_msg["Path"],
                                    "files": []
                                }
                                for file in rus1:
                                    full_path = os.path.join(tool_msg["Path"], file)
                                    if os.path.isfile(full_path):
                                        rus2["files"].append({"name": file, "type": "file"})
                                    elif os.path.isdir(full_path):
                                        rus2["files"].append({"name": file, "type": "folder"})
                                    else:
                                        rus2["files"].append({"name": file, "type": "无法判断"})
                                rus_to_agent = json.dumps(rus2, ensure_ascii=False, indent=4)
                            except Exception as e:
                                rus_to_agent = f"访问目录失败: {str(e)}"
                        else:
                            ret = input("\n你拒绝了AI的请求，请给出建议：")
                            rus_to_agent = f"用户拒绝了你的请求并给出了以下建议: {ret}"
                    
                    elif tool_msg["name"] == "ReadFile":
                        result = ReadFile(tool_msg["Path"])
                        rus_to_agent = json.dumps(result, ensure_ascii=False, indent=4)
                    
                    elif tool_msg["name"] == "WriteFileDiff":
                        # 在需要用户确认的操作前显示通知
                        show_notification("需要您的确认", f"AI想要将内容写入文件: '{tool_msg['Path']}'，模式为 '{tool_msg.get('Mode', 'append')}'")
                        user_return = input(f"\nAI想将内容写入文件: '{tool_msg["Path"]}'，模式为 '{tool_msg.get("Mode", "append")}'，是否同意 (y/n): ")

                        if user_return == "y":
                            result = WriteFileDiff(tool_msg["Path"], tool_msg["Content"], tool_msg.get("Mode", "append"))
                            rus_to_agent = json.dumps(result, ensure_ascii=False, indent=4)
                        else:
                            ret = input("\n你拒绝了AI的请求，请给出建议：")
                            rus_to_agent = f"用户拒绝了你的请求并给出了以下建议: {ret}"
                    
                    elif tool_msg["name"] == "SearchFile":
                        result = SearchFile(tool_msg["Path"], tool_msg["Pattern"])
                        rus_to_agent = json.dumps(result, ensure_ascii=False, indent=4)
                    
                    elif tool_msg["name"] == "SearchContent":
                        result = SearchContent(tool_msg["Path"], tool_msg["Pattern"])
                        rus_to_agent = json.dumps(result, ensure_ascii=False, indent=4)
                    
                    elif tool_msg["name"] == "RunCmd":
                        # 在需要用户确认的操作前显示通知
                        show_notification("需要您的确认", f"AI想要运行命令: '{tool_msg['Command']}'")
                        user_return = input(f"\nAI想运行命令: '{tool_msg["Command"]}' 是否同意 (y/n): ")

                        if user_return == "y":
                            result = RunCmd(tool_msg["Command"])
                            if result["status"] == "success":
                                color_print("✅ 命令执行成功:", "32")
                                color_print("STDOUT:\n" + result["stdout"], "32")
                                color_print("STDERR:\n" + result["stderr"], "31")
                            else:
                                color_print("❌ 命令执行失败:", "31")
                                color_print("STDOUT:\n" + result["stdout"], "31")
                                color_print("STDERR:\n" + result["stderr"], "31")
                            rus_to_agent = json.dumps(result, ensure_ascii=False, indent=4)
                        else:
                            ret = input("\n你拒绝了AI的请求，请给出建议：")
                            rus_to_agent = f"用户拒绝了你的请求并给出了以下建议: {ret}"
                    
                    elif tool_msg["name"] == "TaskDone":
                        print(f"\nAI 完成了任务, 给出以下总结:\n{tool_msg['msg']}")
                        break
                
                except Exception as e:
                    rus_to_agent = f"解析工具调用失败: {str(e)}"
            else:
                print("AI未调用任何工具", flush=True)
            
            chated.append({"role": "assistant", "content": chatedmsg})
            chated.append({"role": "user", "content": f"你调用了工具，工具返回：{rus_to_agent}"})
#copy from https://gitee.com/colid/ai