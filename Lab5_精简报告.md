# 实验五 数据库应用开发大作业精简报告

## 1. 系统总体设计

本系统是基于 MySQL 的命令行社交网络平台，数据库名为 `SocialDB`，主程序为 `lab5.py`，初始化脚本为 `init_db.sql`。系统分为普通用户和管理员两类角色：普通用户完成注册登录、资料维护、用户搜索、好友与分组管理、朋友圈发布/修改/删除/查看和好友朋友圈评论；管理员完成登录、资料维护、用户注销、全站朋友圈浏览和违规朋友圈删除。

系统采用 Python + `mysql-connector-python` 连接 MySQL。程序启动后可选择执行 `init_db.sql` 初始化/重置数据库，也可直接进入业务系统；初始化脚本负责建库、建表、完整性约束、视图、触发器和测试数据，应用层负责菜单交互、输入校验、权限判断、参数化 SQL 执行、事务提交与异常回滚。

## 2. ER 图

<img src="Lab5_ER图.svg" alt="ER图" width="420">

主要实体包括 `Admin`、`User`、`FriendGroup`、`Friendship`、`Post`、`Comment`。关系如下：用户和好友分组为 1:N；用户和朋友圈为 1:N；朋友圈和评论为 1:N；用户和评论为 1:N；好友关系用 `Friendship(user_id, friend_id)` 表示，业务上为双向关系，添加好友时由程序同时写入 A->B 与 B->A 两条记录。

## 3. 表结构

| 表 | 主键 | 主要字段 | 外键与说明 |
| --- | --- | --- | --- |
| `Admin` | `admin_id` | `username`、`password`、`real_name`、`email` | 管理员账号表；`username` 唯一，密码保存 SHA-256 哈希 |
| `User` | `user_id` | `username`、`password`、`real_name`、`gender`、`birthdate`、`age`、`created_at` | 用户表；`username` 唯一，`gender` 为 `M/F/Other`，`age` 限制 0-150 |
| `FriendGroup` | `group_id` | `user_id`、`group_name` | `user_id` -> `User`；同一用户分组名唯一，用户删除时级联删除分组 |
| `Friendship` | `(user_id, friend_id)` | `group_id`、`created_at` | `user_id`、`friend_id` -> `User`，`group_id` -> `FriendGroup`；禁止自己加自己 |
| `Post` | `post_id` | `user_id`、`content`、`created_at`、`updated_at` | `user_id` -> `User`；内容最长 500 字，用户删除时级联删除朋友圈 |
| `Comment` | `comment_id` | `post_id`、`user_id`、`content`、`created_at` | `post_id` -> `Post`，`user_id` -> `User`；内容最长 200 字，朋友圈或用户删除时级联删除评论 |

此外创建视图 `FriendPostView(viewer_id, author_username, post_id, content, created_at, updated_at)`，将 `Friendship`、`Post`、`User` 连接，用于普通用户按好友关系查看朋友圈。

## 4. 约束与安全设计

数据库端完整性约束包括：各表主键约束；`Admin.username`、`User.username`、`FriendGroup(user_id, group_name)` 唯一约束；`FriendGroup.user_id`、`Friendship.user_id/friend_id/group_id`、`Post.user_id`、`Comment.post_id/user_id` 外键约束；`ON DELETE CASCADE` 自动清理用户相关分组、好友关系、朋友圈和评论，`ON DELETE SET NULL` 在分组删除后保留好友关系；`CHECK` 约束限制年龄、朋友圈长度、评论长度和禁止自加好友；`ENUM` 约束限定性别取值。

应用端约束包括：所有 SQL 使用参数化查询，避免 SQL 注入；密码经 SHA-256 哈希后存储；注册、资料修改、发帖、评论等入口检查空值、日期格式、年龄范围和内容长度；添加好友时检查目标用户存在、不能为自己、避免重复关系；移动好友分组时检查分组归属当前用户；评论只允许评论好友的朋友圈；用户只能修改或删除自己的朋友圈，管理员仅通过管理员菜单执行全站管理操作。

## 5. 事务与触发器说明

系统对影响多表一致性的操作使用事务，程序通过 `conn.start_transaction()` 开启事务，成功后 `commit()`，异常时 `rollback()`。

| 操作 | 事务目的 |
| --- | --- |
| 添加好友 | 同时插入双向好友关系，任一方向失败则回滚 |
| 删除好友 | 同时删除双向好友关系，保证双方关系一致 |
| 删除朋友圈 | 删除帖子并同步清理评论，避免残留评论 |
| 管理员注销用户 | 删除用户并依赖外键级联清理分组、好友、朋友圈、评论 |
| 管理员删除朋友圈 | 审核删除指定帖子及其评论，失败回滚 |

触发器 `trg_delete_post_comments` 定义在 `Post` 表的 `BEFORE DELETE` 上，删除朋友圈前执行 `DELETE FROM Comment WHERE post_id = OLD.post_id`，用于显式展示数据库自动维护关联评论的能力；`Comment.post_id ON DELETE CASCADE` 同时提供引用完整性的数据库级保障。

## 6. 小组分工

| 成员 | 分工 |
| --- | --- |
| 滕飞 | 数据库需求分析、ER 图设计、表结构与约束设计、视图和触发器设计 |
| 蔡纪坤 | Python 主程序、用户/管理员功能、事务与异常处理、测试与报告整理 |

