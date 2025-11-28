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