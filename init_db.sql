-- ============================================================
-- 实验五：社交网络平台数据库初始化脚本
-- ============================================================

DROP DATABASE IF EXISTS SocialDB;
CREATE DATABASE SocialDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE SocialDB;

-- ------------------------------------------------------------
-- 1. 管理员表
-- ------------------------------------------------------------
CREATE TABLE Admin (
    admin_id   INT          PRIMARY KEY AUTO_INCREMENT,
    username   VARCHAR(30)  NOT NULL UNIQUE,
    password   CHAR(64)     NOT NULL,
    real_name  VARCHAR(20),
    email      VARCHAR(50)
);

-- ------------------------------------------------------------
-- 2. 用户表
-- ------------------------------------------------------------
CREATE TABLE User (
    user_id    INT          PRIMARY KEY AUTO_INCREMENT,
    username   VARCHAR(30)  NOT NULL UNIQUE,
    password   CHAR(64)     NOT NULL,
    real_name  VARCHAR(20),
    gender     ENUM('M','F','Other'),
    birthdate  DATE,
    age        INT          CHECK (age >= 0 AND age <= 150),
    created_at DATETIME     DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- 3. 好友分组表
-- ------------------------------------------------------------
CREATE TABLE FriendGroup (
    group_id   INT          PRIMARY KEY AUTO_INCREMENT,
    user_id    INT          NOT NULL,
    group_name VARCHAR(30)  NOT NULL,
    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE,
    UNIQUE (user_id, group_name)
);

-- ------------------------------------------------------------
-- 4. 好友关系表
--    业务上好友关系为双向；程序添加好友时会同时插入 A->B 和 B->A 两条记录。
-- ------------------------------------------------------------
CREATE TABLE Friendship (
    user_id    INT  NOT NULL,
    friend_id  INT  NOT NULL,
    group_id   INT,                      -- 所属分组，可为空
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, friend_id),
    CONSTRAINT chk_not_self_friend CHECK (user_id <> friend_id),
    FOREIGN KEY (user_id)   REFERENCES User(user_id) ON DELETE CASCADE,
    FOREIGN KEY (friend_id) REFERENCES User(user_id) ON DELETE CASCADE,
    FOREIGN KEY (group_id)  REFERENCES FriendGroup(group_id) ON DELETE SET NULL
);

-- ------------------------------------------------------------
-- 5. 朋友圈表（字数限制通过 CHECK 约束实现）
-- ------------------------------------------------------------
CREATE TABLE Post (
    post_id    INT           PRIMARY KEY AUTO_INCREMENT,
    user_id    INT           NOT NULL,
    content    VARCHAR(500)  NOT NULL,
    created_at DATETIME      DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME      DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_content_len CHECK (CHAR_LENGTH(content) <= 500),
    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- 6. 评论表
-- ------------------------------------------------------------
CREATE TABLE Comment (
    comment_id INT           PRIMARY KEY AUTO_INCREMENT,
    post_id    INT           NOT NULL,
    user_id    INT           NOT NULL,
    content    VARCHAR(200)  NOT NULL,
    created_at DATETIME      DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (post_id) REFERENCES Post(post_id) ON DELETE CASCADE,
    CONSTRAINT chk_comment_len CHECK (CHAR_LENGTH(content) <= 200),
    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- 7. 触发器：删除朋友圈时自动删除其所有评论
--    （ON DELETE CASCADE 已覆盖，此触发器作为显式演示）
-- ------------------------------------------------------------
DELIMITER $$
CREATE TRIGGER trg_delete_post_comments
BEFORE DELETE ON Post
FOR EACH ROW
BEGIN
    DELETE FROM Comment WHERE post_id = OLD.post_id;
END$$
DELIMITER ;

-- ------------------------------------------------------------
-- 8. 视图：查看某用户好友的朋友圈（含最近更新时间）
-- ------------------------------------------------------------
CREATE VIEW FriendPostView AS
SELECT
    f.user_id        AS viewer_id,
    u.username       AS author_username,
    p.post_id,
    p.content,
    p.created_at,
    p.updated_at
FROM Friendship f
JOIN Post p ON p.user_id = f.friend_id
JOIN User u ON u.user_id = f.friend_id;

-- ------------------------------------------------------------
-- 9. 初始化数据：1 位管理员 + 3 位用户 + 好友关系 + 朋友圈 + 评论
-- ------------------------------------------------------------
INSERT INTO Admin (username, password, real_name, email) VALUES
('admin', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', '系统管理员', 'admin@social.com');

INSERT INTO User (username, password, real_name, gender, birthdate, age) VALUES
('alice',   '4e40e8ffe0ee32fa53e139147ed559229a5930f89c2204706fc174beb36210b3', '爱丽丝', 'F', '2000-03-15', 24),
('bob',     '8d059c3640b97180dd2ee453e20d34ab0cb0f2eccbe87d01915a8e578a202b11', '鲍勃',   'M', '1999-07-20', 25),
('charlie', '1afda89737a745f15d42807d54f67c803727d75ce443b0f3a659531b38ae660f', '查理',   'M', '2001-11-05', 23);

-- alice 的好友分组
INSERT INTO FriendGroup (user_id, group_name) VALUES (1, '同学'), (1, '同事');

-- 好友关系按双向记录保存
INSERT INTO Friendship (user_id, friend_id, group_id) VALUES
(1, 2, 1),
(2, 1, NULL),
(1, 3, 1),
(3, 1, NULL);

-- 朋友圈
INSERT INTO Post (user_id, content) VALUES
(1, '今天天气真好，出去散步了！'),
(2, '刚看完一本好书，推荐给大家。'),
(3, '数据库实验终于做完了，开心！');

-- 评论
INSERT INTO Comment (post_id, user_id, content) VALUES
(1, 2, '羡慕你，我还在写代码...'),
(1, 3, '好羡慕！'),
(2, 1, '是什么书？推荐一下！');
