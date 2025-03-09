import os
import random
from flask import Flask, jsonify
import time
from collections import defaultdict

app = Flask(__name__)
MD_DIR = "app"
CACHE_TIME = 300  # 缓存5分钟（300秒）

# 使用内存缓存
class FileCache:
    def __init__(self):
        self.last_scan = 0
        self.user_index = defaultdict(list)
        self.all_files = []
        self.lock = False

    def refresh_cache(self):
        if time.time() - self.last_scan < CACHE_TIME and self.user_index:
            return
        
        self.user_index.clear()
        self.all_files = []
        
        try:
            for filename in os.listdir(MD_DIR):
                if filename.endswith(".md"):
                    filepath = os.path.join(MD_DIR, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            first_line = f.readline().strip()
                            if first_line.startswith("#name="):
                                username = first_line.split("=", 1)[1].strip()
                                self.user_index[username].append(filename)
                                self.all_files.append(filename)
                    except Exception as e:
                        print(f"Error reading {filename}: {str(e)}")
        except FileNotFoundError:
            os.makedirs(MD_DIR, exist_ok=True)
        
        self.last_scan = time.time()

file_cache = FileCache()

@app.route('/ss')
def random_files():
    file_cache.refresh_cache()
    try:
        # 默认返回5个随机文件，不足时返回全部
        sample_size = min(5, len(file_cache.all_files))
        result = random.sample(file_cache.all_files, sample_size)
        return jsonify({"status": "success", "files": result})
    except ValueError:
        return jsonify({"status": "error", "message": "No files available"})

@app.route('/name=<username>')
def user_files(username):
    file_cache.refresh_cache()
    start_time = time.time()
    
    # 直接从内存缓存获取结果
    files = file_cache.user_index.get(username, [])
    
    print(f"Query time: {time.time() - start_time:.4f} seconds")
    return jsonify({
        "status": "success",
        "count": len(files),
        "files": files
    })

if __name__ == '__main__':
    # 预热缓存
    file_cache.refresh_cache()
    app.run(host='0.0.0.0', port=5005, debug=False)