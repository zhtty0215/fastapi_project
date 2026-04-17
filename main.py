from fastapi import FastAPI
import pymysql
import requests
import os

pwd = os.getenv("DB_PASSWORD")
key=os.getenv("DEEPSEEK_API_KEY")
# 实例名称
app = FastAPI()

# 设置根路径
@app.get("/")
async def root():
    return {"msg": "hello"}

# 发送注册请求
@app.post("/register")
def register(username: str, password: str):
    conn = get_connect()
    cursor = conn.cursor()
    sql = "insert into user_list(username,password) values(%s,%s)"
    cursor.execute(sql, (username, password))
    conn.commit()
    cursor.close()
    conn.close()
    return {"msg": "注册成功"}

# 登录
@app.post("/login")
def login(username: str, password: str):
    conn = get_connect()
    cursor = conn.cursor()
    sql = "select * from user_list where username=%s and password=%s"
    cursor.execute(sql, (username, password))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    if result:
        return {"msg": "登陆成功"}
    else:
        return {"msg": "用户名或密码错误"}

# 调用 DeepSeek AI
def call_ai(messages):
    url = "https://api.deepseek.com/chat/completions"
    headers = {
        "Authorization": f"Bearer{key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "deepseek-chat",
        "messages": messages
    }
    response = requests.post(url, headers=headers, json=data)
    result = response.json()
    return result["choices"][0]["message"]["content"]

# 获取历史记录
def get_history(user_id):
    sql = """
    select question,answer
    from chat_record
    where user_id=%s
    order by id
    limit 5
    """
    conn = get_connect()
    cursor = conn.cursor()
    cursor.execute(sql, (user_id,))
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data

# 构建消息（这里有明显bug）
def build_messages(history, question):
    messages = []
    for q, a in history:
        messages.append({"role": "user", "content": q})
        messages.append({"role": "assistant", "content": a})
    messages.append({"role": "user", "content": question})   # ← 这里写错了
    return messages

# 聊天接口
@app.post("/chat")
def chat(user_id: int, question: str):
    answer = chat_service(user_id, question)
    return {"answer": answer}

# 数据库连接
def get_connect():
    return pymysql.connect(
        host="localhost",
        user="testuser",
        password=pwd.strip(),
        database="test"
    )

# 聊天服务
def chat_service(user_id, question):
    history = get_history(user_id)
    final_question = build_messages(history, question)
    answer = call_ai(final_question)
    save_chat(user_id, question, answer)
    return answer

# 保存聊天记录
def save_chat(user_id, question, answer):
    conn = get_connect()
    cursor = conn.cursor()
    sql = "insert into chat_record(user_id,question,answer) values(%s,%s,%s)"
    cursor.execute(sql, (user_id, question, answer))
    conn.commit()
    cursor.close()
    conn.close()


