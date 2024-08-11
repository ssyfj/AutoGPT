import json

# https://q0tozme54s7.feishu.cn/wiki/YkGpwAlo2iD0h3kZ0TgczWJNnqb#FyXGdCg72oy2I3xDPqjc2WE5nNe
def ChinsesFriendly(string):
    """
        langchain的outputparser返回的描述是压缩后的，并且中文被转成了ascii码的一段文本，这里进行换行，解析json格式，还原中文，格式易读
    """
    lines = string.split("\n")
    for i,line in enumerate(lines):
        if line.startswith("{") and line.endswith("}"):
            try:
                lines[i] = json.dumps(json.loads(line),ensure_ascii=False)
            except:
                pass
    return '\n'.join(lines)