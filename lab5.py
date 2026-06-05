# ============================================================
# 实验五：社交网络平台  lab5.py
# 数据库：MySQL (SocialDB)
# 可在主菜单中选择执行 init_db.sql 完成数据库初始化
# ============================================================

import mysql.connector
from mysql.connector import Error
import os
import hashlib
from datetime import datetime

DB_CONFIG = {
    'host':     '127.0.0.1',
    'port':     3306,
    'user':     'root',
    'password': '',
    'database': 'SocialDB',
    'charset':  'utf8mb4',
}

POST_MAX_LEN = 500
COMMENT_MAX_LEN = 200


def get_conn():
    return mysql.connector.connect(**DB_CONFIG)


def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def close_db(cursor=None, conn=None):
    if cursor is not None:
        cursor.close()
    if conn is not None:
        conn.close()


def rollback(conn):
    if conn is not None:
        conn.rollback()


def normalize_gender(value):
    gender = value.strip().lower()
    if gender == 'm':
        return 'M'
    if gender == 'f':
        return 'F'
    if gender == 'other':
        return 'Other'
    return None


def input_optional_age(prompt):
    while True:
        age_str = input(prompt).strip()
        if not age_str:
            return None
        if age_str.isdigit():
            age = int(age_str)
            if 0 <= age <= 150:
                return age
        print("  年龄必须是 0 到 150 之间的整数，留空表示不填写。")


def input_optional_date(prompt):
    while True:
        value = input(prompt).strip()
        if not value:
            return None
        try:
            datetime.strptime(value, '%Y-%m-%d')
            return value
        except ValueError:
            print("  日期格式必须是 YYYY-MM-DD，例如 2000-03-15；留空表示不填写。")


def input_int(prompt):
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("  请输入数字。")

def print_menu(title, options):
    print(f"\n{'='*40}")
    print(f"  {title}")
    print(f"{'='*40}")
    for key, desc in options:
        print(f"  {key}. {desc}")
    print(f"{'='*40}")


# ============================================================
# 数据库初始化
# ============================================================

def init_database():
    sql_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'init_db.sql')
    if not os.path.exists(sql_file):
        print("[警告] 未找到 init_db.sql，跳过初始化。")
        return False
    base_cfg = {k: v for k, v in DB_CONFIG.items() if k != 'database'}
    conn = None
    cursor = None
    success = False
    try:
        conn = mysql.connector.connect(**base_cfg)
        cursor = conn.cursor()
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        statements = []
        current = []
        delimiter = ';'
        for line in sql_content.splitlines():
            stripped = line.strip()
            if stripped.upper().startswith('DELIMITER'):
                parts = stripped.split()
                delimiter = parts[1] if len(parts) > 1 else ';'
                continue
            current.append(line)
            if stripped.endswith(delimiter):
                stmt = '\n'.join(current).strip()
                statements.append(stmt[:-len(delimiter)].strip())
                current = []
        for stmt in statements:
            if stmt:
                cursor.execute(stmt)
        if conn is not None:
            conn.commit()
        success = True
        print("[初始化] 数据库初始化完成。\n")
        return True
    except Error as e:
        rollback(conn)
        print(f"[初始化失败] {e}")
        return False
    finally:
        if conn is not None and not success:
            rollback(conn)
        close_db(cursor, conn)


def check_database_ready():
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchall()
        return True
    except Error as e:
        print(f"  数据库不可用: {e}")
        print("  请先在主菜单选择“初始化/重置数据库”，或检查 MySQL 配置。")
        return False
    finally:
        close_db(cursor, conn)


# ============================================================
# 用户功能
# ============================================================

def user_register():
    print("\n--- 用户注册 ---")
    username  = input("  用户名: ").strip()
    password  = input("  密码: ").strip()
    if not username:
        print("  用户名不能为空。")
        return
    if not password:
        print("  密码不能为空。")
        return
    real_name = input("  真实姓名: ").strip()
    gender    = normalize_gender(input("  性别 (M/F/Other): "))
    if gender is None:
        gender = 'Other'
    birthdate = input_optional_date("  出生日期 YYYY-MM-DD（留空跳过）: ")
    age       = input_optional_age("  年龄（留空跳过）: ")
    conn = None
    cursor = None
    try:
        conn   = get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO User (username, password, real_name, gender, birthdate, age) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (username, hash_password(password), real_name, gender, birthdate, age)
        )
        conn.commit()
        print(f"  注册成功！欢迎 {username}。")
    except Error as e:
        print(f"  注册失败: {e}")
    finally:
        close_db(cursor, conn)


def user_login():
    print("\n--- 用户登录 ---")
    username = input("  用户名: ").strip()
    password = input("  密码: ").strip()
    conn = None
    cursor = None
    try:
        conn   = get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id, real_name FROM User "
            "WHERE username=%s AND password=%s",
            (username, hash_password(password))
        )
        row = cursor.fetchone()
        if row is None:
            print("  用户名或密码错误。")
            return None
        print(f"  登录成功！你好，{row[1] or username}。")
        return row[0]
    except Error as e:
        print(f"  登录失败: {e}")
        return None
    finally:
        close_db(cursor, conn)


def user_update_profile(user_id):
    print("\n--- 修改个人信息 ---")
    real_name = input("  新姓名（留空跳过）: ").strip()
    gender    = normalize_gender(input("  新性别 M/F/Other（留空跳过）: "))
    birthdate = input_optional_date("  新出生日期 YYYY-MM-DD（留空跳过）: ")
    age       = input_optional_age("  新年龄（留空跳过）: ")
    updates, params = [], []
    if real_name:
        updates.append("real_name=%s"); params.append(real_name)
    if gender is not None:
        updates.append("gender=%s"); params.append(gender)
    if birthdate:
        updates.append("birthdate=%s"); params.append(birthdate)
    if age is not None:
        updates.append("age=%s"); params.append(age)
    if not updates:
        print("  未做任何修改。"); return
    params.append(user_id)
    conn = None
    cursor = None
    try:
        conn   = get_conn()
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE User SET {', '.join(updates)} WHERE user_id=%s", params
        )
        conn.commit()
        print("  个人信息更新成功。")
    except Error as e:
        print(f"  更新失败: {e}")
    finally:
        close_db(cursor, conn)

# ============================================================
# 好友管理
# ============================================================

def search_user(keyword):
    conn = None
    cursor = None
    try:
        conn   = get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id, username, real_name FROM User "
            "WHERE username LIKE %s",
            (f'%{keyword}%',)
        )
        rows = cursor.fetchall()
        if rows:
            print("  搜索结果：")
            for r in rows:
                print(f"    ID={r[0]}  用户名={r[1]}  姓名={r[2]}")
        else:
            print("  未找到匹配用户。")
        return rows
    except Error as e:
        print(f"  搜索失败: {e}")
        return []
    finally:
        close_db(cursor, conn)


def add_friend(user_id):
    keyword = input("  输入要添加的用户名关键词: ").strip()
    results = search_user(keyword)
    if not results:
        return
    friend_id = input_int("  输入要添加的用户 ID: ")
    if friend_id == user_id:
        print("  不能添加自己为好友。"); return
    conn = None
    cursor = None
    try:
        conn   = get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM User WHERE user_id=%s", (friend_id,)
        )
        if cursor.fetchone() is None:
            print("  该用户不存在。")
            return
        cursor.execute(
            "SELECT group_id, group_name FROM FriendGroup WHERE user_id=%s", (user_id,)
        )
        groups   = cursor.fetchall()
        valid_groups = {g[0] for g in groups}
        group_id = None
        if groups:
            print("  你的好友分组：")
            for g in groups:
                print(f"    {g[0]}. {g[1]}")
            gid_str = input("  选择分组 ID（留空不分组）: ").strip()
            if gid_str.isdigit():
                group_id = int(gid_str)
                if group_id not in valid_groups:
                    print("  分组不存在或不属于当前用户。")
                    return
        #conn.start_transaction()
        cursor.execute(
            "INSERT IGNORE INTO Friendship (user_id, friend_id, group_id) "
            "VALUES (%s, %s, %s)",
            (user_id, friend_id, group_id)
        )
        inserted_forward = cursor.rowcount
        cursor.execute(
            "INSERT IGNORE INTO Friendship (user_id, friend_id, group_id) "
            "VALUES (%s, %s, NULL)",
            (friend_id, user_id)
        )
        inserted_reverse = cursor.rowcount
        conn.commit()
        inserted_total = inserted_forward + inserted_reverse
        if inserted_total == 0:
            print("  已经是好友，无需重复添加。")
        elif inserted_total == 1:
            print("  好友关系已补全为双向。")
        else:
            print("  好友添加成功。")
    except Error as e:
        rollback(conn)
        print(f"  添加失败: {e}")
    finally:
        close_db(cursor, conn)


def remove_friend(user_id):
    friend_id = input_int("  输入要删除的好友 ID: ")
    conn = None
    cursor = None
    try:
        conn   = get_conn()
        cursor = conn.cursor()
        conn.start_transaction()
        cursor.execute(
            "DELETE FROM Friendship WHERE user_id=%s AND friend_id=%s",
            (user_id, friend_id)
        )
        deleted_forward = cursor.rowcount
        cursor.execute(
            "DELETE FROM Friendship WHERE user_id=%s AND friend_id=%s",
            (friend_id, user_id)
        )
        deleted_reverse = cursor.rowcount
        conn.commit()
        if deleted_forward + deleted_reverse == 0:
            print("  未找到该好友关系。")
        else:
            print("  好友已删除。")
    except Error as e:
        rollback(conn)
        print(f"  删除失败: {e}")
    finally:
        close_db(cursor, conn)


def list_friends(user_id):
    conn = None
    cursor = None
    try:
        conn   = get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.user_id, u.username, u.real_name, fg.group_name
            FROM Friendship f
            JOIN User u ON u.user_id = f.friend_id
            LEFT JOIN FriendGroup fg ON fg.group_id = f.group_id
            WHERE f.user_id = %s
        """, (user_id,))
        rows = cursor.fetchall()
        if rows:
            print("  好友列表：")
            for r in rows:
                print(f"    ID={r[0]}  {r[1]}({r[2]})  分组:{r[3] or '未分组'}")
        else:
            print("  暂无好友。")
    except Error as e:
        print(f"  查询失败: {e}")
    finally:
        close_db(cursor, conn)


def manage_friend_groups(user_id):
    print_menu("好友分组管理", [('1', '新建分组'), ('2', '将好友移入分组'), ('0', '返回')])
    choice = input("  选择: ").strip()
    conn = None
    cursor = None
    try:
        conn   = get_conn()
        cursor = conn.cursor()
        if choice == '1':
            gname = input("  分组名称: ").strip()
            if not gname:
                print("  分组名称不能为空。")
                return
            cursor.execute(
                "INSERT INTO FriendGroup (user_id, group_name) VALUES (%s, %s)",
                (user_id, gname)
            )
            conn.commit()
            print("  分组创建成功。")
        elif choice == '2':
            cursor.execute(
                "SELECT group_id, group_name FROM FriendGroup WHERE user_id=%s",
                (user_id,)
            )
            groups = cursor.fetchall()
            if not groups:
                print("  当前还没有分组，请先新建分组。")
                return
            print("  你的好友分组：")
            for g in groups:
                print(f"    {g[0]}. {g[1]}")
            friend_id = input_int("  好友 ID: ")
            group_id  = input_int("  目标分组 ID: ")
            cursor.execute(
                "SELECT 1 FROM Friendship WHERE user_id=%s AND friend_id=%s",
                (user_id, friend_id)
            )
            if cursor.fetchone() is None:
                print("  该用户不是你的好友。")
                return
            cursor.execute(
                "SELECT 1 FROM FriendGroup WHERE group_id=%s AND user_id=%s",
                (group_id, user_id)
            )
            if cursor.fetchone() is None:
                print("  分组不存在或不属于当前用户。")
                return
            cursor.execute(
                "UPDATE Friendship SET group_id=%s WHERE user_id=%s AND friend_id=%s",
                (group_id, user_id, friend_id)
            )
            conn.commit()
            if cursor.rowcount == 0:
                print("  未找到该好友关系。")
            else:
                print("  已更新分组。")
        elif choice == '0':
            return
        else:
            print("  无效选项。")
    except Error as e:
        print(f"  操作失败: {e}")
    finally:
        close_db(cursor, conn)

# ============================================================
# 朋友圈模块
# ============================================================

def post_create(user_id):
    content = input(f"  内容（最多{POST_MAX_LEN}字）: ").strip()
    if len(content) > POST_MAX_LEN:
        print(f"  内容超过{POST_MAX_LEN}字限制。"); return
    if not content:
        print("  内容不能为空。"); return
    conn = None
    cursor = None
    try:
        conn   = get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Post (user_id, content) VALUES (%s, %s)", (user_id, content)
        )
        conn.commit()
        print("  朋友圈发表成功。")
    except Error as e:
        print(f"  发表失败: {e}")
    finally:
        close_db(cursor, conn)


def post_edit(user_id):
    post_id     = input_int("  输入要修改的朋友圈 ID: ")
    new_content = input(f"  新内容（最多{POST_MAX_LEN}字）: ").strip()
    if len(new_content) > POST_MAX_LEN:
        print("  内容超过字数限制。"); return
    if not new_content:
        print("  内容不能为空。"); return
    conn = None
    cursor = None
    try:
        conn   = get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE Post SET content=%s WHERE post_id=%s AND user_id=%s",
            (new_content, post_id, user_id)
        )
        conn.commit()
        if cursor.rowcount == 0:
            print("  未找到该朋友圈或无权修改。")
        else:
            print("  修改成功。")
    except Error as e:
        print(f"  修改失败: {e}")
    finally:
        close_db(cursor, conn)


def post_delete(user_id):
    post_id = input_int("  输入要删除的朋友圈 ID: ")
    conn = None
    cursor = None
    try:
        conn   = get_conn()
        cursor = conn.cursor()
        conn.start_transaction()
        cursor.execute(
            "DELETE FROM Post WHERE post_id=%s AND user_id=%s", (post_id, user_id)
        )
        conn.commit()
        if cursor.rowcount == 0:
            print("  未找到该朋友圈或无权删除。")
        else:
            print("  朋友圈及其评论已删除（触发器自动处理）。")
    except Error as e:
        rollback(conn)
        print(f"  删除失败: {e}")
    finally:
        close_db(cursor, conn)


def view_friend_posts(user_id):
    conn = None
    cursor = None
    try:
        conn   = get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT post_id, author_username, content, created_at, updated_at "
            "FROM FriendPostView WHERE viewer_id=%s ORDER BY updated_at DESC",
            (user_id,)
        )
        posts = cursor.fetchall()
        if not posts:
            print("  好友暂无朋友圈。"); return
        for p in posts:
            print(f"\n  [帖子ID:{p[0]}] @{p[1]}  发布:{p[3]}  更新:{p[4]}")
            print(f"  {p[2]}")
            cursor.execute(
                "SELECT u.username, c.content, c.created_at "
                "FROM Comment c JOIN User u ON u.user_id=c.user_id "
                "WHERE c.post_id=%s ORDER BY c.created_at",
                (p[0],)
            )
            comments = cursor.fetchall()
            if comments:
                print("  评论：")
                for c in comments:
                    print(f"    @{c[0]}: {c[1]}  ({c[2]})")
    except Error as e:
        print(f"  查询失败: {e}")
    finally:
        close_db(cursor, conn)


def view_my_posts(user_id):
    conn = None
    cursor = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT post_id, content, created_at, updated_at
            FROM Post
            WHERE user_id=%s
            ORDER BY updated_at DESC
        """, (user_id,))
        posts = cursor.fetchall()
        if not posts:
            print("  你还没有发表朋友圈。")
            return
        for p in posts:
            print(f"\n  [帖子ID:{p[0]}]  发布:{p[2]}  更新:{p[3]}")
            print(f"  {p[1]}")
            cursor.execute(
                "SELECT u.username, c.content, c.created_at "
                "FROM Comment c JOIN User u ON u.user_id=c.user_id "
                "WHERE c.post_id=%s ORDER BY c.created_at",
                (p[0],)
            )
            comments = cursor.fetchall()
            if comments:
                print("  评论：")
                for c in comments:
                    print(f"    @{c[0]}: {c[1]}  ({c[2]})")
    except Error as e:
        print(f"  查询失败: {e}")
    finally:
        close_db(cursor, conn)


def add_comment(user_id):
    post_id = input_int("  输入要评论的朋友圈 ID: ")
    content = input("  评论内容: ").strip()
    if not content:
        print("  评论不能为空。"); return
    if len(content) > COMMENT_MAX_LEN:
        print(f"  评论不能超过{COMMENT_MAX_LEN}字。"); return
    conn = None
    cursor = None
    try:
        conn   = get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 1
            FROM Post p
            JOIN Friendship f ON f.friend_id = p.user_id
            WHERE p.post_id=%s AND f.user_id=%s
        """, (post_id, user_id))
        if cursor.fetchone() is None:
            print("  只能评论好友的朋友圈。")
            return
        cursor.execute(
            "INSERT INTO Comment (post_id, user_id, content) VALUES (%s, %s, %s)",
            (post_id, user_id, content)
        )
        conn.commit()
        print("  评论成功。")
    except Error as e:
        print(f"  评论失败: {e}")
    finally:
        close_db(cursor, conn)

# ============================================================
# 管理员功能
# ============================================================

def admin_login():
    print("\n--- 管理员登录 ---")
    username = input("  管理员账号: ").strip()
    password = input("  密码: ").strip()
    conn = None
    cursor = None
    try:
        conn   = get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT admin_id, real_name FROM Admin "
            "WHERE username=%s AND password=%s",
            (username, hash_password(password))
        )
        row = cursor.fetchone()
        if row is None:
            print("  账号或密码错误。")
            return None
        print(f"  管理员登录成功！你好，{row[1] or username}。")
        return row[0]
    except Error as e:
        print(f"  登录失败: {e}")
        return None
    finally:
        close_db(cursor, conn)


def admin_update_profile(admin_id):
    print("\n--- 修改管理员信息 ---")
    real_name = input("  新姓名（留空跳过）: ").strip()
    email     = input("  新邮箱（留空跳过）: ").strip()
    updates, params = [], []
    if real_name:
        updates.append("real_name=%s"); params.append(real_name)
    if email:
        updates.append("email=%s"); params.append(email)
    if not updates:
        print("  未做任何修改。"); return
    params.append(admin_id)
    conn = None
    cursor = None
    try:
        conn   = get_conn()
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE Admin SET {', '.join(updates)} WHERE admin_id=%s", params
        )
        conn.commit()
        print("  信息更新成功。")
    except Error as e:
        print(f"  更新失败: {e}")
    finally:
        close_db(cursor, conn)


def admin_deactivate_user():
    """
    注销用户：使用事务删除该用户及所有关联信息。
    """
    keyword = input("  输入要注销的用户名关键词: ").strip()
    conn = None
    cursor = None
    try:
        conn   = get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id, username FROM User WHERE username LIKE %s",
            (f'%{keyword}%',)
        )
        rows = cursor.fetchall()
        if not rows:
            print("  未找到用户。"); return
        for r in rows:
            print(f"    ID={r[0]}  {r[1]}")
        uid = input_int("  输入要注销的用户 ID: ")
        if uid not in {r[0] for r in rows}:
            print("  输入的 ID 不在本次搜索结果中。")
            return

        #conn.start_transaction()
        cursor.execute("DELETE FROM User WHERE user_id=%s", (uid,))
        conn.commit()
        if cursor.rowcount == 0:
            print("  未找到该用户。")
        else:
            print("  用户已注销，相关数据已清除。")
    except Error as e:
        rollback(conn)
        print(f"  注销失败: {e}")
    finally:
        close_db(cursor, conn)


def admin_view_all_posts():
    """管理员浏览所有朋友圈（不显示用户个人信息）"""
    conn = None
    cursor = None
    try:
        conn   = get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT post_id, content, created_at, updated_at
            FROM Post
            ORDER BY updated_at DESC
        """)
        posts = cursor.fetchall()
        if not posts:
            print("  暂无朋友圈。"); return
        for p in posts:
            print(f"\n  [帖子ID:{p[0]}]  发布:{p[2]}  更新:{p[3]}")
            print(f"  {p[1]}")
    except Error as e:
        print(f"  查询失败: {e}")
    finally:
        close_db(cursor, conn)


def admin_delete_post():
    """管理员删除朋友圈（审核）"""
    post_id = input_int("  输入要删除的朋友圈 ID: ")
    conn = None
    cursor = None
    try:
        conn   = get_conn()
        cursor = conn.cursor()
        conn.start_transaction()
        cursor.execute("DELETE FROM Post WHERE post_id=%s", (post_id,))
        conn.commit()
        if cursor.rowcount == 0:
            print("  未找到该朋友圈。")
        else:
            print("  朋友圈已删除（评论已同步删除）。")
    except Error as e:
        rollback(conn)
        print(f"  删除失败: {e}")
    finally:
        close_db(cursor, conn)

# ============================================================
# 菜单循环
# ============================================================

def user_menu(user_id):
    while True:
        print_menu("用户菜单", [
            ('1', '修改个人信息'),
            ('2', '搜索用户'),
            ('3', '添加好友'),
            ('4', '删除好友'),
            ('5', '查看好友列表'),
            ('6', '好友分组管理'),
            ('7', '发表朋友圈'),
            ('8', '修改朋友圈'),
            ('9', '删除朋友圈'),
            ('10', '查看好友朋友圈'),
            ('11', '查看我的朋友圈'),
            ('12', '评论朋友圈'),
            ('0', '退出登录'),
        ])
        choice = input("  请选择: ").strip()
        if   choice == '1':  user_update_profile(user_id)
        elif choice == '2':  search_user(input("  关键词: ").strip())
        elif choice == '3':  add_friend(user_id)
        elif choice == '4':  remove_friend(user_id)
        elif choice == '5':  list_friends(user_id)
        elif choice == '6':  manage_friend_groups(user_id)
        elif choice == '7':  post_create(user_id)
        elif choice == '8':  post_edit(user_id)
        elif choice == '9':  post_delete(user_id)
        elif choice == '10': view_friend_posts(user_id)
        elif choice == '11': view_my_posts(user_id)
        elif choice == '12': add_comment(user_id)
        elif choice == '0':  print("  已退出登录。"); break
        else: print("  无效选项。")


def admin_menu(admin_id):
    while True:
        print_menu("管理员菜单", [
            ('1', '修改个人信息'),
            ('2', '注销用户'),
            ('3', '浏览所有朋友圈'),
            ('4', '删除朋友圈（审核）'),
            ('0', '退出登录'),
        ])
        choice = input("  请选择: ").strip()
        if   choice == '1': admin_update_profile(admin_id)
        elif choice == '2': admin_deactivate_user()
        elif choice == '3': admin_view_all_posts()
        elif choice == '4': admin_delete_post()
        elif choice == '0': print("  已退出登录。"); break
        else: print("  无效选项。")


def system_menu():
    while True:
        print_menu("社交网络平台", [
            ('1', '用户注册'),
            ('2', '用户登录'),
            ('3', '管理员登录'),
            ('0', '返回主菜单'),
        ])
        choice = input("  请选择: ").strip()
        if choice == '1':
            user_register()
        elif choice == '2':
            uid = user_login()
            if uid:
                user_menu(uid)
        elif choice == '3':
            aid = admin_login()
            if aid:
                admin_menu(aid)
        elif choice == '0':
            break
        else:
            print("  无效选项。")


def main():
    while True:
        print_menu("Lab5 数据库应用系统", [
            ('1', '初始化/重置数据库'),
            ('2', '启动系统'),
            ('0', '退出程序'),
        ])
        choice = input("  请选择: ").strip()
        if choice == '1':
            init_database()
        elif choice == '2':
            if check_database_ready():
                system_menu()
        elif choice == '0':
            print("  再见！")
            break
        else:
            print("  无效选项。")


if __name__ == "__main__":
    main()
