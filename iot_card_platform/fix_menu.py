"""
修复菜单乱码
"""
import asyncio
from app.db.database import get_db
from sqlalchemy import text

async def fix_menu():
    async for db in get_db():
        try:
            # 修复菜单乱码
            sql = text("UPDATE sys_menus SET name = '出入库记录' WHERE code = 'stock_records'")
            result = await db.execute(sql)
            await db.commit()
            print(f"✅ 菜单名称已修复，影响行数: {result.rowcount}")
            
            # 验证
            sql = text("SELECT id, code, name, path FROM sys_menus WHERE code = 'stock_records'")
            result = await db.execute(sql)
            row = result.fetchone()
            if row:
                print(f"菜单信息: ID={row[0]}, Code={row[1]}, Name={row[2]}, Path={row[3]}")
            else:
                print("未找到菜单")
        except Exception as e:
            print(f"❌ 错误: {e}")
        finally:
            break

if __name__ == "__main__":
    asyncio.run(fix_menu())

修复菜单乱码
"""
import asyncio
from app.db.database import get_db
from sqlalchemy import text

async def fix_menu():
    async for db in get_db():
        try:
            # 修复菜单乱码
            sql = text("UPDATE sys_menus SET name = '出入库记录' WHERE code = 'stock_records'")
            result = await db.execute(sql)
            await db.commit()
            print(f"✅ 菜单名称已修复，影响行数: {result.rowcount}")
            
            # 验证
            sql = text("SELECT id, code, name, path FROM sys_menus WHERE code = 'stock_records'")
            result = await db.execute(sql)
            row = result.fetchone()
            if row:
                print(f"菜单信息: ID={row[0]}, Code={row[1]}, Name={row[2]}, Path={row[3]}")
            else:
                print("未找到菜单")
        except Exception as e:
            print(f"❌ 错误: {e}")
        finally:
            break

if __name__ == "__main__":
    asyncio.run(fix_menu())

修复菜单乱码
"""
import asyncio
from app.db.database import get_db
from sqlalchemy import text

async def fix_menu():
    async for db in get_db():
        try:
            # 修复菜单乱码
            sql = text("UPDATE sys_menus SET name = '出入库记录' WHERE code = 'stock_records'")
            result = await db.execute(sql)
            await db.commit()
            print(f"✅ 菜单名称已修复，影响行数: {result.rowcount}")
            
            # 验证
            sql = text("SELECT id, code, name, path FROM sys_menus WHERE code = 'stock_records'")
            result = await db.execute(sql)
            row = result.fetchone()
            if row:
                print(f"菜单信息: ID={row[0]}, Code={row[1]}, Name={row[2]}, Path={row[3]}")
            else:
                print("未找到菜单")
        except Exception as e:
            print(f"❌ 错误: {e}")
        finally:
            break

if __name__ == "__main__":
    asyncio.run(fix_menu())

修复菜单乱码
"""
import asyncio
from app.db.database import get_db
from sqlalchemy import text

async def fix_menu():
    async for db in get_db():
        try:
            # 修复菜单乱码
            sql = text("UPDATE sys_menus SET name = '出入库记录' WHERE code = 'stock_records'")
            result = await db.execute(sql)
            await db.commit()
            print(f"✅ 菜单名称已修复，影响行数: {result.rowcount}")
            
            # 验证
            sql = text("SELECT id, code, name, path FROM sys_menus WHERE code = 'stock_records'")
            result = await db.execute(sql)
            row = result.fetchone()
            if row:
                print(f"菜单信息: ID={row[0]}, Code={row[1]}, Name={row[2]}, Path={row[3]}")
            else:
                print("未找到菜单")
        except Exception as e:
            print(f"❌ 错误: {e}")
        finally:
            break

if __name__ == "__main__":
    asyncio.run(fix_menu())


