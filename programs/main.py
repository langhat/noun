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
from commands import *
from show_notification import *

# 初始化对话历史
ai_system = ''
with open('system.txt', 'r', encoding='utf-8') as f:
    ai_system = f.read()
chated = [
    {'role': 'system', 'content': ai_system}
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
                        user_return = input(f"\nAI想将内容写入文件: \"{tool_msg['Path']}\"，模式为 \"{tool_msg.get('Mode', 'append')}\"，是否同意 (y/n): ")

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
                        user_return = input(f"\nAI想运行命令: \'{tool_msg['Command']}\' 是否同意 (y/n): ")

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