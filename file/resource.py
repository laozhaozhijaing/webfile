from flask import Flask, request, jsonify
import json
import os
import requests
from datetime import datetime
import threading

app = Flask(__name__)
DATA_FILE = 'resources.json'
lock = threading.Lock()

class ResourceManager:
    @staticmethod
    def load_data():
        try:
            with lock:
                if not os.path.exists(DATA_FILE):
                    return []
                with open(DATA_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading data: {str(e)}")
            return []

    @staticmethod
    def save_data(data):
        try:
            with lock:
                with open(DATA_FILE, 'w') as f:
                    json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving data: {str(e)}")

@app.route('/new', methods=['GET'])
def new_resource():
    # Token验证
    token = request.args.get('token')
    if not token:
        return jsonify({"status": "error", "message": "缺少token参数"})
    
    resp = requests.get(f'http://127.0.0.1:5000/yz?token={token}')
    if resp.status_code != 200 or resp.json().get('status') != 'success':
        return jsonify({"status": "error", "message": "无效token"})
    
    user_info = resp.json()
    username = user_info['name']

    # 获取参数
    title = request.args.get('biaoti')
    if not title:
        return jsonify({"status": "error", "message": "缺少标题参数"})

    # 收集资源地址
    resources = []
    for key in sorted(request.args.keys()):
        if key.startswith('ziyuan'):
            resources.append(request.args.get(key))
    
    if not resources:
        return jsonify({"status": "error", "message": "至少需要一个资源地址"})

    introduction = request.args.get('jieshao', '')

    # 创建新记录
    new_entry = {
        "user": username,
        "title": title,
        "resources": resources,
        "introduction": introduction,
        "timestamp": datetime.now().isoformat()
    }

    data = ResourceManager.load_data()
    data.append(new_entry)
    ResourceManager.save_data(data)

    return jsonify({"status": "success"})

@app.route('/chakan', methods=['GET'])
def view_resource():
    title = request.args.get('biaoti')
    if not title:
        return jsonify({"status": "error", "message": "缺少标题参数"})
    
    data = ResourceManager.load_data()
    results = [item for item in data if item['title'] == title]
    
    if not results:
        return jsonify({"status": "error", "message": "未找到相关资源"})
    
    return jsonify({"status": "success", "data": results})

@app.route('/yongh', methods=['GET'])
def user_resources():
    username = request.args.get('name')
    if not username:
        return jsonify({"status": "error", "message": "缺少用户名参数"})
    
    data = ResourceManager.load_data()
    results = [item for item in data if item['user'] == username]
    
    return jsonify({"status": "success", "data": results})

@app.route('/ss', methods=['GET'])
def search_resources():
    keyword = request.args.get('name')
    if not keyword:
        return jsonify({"status": "error", "message": "缺少搜索关键词"})
    
    data = ResourceManager.load_data()
    found_titles = set()
    
    for item in data:
        if (keyword.lower() in item['title'].lower() or 
            keyword.lower() in item['introduction'].lower()):
            found_titles.add(item['title'])
    
    return jsonify({"status": "success", "data": list(found_titles)})

if __name__ == '__main__':
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w') as f:
            f.write('[]')
    app.run(debug=True,port=5004)