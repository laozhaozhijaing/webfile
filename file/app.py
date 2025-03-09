from flask import Flask, request, jsonify
import smtplib
import hashlib
import secrets
import json
import time
import random
from email.mime.text import MIMEText
from threading import Lock

app = Flask(__name__)

# 文件路径配置
USER_FILE = 'user.json'
TOKEN_FILE = 'token.json'

# 线程锁用于文件操作
user_lock = Lock()
token_lock = Lock()

# 临时存储验证码 {name: {code: str, timestamp: float, mail: str, passwd: str}}
verification_codes = {}

# SMTP配置（需替换为实际值）
SMTP_SENDER = 'zty192168@163.com'
SMTP_PASSWORD = 'ETgmS7w3Wtt3D6ri'  # SMTP授权码
SMTP_SERVER = 'smtp.163.com'
SMTP_PORT = 465

def load_users():
    try:
        with open(USER_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_users(users):
    with user_lock:
        with open(USER_FILE, 'w') as f:
            json.dump(users, f, indent=4)

def load_tokens():
    try:
        with open(TOKEN_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_tokens(tokens):
    with token_lock:
        with open(TOKEN_FILE, 'w') as f:
            json.dump(tokens, f, indent=4)

def hash_password(password):
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return salt, key.hex()

def verify_password(salt, hashed, password):
    test_key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return test_key.hex() == hashed

def send_email(receiver, code):
    msg = MIMEText(f'您的验证码是：{code}，有效期5分钟。')
    msg['Subject'] = '验证码'
    msg['From'] = SMTP_SENDER
    msg['To'] = receiver

    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SMTP_SENDER, SMTP_PASSWORD)
            server.sendmail(SMTP_SENDER, receiver, msg.as_string())
            return True
    except Exception as e:
        print(f"邮件发送失败：{e}")
        return False

@app.route('/newuser', methods=['GET'])
def register_step1():
    name = request.args.get('name')
    mail = request.args.get('mail')
    passwd = request.args.get('passwd')

    if not all([name, mail, passwd]):
        return jsonify({'status': 'error', 'message': '参数不全'}), 400

    users = load_users()
    if any(u['name'] == name for u in users):
        return jsonify({'status': 'error', 'message': '用户名已存在'}), 400
    if any(u['email'] == mail for u in users):
        return jsonify({'status': 'error', 'message': '邮箱已存在'}), 400

    code = ''.join(random.choices('0123456789', k=6))
    if not send_email(mail, code):
        return jsonify({'status': 'error', 'message': '邮件发送失败'}), 500

    verification_codes[name] = {
        'code': code,
        'timestamp': time.time(),
        'mail': mail,
        'passwd': passwd
    }

    return jsonify({'status': 'success', 'message': '验证码已发送'}), 200

@app.route('/newuser2', methods=['GET'])
def register_step2():
    name = request.args.get('name')
    yzm = request.args.get('yzm')

    if not all([name, yzm]):
        return jsonify({'status': 'error', 'message': '参数不全'}), 400

    data = verification_codes.get(name)
    if not data:
        return jsonify({'status': 'error', 'message': '验证码错误或已过期'}), 400

    if time.time() - data['timestamp'] > 300:
        del verification_codes[name]
        return jsonify({'status': 'error', 'message': '验证码已过期'}), 400

    if yzm != data['code']:
        return jsonify({'status': 'error', 'message': '验证码错误'}), 400

    salt, hashed = hash_password(data['passwd'])
    new_user = {
        'name': name,
        'passwd': hashed,
        'passwdyz': salt,
        'email': data['mail']
    }

    users = load_users()
    users.append(new_user)
    save_users(users)
    del verification_codes[name]

    return jsonify({'status': 'success', 'message': '注册成功'}), 200

@app.route('/newpasswd', methods=['GET'])
def reset_pw_step1():
    name = request.args.get('name')
    mail = request.args.get('mail')

    if not all([name, mail]):
        return jsonify({'status': 'error', 'message': '参数不全'}), 400

    users = load_users()
    user = next((u for u in users if u['name'] == name), None)
    if not user or user['email'] != mail:
        return jsonify({'status': 'error', 'message': '验证失败'}), 400

    code = ''.join(random.choices('0123456789', k=6))
    if not send_email(mail, code):
        return jsonify({'status': 'error', 'message': '邮件发送失败'}), 500

    verification_codes[name] = {
        'code': code,
        'timestamp': time.time(),
        'mail': mail
    }

    return jsonify({'status': 'success', 'message': '验证码已发送'}), 200

@app.route('/newpasswd2', methods=['GET'])
def reset_pw_step2():
    name = request.args.get('name')
    yzm = request.args.get('yzm')
    new_passwd = request.args.get('passwd')

    if not all([name, yzm, new_passwd]):
        return jsonify({'status': 'error', 'message': '参数不全'}), 400

    data = verification_codes.get(name)
    if not data:
        return jsonify({'status': 'error', 'message': '验证码错误或已过期'}), 400

    if time.time() - data['timestamp'] > 300:
        del verification_codes[name]
        return jsonify({'status': 'error', 'message': '验证码已过期'}), 400

    if yzm != data['code']:
        return jsonify({'status': 'error', 'message': '验证码错误'}), 400

    users = load_users()
    user = next((u for u in users if u['name'] == name), None)
    if not user:
        return jsonify({'status': 'error', 'message': '用户不存在'}), 400

    salt, hashed = hash_password(new_passwd)
    user['passwd'] = hashed
    user['passwdyz'] = salt
    save_users(users)
    del verification_codes[name]

    tokens = load_tokens()
    tokens = {k: v for k, v in tokens.items() if v['name'] != name}
    save_tokens(tokens)

    return jsonify({'status': 'success', 'message': '密码已重置'}), 200

@app.route('/login', methods=['GET'])
def login():
    name = request.args.get('name')
    passwd = request.args.get('passwd')

    if not all([name, passwd]):
        return jsonify({'status': 'error', 'message': '参数不全'}), 400

    users = load_users()
    user = next((u for u in users if u['name'] == name), None)
    if not user or not verify_password(user['passwdyz'], user['passwd'], passwd):
        return jsonify({'status': 'error', 'message': '验证失败'}), 401

    token = secrets.token_urlsafe(32)
    tokens = load_tokens()
    tokens = {k: v for k, v in tokens.items() if v['name'] != name}
    tokens[token] = {'name': name, 'time': time.time()}
    save_tokens(tokens)

    return jsonify({'status': 'success', 'token': token}), 200

@app.route('/yz', methods=['GET'])
def verify_token():
    token = request.args.get('token')
    if not token:
        return jsonify({'status': 'error', 'message': '参数不全'}), 400

    tokens = load_tokens()
    info = tokens.get(token)
    if not info or time.time() - info['time'] > 604800:  # 7天有效期
        return jsonify({'status': 'error', 'message': '无效token'}), 401

    users = load_users()
    user = next((u for u in users if u['name'] == info['name']), None)
    if not user:
        return jsonify({'status': 'error', 'message': '用户不存在'}), 404

    return jsonify({'status': 'success', 'name': user['name'], 'email': user['email']}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)