import os
import re
import fnmatch
from flask import Flask, request, jsonify
from collections import defaultdict, Counter
import threading

app = Flask(__name__)
app_folder = "app"
search_counter = Counter()
index_lock = threading.Lock()

# 内存索引结构
file_index = []              # [{id, path, filename, content}]
inverted_index = defaultdict(set)  # {term: set(file_ids)}
filename_index = defaultdict(set)  # {term: set(file_ids)}

def markdown_to_text(content):
    """高效去除Markdown标记"""
    content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)  # 去除注释
    content = re.sub(r'```.*?```', '', content, flags=re.DOTALL)  # 去除代码块
    content = re.sub(r'[#*\-_=`~]+', ' ', content)                # 去除特殊符号
    return content.strip()

def build_index():
    """构建内存倒排索引"""
    global file_index
    temp_index = []
    temp_inverted = defaultdict(set)
    temp_filename = defaultdict(set)
    
    for root, _, files in os.walk(app_folder):
        for idx, filename in enumerate(files):
            if not filename.endswith('.md'):
                continue
            
            path = os.path.join(root, filename)
            with open(path, 'r', encoding='utf-8') as f:
                content = markdown_to_text(f.read())
                
            # 索引元数据
            file_entry = {
                'id': idx,
                'path': path,
                'filename': filename,
                'content': content
            }
            temp_index.append(file_entry)
            
            # 文件名索引
            for part in filename.lower().split():
                temp_filename[part].add(idx)
            
            # 内容索引（按词）
            for word in re.findall(r'\b\w+[\w\-]*\b', content.lower()):
                temp_inverted[word].add(idx)
    
    with index_lock:
        file_index = temp_index
        inverted_index.clear()
        inverted_index.update(temp_inverted)
        filename_index.clear()
        filename_index.update(temp_filename)

def wildcard_to_regex(pattern):
    """通配符转正则表达式"""
    return re.compile(fnmatch.translate(pattern), re.IGNORECASE)

def search_files(pattern):
    """执行通配符搜索"""
    # 优化：优先检查文件名
    matched_files = set()
    regex = wildcard_to_regex(pattern)
    
    # 文件名匹配
    for term in filename_index:
        if regex.match(term):
            matched_files.update(filename_index[term])
    
    # 内容匹配（如果结果不足）
    if len(matched_files) < 50:
        for term in inverted_index:
            if regex.match(term):
                matched_files.update(inverted_index[term])
    
    return matched_files

@app.route('/ss')
def search():
    query = request.args.get('name', '').lower().strip()
    if not query:
        return jsonify({"error": "Missing query"}), 400
    
    # 记录搜索热词
    search_counter[query] += 1
    
    # 执行搜索
    matched_ids = search_files(query)
    results = []
    
    for fid in matched_ids:
        entry = file_index[fid]
        results.append({
            "path": entry['path'],
            "filename": entry['filename'],
            "excerpt": entry['content'][:100]  # 简单摘要
        })
    
    return jsonify({"results": results[:50]})  # 限制返回数量

@app.route('/phb')
def hot_phrases():
    return jsonify([
        {"word": k, "count": v} 
        for k, v in search_counter.most_common(50)
    ])

if __name__ == '__main__':
    build_index()  # 启动时构建索引
    app.run(port=5002, threaded=True)