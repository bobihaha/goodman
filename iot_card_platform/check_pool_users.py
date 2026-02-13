"""
检查流量池和用户关系
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text

async def check_pools_and_users():
    engine = create_async_engine(
        "mysql+aiomysql://root:2026huihui$$@localhost:3306/iot_card_platform",
        echo=False
    )
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        print("=" * 80)
        print("流量池和用户关系检查")
        print("=" * 80)
        
        # 查询所有流量池
        result = await session.execute(text("""
            SELECT 
                id,
                name,
                user_id,
                carrier,
                flow_size,
                period_type,
                card_count,
                status
            FROM traffic_pools
            WHERE is_deleted = 0
            ORDER BY id
        """))
        
        pools = result.fetchall()
        
        print(f"\n共有 {len(pools)} 个流量池：\n")
        
        for pool in pools:
            print(f"流量池 ID: {pool.id}")
            print(f"  名称: {pool.name}")
            print(f"  用户ID: {pool.user_id if pool.user_id else '平台级'}")
            print(f"  运营商: {pool.carrier}")
            print(f"  流量: {pool.flow_size}MB")
            print(f"  周期: {pool.period_type}")
            print(f"  卡片数: {pool.card_count}")
            print(f"  状态: {pool.status}")
            print()
        
        print("=" * 80)
        print("用户列表")
        print("=" * 80)
        
        # 查询所有用户
        result2 = await session.execute(text("""
            SELECT id, username, real_name, user_level, status
            FROM sys_users
            WHERE is_deleted = 0
            ORDER BY id
        """))
        
        users = result2.fetchall()
        
        print(f"\n共有 {len(users)} 个用户：\n")
        
        for user in users:
            print(f"用户 ID: {user.id}")
            print(f"  用户名: {user.username}")
            print(f"  真实姓名: {user.real_name}")
            print(f"  级别: {user.user_level}")
            print(f"  状态: {user.status}")
            
            # 查询该用户的流量池数量
            result3 = await session.execute(text("""
                SELECT COUNT(*) as count
                FROM traffic_pools
                WHERE user_id = :user_id AND is_deleted = 0
            """), {"user_id": user.id})
            pool_count = result3.scalar()
            
            print(f"  流量池数量: {pool_count}")
            print()
        
        print("=" * 80)
        print("建议")
        print("=" * 80)
        print("\n如果前端看不到流量池，请检查：")
        print("1. 是否使用正确的用户登录（user_id=2）")
        print("2. 前端API是否正确传递了用户ID")
        print("3. 后端API是否正确过滤了用户的流量池")
        print()

if __name__ == "__main__":
    asyncio.run(check_pools_and_users())


"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text

async def check_pools_and_users():
    engine = create_async_engine(
        "mysql+aiomysql://root:2026huihui$$@localhost:3306/iot_card_platform",
        echo=False
    )
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        print("=" * 80)
        print("流量池和用户关系检查")
        print("=" * 80)
        
        # 查询所有流量池
        result = await session.execute(text("""
            SELECT 
                id,
                name,
                user_id,
                carrier,
                flow_size,
                period_type,
                card_count,
                status
            FROM traffic_pools
            WHERE is_deleted = 0
            ORDER BY id
        """))
        
        pools = result.fetchall()
        
        print(f"\n共有 {len(pools)} 个流量池：\n")
        
        for pool in pools:
            print(f"流量池 ID: {pool.id}")
            print(f"  名称: {pool.name}")
            print(f"  用户ID: {pool.user_id if pool.user_id else '平台级'}")
            print(f"  运营商: {pool.carrier}")
            print(f"  流量: {pool.flow_size}MB")
            print(f"  周期: {pool.period_type}")
            print(f"  卡片数: {pool.card_count}")
            print(f"  状态: {pool.status}")
            print()
        
        print("=" * 80)
        print("用户列表")
        print("=" * 80)
        
        # 查询所有用户
        result2 = await session.execute(text("""
            SELECT id, username, real_name, user_level, status
            FROM sys_users
            WHERE is_deleted = 0
            ORDER BY id
        """))
        
        users = result2.fetchall()
        
        print(f"\n共有 {len(users)} 个用户：\n")
        
        for user in users:
            print(f"用户 ID: {user.id}")
            print(f"  用户名: {user.username}")
            print(f"  真实姓名: {user.real_name}")
            print(f"  级别: {user.user_level}")
            print(f"  状态: {user.status}")
            
            # 查询该用户的流量池数量
            result3 = await session.execute(text("""
                SELECT COUNT(*) as count
                FROM traffic_pools
                WHERE user_id = :user_id AND is_deleted = 0
            """), {"user_id": user.id})
            pool_count = result3.scalar()
            
            print(f"  流量池数量: {pool_count}")
            print()
        
        print("=" * 80)
        print("建议")
        print("=" * 80)
        print("\n如果前端看不到流量池，请检查：")
        print("1. 是否使用正确的用户登录（user_id=2）")
        print("2. 前端API是否正确传递了用户ID")
        print("3. 后端API是否正确过滤了用户的流量池")
        print()

if __name__ == "__main__":
    asyncio.run(check_pools_and_users())


"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text

async def check_pools_and_users():
    engine = create_async_engine(
        "mysql+aiomysql://root:2026huihui$$@localhost:3306/iot_card_platform",
        echo=False
    )
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        print("=" * 80)
        print("流量池和用户关系检查")
        print("=" * 80)
        
        # 查询所有流量池
        result = await session.execute(text("""
            SELECT 
                id,
                name,
                user_id,
                carrier,
                flow_size,
                period_type,
                card_count,
                status
            FROM traffic_pools
            WHERE is_deleted = 0
            ORDER BY id
        """))
        
        pools = result.fetchall()
        
        print(f"\n共有 {len(pools)} 个流量池：\n")
        
        for pool in pools:
            print(f"流量池 ID: {pool.id}")
            print(f"  名称: {pool.name}")
            print(f"  用户ID: {pool.user_id if pool.user_id else '平台级'}")
            print(f"  运营商: {pool.carrier}")
            print(f"  流量: {pool.flow_size}MB")
            print(f"  周期: {pool.period_type}")
            print(f"  卡片数: {pool.card_count}")
            print(f"  状态: {pool.status}")
            print()
        
        print("=" * 80)
        print("用户列表")
        print("=" * 80)
        
        # 查询所有用户
        result2 = await session.execute(text("""
            SELECT id, username, real_name, user_level, status
            FROM sys_users
            WHERE is_deleted = 0
            ORDER BY id
        """))
        
        users = result2.fetchall()
        
        print(f"\n共有 {len(users)} 个用户：\n")
        
        for user in users:
            print(f"用户 ID: {user.id}")
            print(f"  用户名: {user.username}")
            print(f"  真实姓名: {user.real_name}")
            print(f"  级别: {user.user_level}")
            print(f"  状态: {user.status}")
            
            # 查询该用户的流量池数量
            result3 = await session.execute(text("""
                SELECT COUNT(*) as count
                FROM traffic_pools
                WHERE user_id = :user_id AND is_deleted = 0
            """), {"user_id": user.id})
            pool_count = result3.scalar()
            
            print(f"  流量池数量: {pool_count}")
            print()
        
        print("=" * 80)
        print("建议")
        print("=" * 80)
        print("\n如果前端看不到流量池，请检查：")
        print("1. 是否使用正确的用户登录（user_id=2）")
        print("2. 前端API是否正确传递了用户ID")
        print("3. 后端API是否正确过滤了用户的流量池")
        print()

if __name__ == "__main__":
    asyncio.run(check_pools_and_users())


"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text

async def check_pools_and_users():
    engine = create_async_engine(
        "mysql+aiomysql://root:2026huihui$$@localhost:3306/iot_card_platform",
        echo=False
    )
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        print("=" * 80)
        print("流量池和用户关系检查")
        print("=" * 80)
        
        # 查询所有流量池
        result = await session.execute(text("""
            SELECT 
                id,
                name,
                user_id,
                carrier,
                flow_size,
                period_type,
                card_count,
                status
            FROM traffic_pools
            WHERE is_deleted = 0
            ORDER BY id
        """))
        
        pools = result.fetchall()
        
        print(f"\n共有 {len(pools)} 个流量池：\n")
        
        for pool in pools:
            print(f"流量池 ID: {pool.id}")
            print(f"  名称: {pool.name}")
            print(f"  用户ID: {pool.user_id if pool.user_id else '平台级'}")
            print(f"  运营商: {pool.carrier}")
            print(f"  流量: {pool.flow_size}MB")
            print(f"  周期: {pool.period_type}")
            print(f"  卡片数: {pool.card_count}")
            print(f"  状态: {pool.status}")
            print()
        
        print("=" * 80)
        print("用户列表")
        print("=" * 80)
        
        # 查询所有用户
        result2 = await session.execute(text("""
            SELECT id, username, real_name, user_level, status
            FROM sys_users
            WHERE is_deleted = 0
            ORDER BY id
        """))
        
        users = result2.fetchall()
        
        print(f"\n共有 {len(users)} 个用户：\n")
        
        for user in users:
            print(f"用户 ID: {user.id}")
            print(f"  用户名: {user.username}")
            print(f"  真实姓名: {user.real_name}")
            print(f"  级别: {user.user_level}")
            print(f"  状态: {user.status}")
            
            # 查询该用户的流量池数量
            result3 = await session.execute(text("""
                SELECT COUNT(*) as count
                FROM traffic_pools
                WHERE user_id = :user_id AND is_deleted = 0
            """), {"user_id": user.id})
            pool_count = result3.scalar()
            
            print(f"  流量池数量: {pool_count}")
            print()
        
        print("=" * 80)
        print("建议")
        print("=" * 80)
        print("\n如果前端看不到流量池，请检查：")
        print("1. 是否使用正确的用户登录（user_id=2）")
        print("2. 前端API是否正确传递了用户ID")
        print("3. 后端API是否正确过滤了用户的流量池")
        print()

if __name__ == "__main__":
    asyncio.run(check_pools_and_users())

