ALTER TABLE sys_users
    ADD COLUMN open_api_app_id VARCHAR(64) NULL COMMENT '开放API APPID' AFTER h5_last_reset_at,
    ADD COLUMN open_api_app_secret VARCHAR(255) NULL COMMENT '开放API AppSecret' AFTER open_api_app_id,
    ADD COLUMN open_api_enabled TINYINT(1) NOT NULL DEFAULT 0 COMMENT '开放API是否启用: 0=否, 1=是' AFTER open_api_app_secret,
    ADD COLUMN open_api_last_reset_at DATETIME NULL COMMENT '开放API密钥最近重置时间' AFTER open_api_enabled;

CREATE UNIQUE INDEX uk_sys_users_open_api_app_id ON sys_users(open_api_app_id);
