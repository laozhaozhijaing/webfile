        用户注册 
    ─────────────────────────────────────── 
    注册验证（发送验证码）
    GET http://127.0.0.1:5000/newuser?name=用户名&mail=邮箱&passwd=密码 
     
    注册确认 
    GET http://127.0.0.1:5000/newuser2?name=用户名&yzm=验证码 
     
    密码重置 
    ─────────────────────────────────────── 
    重置验证（发送验证码）
    GET http://127.0.0.1:5000/newpasswd?name=用户名&mail=邮箱 
     
    重置确认 
    GET http://127.0.0.1:5000/newpasswd2?name=用户名&yzm=验证码 
     
    用户登录 
    ─────────────────────────────────────── 
    获取token 
    GET http://127.0.0.1:5000/login?name=用户名&passwd=密码 
     
    Token验证 
    ─────────────────────────────────────── 
    验证token有效性 
    GET http://127.0.0.1:5000/yz?token=用户token 

    文章和评论系统
    ─────────────────────────────────────── 
    
    创建文章
    http://127.0.0.1:5001/wz?nam=示例文章&newwz=# Hello World&token=valid_token

    获取文章
    http://127.0.0.1:5001/wzdq?nam=示例文章

    添加主评论
    http://127.0.0.1:5001/pl?nam=示例文章&data=好文章！&token=valid_token

    添加回复（假设主评论ID=1）
    http://127.0.0.1:5001/pl?nam=示例文章&data=我同意&reply_to=1&token=valid_token

    给文章点赞
    http://127.0.0.1:5001/pl?nam=示例文章&dz=wz

    给评论点赞（假设评论ID=1）
    http://127.0.0.1:5001/pl?nam=示例文章&dz=1

    置顶评论
    http://127.0.0.1:5001/pl?nam=示例文章&zd=2&token=valid_token

    删除评论
    http://127.0.0.1:5001/pl?nam=示例文章&sc=3&token=valid_token

    获取评论列表
    http://127.0.0.1:5001/plfh?nam=示例文章

    删除文章
    http://127.0.0.1:5001/rm?nam=示例文章&token=valid_token

    新建资源：
    http://127.0.0.1:5004/new?biaoti=Python入门教程&ziyuan1=https://pan.example.com/1234&ziyuan2=https://pan.example.com/5678&jieshao=适合新手的Python教程合集&token=valid_token_here

    查看资源：
    http://127.0.0.1:5004/chakan?biaoti=Python入门教程

    查看用户所有资源：
    http://127.0.0.1:5004/yongh?name=name

    搜索资源：
    http://127.0.0.1:5004/ss?name=name

    筛选用户文章
    http://127.0.0.1:5005/yongh?name=用户名 

    随机推送文章
    http://127.0.0.1:5005/ss

    搜索文章
    http://127.0.0.1:5002/ss?name=zty192

    返回前50名搜索热门词汇
    http://127.0.0.1：5002/phb
    
    
