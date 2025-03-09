from flask import Flask, request, jsonify
import os
import json
import requests
import time
import re

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

ARTICLES_FILE = "articles.json"
COMMENTS_DIR = "comments"
APP_DIR = "app"

os.makedirs(APP_DIR, exist_ok=True)
os.makedirs(COMMENTS_DIR, exist_ok=True)

# 辅助函数 ==============================================================

def sanitize_filename(name):
    """生成安全的文件名"""
    safe_name = re.sub(r'[^\w\-_]', '', name)[:50]
    return f"{safe_name}_comments.json"

def load_comments(article_name):
    """加载指定文章的评论数据"""
    filename = sanitize_filename(article_name)
    path = os.path.join(COMMENTS_DIR, filename)
    
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "likes": 0,
        "comments": [],
        "next_id": 1
    }

def save_comments(article_name, data):
    """保存指定文章的评论数据"""
    filename = sanitize_filename(article_name)
    path = os.path.join(COMMENTS_DIR, filename)
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_articles():
    """加载文章数据"""
    if os.path.exists(ARTICLES_FILE):
        with open(ARTICLES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_articles(data):
    """保存文章数据"""
    with open(ARTICLES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def verify_token(token):
    """验证token有效性"""
    try:
        response = requests.get(f"http://127.0.0.1:5000/yz?token={token}")
        if response.json().get("status") == "success":
            return response.json()
        return None
    except:
        return None

# 路由处理 ==============================================================

@app.route("/wz", methods=["GET"])
def create_article():
    """创建文章"""
    token = request.args.get("token")
    name = request.args.get("nam")
    content = request.args.get("newwz")
    
    user = verify_token(token)
    if not user:
        return jsonify({"status": "error", "message": "无效token"}), 401
    
    safe_name = "".join([c for c in name if c.isalnum() or c in (" ", "-", "_")])[:50]
    filename = f"{safe_name}.md"
    
    articles = load_articles()
    if safe_name in articles:
        return jsonify({"status": "error", "message": "文章已存在"}), 400
    
    try:
        with open(os.path.join(APP_DIR, filename), "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
    articles[safe_name] = {
        "user": user["name"],
        "path": filename,
        "create_time": time.time()
    }
    save_articles(articles)
    return jsonify({"status": "success", "message": "文章创建成功"})

@app.route("/wzdq", methods=["GET"])
def get_article():
    """获取文章内容"""
    name = request.args.get("nam")
    articles = load_articles()
    
    if not name or name not in articles:
        return jsonify({"status": "error", "message": "文章不存在"}), 404
    
    try:
        file_path = os.path.join(APP_DIR, articles[name]["path"])
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        return jsonify({
            "status": "success",
            "article_name": name,
            "author": articles[name]["user"],
            "content": content,
            "create_time": articles[name]["create_time"]
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"读取失败: {str(e)}"
        }), 500

@app.route("/rm", methods=["GET"])
def remove_article():
    """删除文章"""
    token = request.args.get("token")
    name = request.args.get("nam")
    
    user = verify_token(token)
    if not user:
        return jsonify({"status": "error", "message": "无效token"}), 401
    
    articles = load_articles()
    if name not in articles or articles[name]["user"] != user["name"]:
        return jsonify({"status": "error", "message": "无权操作"}), 403
    
    try:
        # 删除文章文件
        os.remove(os.path.join(APP_DIR, articles[name]["path"]))
        # 删除评论文件
        comment_file = os.path.join(COMMENTS_DIR, sanitize_filename(name))
        if os.path.exists(comment_file):
            os.remove(comment_file)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
    del articles[name]
    save_articles(articles)
    return jsonify({"status": "success", "message": "文章删除成功"})

@app.route("/pl", methods=["GET"])
def handle_comment():
    """评论处理中心"""
    token = request.args.get("token")
    name = request.args.get("nam")
    data = request.args.get("data")
    zd = request.args.get("zd")
    sc = request.args.get("sc")
    dz = request.args.get("dz")
    reply_to = request.args.get("reply_to")

    # 处理点赞
    if dz:
        comments = load_comments(name)
        articles = load_articles()
        
        if name not in articles:
            return jsonify({"status": "error", "message": "文章不存在"}), 404
        
        if dz == "wz":
            comments["likes"] += 1
        else:
            try:
                target_id = int(dz)
                found = False
                for comment in comments["comments"]:
                    if comment["id"] == target_id:
                        comment["likes"] += 1
                        found = True
                        break
                    for reply in comment.get("replies", []):
                        if reply["id"] == target_id:
                            reply["likes"] += 1
                            found = True
                            break
                if not found:
                    return jsonify({"status": "error", "message": "目标不存在"}), 404
            except:
                return jsonify({"status": "error", "message": "参数错误"}), 400
        
        save_comments(name, comments)
        return jsonify({"status": "success", "message": "点赞成功"})
    
    # 需要token的操作
    user = verify_token(token)
    if not user:
        return jsonify({"status": "error", "message": "无效token"}), 401
    
    comments = load_comments(name)
    articles = load_articles()
    
    if name not in articles:
        return jsonify({"status": "error", "message": "文章不存在"}), 404
    
    # 添加评论或回复
    if data:
        if reply_to:
            try:
                parent_id = int(reply_to)
                parent_comment = None
                for comment in comments["comments"]:
                    if comment["id"] == parent_id:
                        parent_comment = comment
                        break
                
                if not parent_comment:
                    return jsonify({"status": "error", "message": "父评论不存在"}), 404

                if "next_reply_id" not in parent_comment:
                    parent_comment["next_reply_id"] = 1

                new_reply = {
                    "id": parent_comment["next_reply_id"],
                    "user": user["name"],
                    "content": data,
                    "likes": 0,
                    "create_time": time.time()
                }
                parent_comment.setdefault("replies", []).append(new_reply)
                parent_comment["next_reply_id"] += 1
                
                save_comments(name, comments)
                return jsonify({"status": "success", "message": "回复添加成功"})
            except:
                return jsonify({"status": "error", "message": "参数错误"}), 400
        else:
            new_comment = {
                "id": comments["next_id"],
                "user": user["name"],
                "content": data,
                "likes": 0,
                "replies": [],
                "next_reply_id": 1,
                "create_time": time.time()
            }
            comments["comments"].append(new_comment)
            comments["next_id"] += 1
            save_comments(name, comments)
            return jsonify({"status": "success", "message": "评论添加成功"})
    
    # 管理评论
    if zd or sc:
        if articles[name]["user"] != user["name"]:
            return jsonify({"status": "error", "message": "无权操作"}), 403
        
        try:
            target_id = int(zd or sc)
        except:
            return jsonify({"status": "error", "message": "参数错误"}), 400
        
        if zd:
            for i, comment in enumerate(comments["comments"]):
                if comment["id"] == target_id:
                    comments["comments"].insert(0, comments["comments"].pop(i))
                    save_comments(name, comments)
                    return jsonify({"status": "success", "message": "评论置顶成功"})
            return jsonify({"status": "error", "message": "评论不存在"}), 404
        
        if sc:
            new_comments = []
            for comment in comments["comments"]:
                if comment["id"] != target_id:
                    new_comments.append(comment)
            comments["comments"] = new_comments
            save_comments(name, comments)
            return jsonify({"status": "success", "message": "评论删除成功"})
    
    return jsonify({"status": "error", "message": "参数错误"}), 400

@app.route("/plfh", methods=["GET"])
def get_comments():
    """获取评论列表"""
    name = request.args.get("nam")
    comments = load_comments(name)
    articles = load_articles()
    
    if name not in articles:
        return jsonify({"status": "error", "message": "文章不存在"}), 404
    
    return jsonify({
        "status": "success",
        "likes": comments["likes"],
        "comments": comments["comments"]
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)