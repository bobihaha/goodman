"""
修复数据库表结构 - 添加缺失的 is_deleted 字段
"""
import asyncio
from sqlalchemy import text
from app.db.database import AsyncSessionLocal


async def fix_tables():
    """添加缺失的 is_deleted 字段"""
    
    sqls = [
        """
        ALTER TABLE stock_in_record_cards 
        ADD COLUMN is_deleted TINYINT DEFAULT 0 COMMENT '删除标记：0=未删除，1=已删除'
        """,
        """
        ALTER TABLE stock_out_record_cards 
        ADD COLUMN is_deleted TINYINT DEFAULT 0 COMMENT '删除标记：0=未删除，1=已删除'
        """,
        """
        ALTER TABLE stock_recycle_record_cards 
        ADD COLUMN is_deleted TINYINT DEFAULT 0 COMMENT '删除标记：0=未删除，1=已删除'
        """
    ]
    
    async with AsyncSessionLocal() as db:
        for sql in sqls:
            try:
                await db.execute(text(sql))
                await db.commit()
                print(f"✓ 执行成功: {sql.strip()[:50]}...")
            except Exception as e:
                if "Duplicate column name" in str(e):
                    print(f"⊙ 字段已存在，跳过")
                else:
                    print(f"✗ 执行失败: {e}")
                    await db.rollback()
    
    print("\n修复完成！")


if __name__ == "__main__":
    asyncio.run(fix_tables())

