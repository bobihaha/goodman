#!/usr/bin/env python3
"""
数据库迁移脚本执行器
用法: python scripts/run_migration.py sql/add_project_management.sql
"""
import sys
import os
import asyncio
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.db.database import engine


async def run_migration(sql_file: str):
    """执行 SQL 迁移脚本"""
    if not os.path.exists(sql_file):
        print(f"❌ 文件不存在: {sql_file}")
        return False

    print(f"📄 读取 SQL 文件: {sql_file}")
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    # 分割 SQL 语句（按分号分割，但跳过注释）
    statements = []
    current = []
    for line in sql_content.split('\n'):
        line = line.strip()
        if not line or line.startswith('--'):
            continue
        current.append(line)
        if line.endswith(';'):
            statements.append(' '.join(current))
            current = []

    print(f"📊 共 {len(statements)} 条 SQL 语句")

    async with engine.begin() as conn:
        for i, stmt in enumerate(statements, 1):
            try:
                print(f"⚙️  执行语句 {i}/{len(statements)}...")
                result = await conn.execute(text(stmt))
                if result.returns_rows:
                    rows = result.fetchall()
                    for row in rows:
                        print(f"   {dict(row._mapping)}")
            except Exception as e:
                print(f"❌ 执行失败: {e}")
                return False

    print("✅ 迁移完成")
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python scripts/run_migration.py <sql_file>")
        sys.exit(1)

    sql_file = sys.argv[1]
    success = asyncio.run(run_migration(sql_file))
    sys.exit(0 if success else 1)
