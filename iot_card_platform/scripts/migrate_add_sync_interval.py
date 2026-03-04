#!/usr/bin/env python3
"""
数据库迁移脚本：添加供应商同步间隔字段
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.config import settings


def migrate():
    """执行迁移"""
    # 将异步URL转换为同步URL
    sync_url = settings.db_url.replace("aiomysql", "pymysql")
    engine = create_engine(sync_url)

    sql = "ALTER TABLE suppliers ADD COLUMN sync_interval INT DEFAULT 60 COMMENT '同步间隔(分钟)';"

    with engine.connect() as conn:
        try:
            conn.execute(text(sql))
            conn.commit()
            print("✓ 迁移成功：已添加 suppliers.sync_interval 字段")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print("✓ 字段已存在，跳过迁移")
            else:
                print(f"✗ 迁移失败：{e}")
                raise


if __name__ == "__main__":
    migrate()
