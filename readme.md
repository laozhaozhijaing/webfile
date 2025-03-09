这是一个python博客系统
核心模块详解 
 
1. 资源管理服务（文档1）
```python 
@app.route('/new', methods=['GET'])
def new_resource():
    # 实现流程：
    # 1. Token验证 → 2. 参数校验 → 3. 资源组装 → 4. 数据持久化 
    # 数据存储结构：
    {
        "user": "用户名",
        "title": "资源标题",
        "resources": ["资源URL列表"],
        "introduction": "简介",
        "timestamp": "ISO时间戳"
    }
```
- 多资源参数自动收集（支持ziyuan1, ziyuan2...格式）
- 线程安全文件操作（通过threading.Lock保证）
- 用户行为审计（记录操作时间戳）
 
2. 文章评论系统（文档3）
```python 
评论数据结构示例 
{
    "likes": 123,      # 文章总点赞 
    "comments": [
        {
            "id": 1,
            "user": "用户A",
            "content": "主评论",
            "likes": 10,
            "replies": [  # 二级回复 
                {
                    "id": 1,
                    "user": "用户B",
                    "content": "回复内容",
                    "likes": 2 
                }
            ]
        }
    ]
}
```
- 点赞操作：通过dz参数区分文章/评论点赞（dz=wz表示文章点赞）
- 评论管理：作者可置顶(zd)/删除(sc)评论 
- 安全机制：文件名消毒处理（sanitize_filename）
 
3. 搜索服务（文档4）
```python 
def build_index():
    # 索引构建流程：
    # 遍历文件 → 提取文本 → 创建倒排索引 → 内存缓存 
    # 搜索优化策略：
    # 1. 优先文件名匹配 2. 内容词项匹配 3. 结果截断(最多50条)
```
- 倒排索引结构提升检索速度 
- 通配符转正则表达式（支持*等搜索语法）
- 独立索引锁机制（index_lock）保证线程安全 
 
4. 文件缓存服务（文档2）
```python 
class FileCache:
    def refresh_cache(self):
        # 缓存更新策略：
        # 1. 每5分钟强制刷新 2. 首次访问预加载 3. 异常文件跳过 
```
```
app/
├── user1_article.md 
└── group/
    └── project_note.md 
```
- 用户维度文件索引（/name=<username>）
- 随机推荐算法（random.sample实现）
 
系统交互流程 
1. 用户认证：各服务通过调用`http://127.0.0.1:5000/yz`验证token 
2. 内容创建：
   ```mermaid 
   graph TD 
   A[用户] -->|提交资源| B(资源服务5004)
   A -->|发布文章| C(文章服务5001)
   C --> D[生成MD文件]
   B --> E[更新resources.json]
   ```
3. 数据检索：
   - 普通搜索：调用5002服务进行全文检索 
   - 资源搜索：通过5004服务的/ss接口进行标题/简介匹配 
 
设计亮点 
1. 存储优化：
   - 采用JSON+Markdown混合存储 
   - 敏感操作记录时间戳（ISO 8601格式）
2. 安全机制：
   - 文件名消毒（sanitize_filename）
   - Token双重验证（各服务独立校验）
3. 性能方案：
   - 内存缓存索引（文档2、4）
   - 读写锁控制（threading.Lock）
   - 分片加载策略（文件缓存服务）
 
