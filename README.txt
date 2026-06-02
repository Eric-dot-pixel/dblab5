============================================================
实验五：社交网络平台  运行说明
============================================================

【环境要求】
- Python 3.x（推荐 3.10+）
- MySQL 8.0+（需提前安装并启动）

【文件清单】
  lab5.py          主程序
  init_db.sql      数据库初始化脚本
  requirements.txt Python 依赖清单

【运行步骤】

1. 安装 Python 依赖
   打开命令行，进入本文件夹，执行：
   pip install -r requirements.txt

2. 修改数据库连接密码
   用文本编辑器打开 lab5.py，找到第 12 行：
     'password': '',
   改成你自己 MySQL 的 root 密码。

3. 运行程序
   python lab5.py
   程序启动时会自动执行 init_db.sql 初始化数据库，无需手动执行 SQL。

【初始账号】
  管理员：admin / admin123
  用户：  alice / alice123
         bob   / bob123
         charlie / charlie123

【注意】
  每次运行 lab5.py 会重建数据库（DROP DATABASE IF EXISTS SocialDB），
  如不想重置数据，第二次运行前可将 init_db.sql 中第一行注释掉：
  -- DROP DATABASE IF EXISTS SocialDB;

  数据库中保存的是 SHA-256 哈希后的密码，登录时仍使用上方明文初始账号即可。
