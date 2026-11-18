-- 项目分组兼容初始化及排序。生产可能尚未创建 projects 表。
-- 只新增表/字段，不修改已有卡片归属；可重复运行，应用回滚时保留结构。
CREATE TABLE IF NOT EXISTS projects (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '项目ID',
    name VARCHAR(100) NOT NULL COMMENT '项目名称',
    user_id BIGINT UNSIGNED NOT NULL COMMENT '所属用户ID',
    remark VARCHAR(500) DEFAULT NULL COMMENT '备注',
    sort_order INT NOT NULL DEFAULT 0 COMMENT '账号内项目顺序',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_deleted TINYINT NOT NULL DEFAULT 0,
    PRIMARY KEY (id),
    KEY idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目表';

SET @project_sort_sql = IF(
    EXISTS (SELECT 1 FROM information_schema.columns
            WHERE table_schema = DATABASE() AND table_name = 'projects' AND column_name = 'sort_order'),
    'SELECT 1',
    'ALTER TABLE projects ADD COLUMN sort_order INT NOT NULL DEFAULT 0 COMMENT ''账号内项目顺序'''
);
PREPARE project_sort_stmt FROM @project_sort_sql;
EXECUTE project_sort_stmt;
DEALLOCATE PREPARE project_sort_stmt;

SET @card_project_sql = IF(
    EXISTS (SELECT 1 FROM information_schema.columns
            WHERE table_schema = DATABASE() AND table_name = 'iot_cards' AND column_name = 'project_id'),
    'SELECT 1',
    'ALTER TABLE iot_cards ADD COLUMN project_id BIGINT UNSIGNED DEFAULT NULL COMMENT ''所属项目ID'', ADD INDEX idx_project_id (project_id)'
);
PREPARE card_project_stmt FROM @card_project_sql;
EXECUTE card_project_stmt;
DEALLOCATE PREPARE card_project_stmt;
