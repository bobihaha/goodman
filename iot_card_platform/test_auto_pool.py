"""
测试自动组池功能
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.db.models.iot_card import IotCardModel, CardType, CardStatus
from app.db.models.pool import TrafficPoolModel
from app.crud.pool_crud import pool_crud

async def test_auto_pool():
    # 创建数据库连接
    engine = create_async_engine(
        "mysql+aiomysql://root:2026huihui$$@localhost:3306/iot_card_platform",
        echo=True
    )
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        print("=" * 60)
        print("1. 检查流量池卡数量")
        print("=" * 60)
        
        # 查询流量池卡
        query = select(IotCardModel).where(
            IotCardModel.card_type == CardType.pool,
            IotCardModel.is_deleted == 0
        )
        result = await session.execute(query)
        pool_cards = result.scalars().all()
        
        print(f"流量池卡总数: {len(pool_cards)}")
        
        # 按状态统计
        status_count = {}
        for card in pool_cards:
            status = card.status.value
            status_count[status] = status_count.get(status, 0) + 1
        
        print("\n按状态统计:")
        for status, count in status_count.items():
            print(f"  {status}: {count}")
        
        # 查询已激活的流量池卡
        activated_cards = [c for c in pool_cards if c.status == CardStatus.activated]
        print(f"\n已激活的流量池卡: {len(activated_cards)}")
        
        if activated_cards:
            print("\n已激活流量池卡详情:")
            for card in activated_cards[:5]:  # 只显示前5张
                print(f"  ICCID: {card.iccid}")
                print(f"    用户ID: {card.user_id}")
                print(f"    流量池ID: {card.pool_id}")
                print(f"    运营商: {card.carrier.value}")
                print(f"    流量: {card.flow_size}MB")
                print(f"    周期: {card.period_type.value}")
                print()
        
        print("=" * 60)
        print("2. 检查流量池数量")
        print("=" * 60)
        
        # 查询流量池
        query2 = select(TrafficPoolModel).where(
            TrafficPoolModel.is_deleted == 0
        )
        result2 = await session.execute(query2)
        pools = result2.scalars().all()
        
        print(f"流量池总数: {len(pools)}")
        
        if pools:
            print("\n流量池列表:")
            for pool in pools:
                print(f"  ID: {pool.id}")
                print(f"    名称: {pool.name}")
                print(f"    用户ID: {pool.user_id}")
                print(f"    运营商: {pool.carrier.value}")
                print(f"    流量: {pool.flow_size}MB")
                print(f"    周期: {pool.period_type.value}")
                print(f"    卡片数: {pool.card_count}")
                print(f"    状态: {pool.status.value}")
                print()
        
        print("=" * 60)
        print("3. 测试 find_or_create_pool 方法")
        print("=" * 60)
        
        if activated_cards:
            test_card = activated_cards[0]
            print(f"使用测试卡片: {test_card.iccid}")
            print(f"  用户ID: {test_card.user_id}")
            print(f"  运营商: {test_card.carrier.value}")
            print(f"  流量: {test_card.flow_size}MB")
            print(f"  周期: {test_card.period_type.value}")
            
            try:
                pool = await pool_crud.find_or_create_pool(
                    db=session,
                    user_id=test_card.user_id,
                    carrier=test_card.carrier.value,
                    flow_size=test_card.flow_size,
                    period_type=test_card.period_type.value,
                    created_by=test_card.user_id
                )
                
                print(f"\n✅ 成功找到或创建流量池:")
                print(f"  ID: {pool.id}")
                print(f"  名称: {pool.name}")
                print(f"  卡片数: {pool.card_count}")
                
                await session.commit()
                
            except Exception as e:
                print(f"\n❌ 测试失败: {str(e)}")
                import traceback
                traceback.print_exc()
        else:
            print("没有已激活的流量池卡，无法测试")
        
        print("=" * 60)
        print("4. 建议")
        print("=" * 60)
        
        if len(activated_cards) == 0:
            print("⚠️  没有已激活的流量池卡")
            print("   建议：")
            print("   1. 出库时选择卡类型为'流量池卡'")
            print("   2. 通过同步功能激活卡片")
            print("   3. 激活后会自动创建流量池并加入")
        elif len(pools) == 0:
            print("⚠️  有已激活的流量池卡，但没有流量池")
            print("   可能原因：")
            print("   1. 卡片激活时自动组池功能未触发")
            print("   2. 代码逻辑有问题")
            print("   建议：手动触发同步，或检查后端日志")
        else:
            print("✅ 系统正常，已有流量池")

if __name__ == "__main__":
    asyncio.run(test_auto_pool())


"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.db.models.iot_card import IotCardModel, CardType, CardStatus
from app.db.models.pool import TrafficPoolModel
from app.crud.pool_crud import pool_crud

async def test_auto_pool():
    # 创建数据库连接
    engine = create_async_engine(
        "mysql+aiomysql://root:2026huihui$$@localhost:3306/iot_card_platform",
        echo=True
    )
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        print("=" * 60)
        print("1. 检查流量池卡数量")
        print("=" * 60)
        
        # 查询流量池卡
        query = select(IotCardModel).where(
            IotCardModel.card_type == CardType.pool,
            IotCardModel.is_deleted == 0
        )
        result = await session.execute(query)
        pool_cards = result.scalars().all()
        
        print(f"流量池卡总数: {len(pool_cards)}")
        
        # 按状态统计
        status_count = {}
        for card in pool_cards:
            status = card.status.value
            status_count[status] = status_count.get(status, 0) + 1
        
        print("\n按状态统计:")
        for status, count in status_count.items():
            print(f"  {status}: {count}")
        
        # 查询已激活的流量池卡
        activated_cards = [c for c in pool_cards if c.status == CardStatus.activated]
        print(f"\n已激活的流量池卡: {len(activated_cards)}")
        
        if activated_cards:
            print("\n已激活流量池卡详情:")
            for card in activated_cards[:5]:  # 只显示前5张
                print(f"  ICCID: {card.iccid}")
                print(f"    用户ID: {card.user_id}")
                print(f"    流量池ID: {card.pool_id}")
                print(f"    运营商: {card.carrier.value}")
                print(f"    流量: {card.flow_size}MB")
                print(f"    周期: {card.period_type.value}")
                print()
        
        print("=" * 60)
        print("2. 检查流量池数量")
        print("=" * 60)
        
        # 查询流量池
        query2 = select(TrafficPoolModel).where(
            TrafficPoolModel.is_deleted == 0
        )
        result2 = await session.execute(query2)
        pools = result2.scalars().all()
        
        print(f"流量池总数: {len(pools)}")
        
        if pools:
            print("\n流量池列表:")
            for pool in pools:
                print(f"  ID: {pool.id}")
                print(f"    名称: {pool.name}")
                print(f"    用户ID: {pool.user_id}")
                print(f"    运营商: {pool.carrier.value}")
                print(f"    流量: {pool.flow_size}MB")
                print(f"    周期: {pool.period_type.value}")
                print(f"    卡片数: {pool.card_count}")
                print(f"    状态: {pool.status.value}")
                print()
        
        print("=" * 60)
        print("3. 测试 find_or_create_pool 方法")
        print("=" * 60)
        
        if activated_cards:
            test_card = activated_cards[0]
            print(f"使用测试卡片: {test_card.iccid}")
            print(f"  用户ID: {test_card.user_id}")
            print(f"  运营商: {test_card.carrier.value}")
            print(f"  流量: {test_card.flow_size}MB")
            print(f"  周期: {test_card.period_type.value}")
            
            try:
                pool = await pool_crud.find_or_create_pool(
                    db=session,
                    user_id=test_card.user_id,
                    carrier=test_card.carrier.value,
                    flow_size=test_card.flow_size,
                    period_type=test_card.period_type.value,
                    created_by=test_card.user_id
                )
                
                print(f"\n✅ 成功找到或创建流量池:")
                print(f"  ID: {pool.id}")
                print(f"  名称: {pool.name}")
                print(f"  卡片数: {pool.card_count}")
                
                await session.commit()
                
            except Exception as e:
                print(f"\n❌ 测试失败: {str(e)}")
                import traceback
                traceback.print_exc()
        else:
            print("没有已激活的流量池卡，无法测试")
        
        print("=" * 60)
        print("4. 建议")
        print("=" * 60)
        
        if len(activated_cards) == 0:
            print("⚠️  没有已激活的流量池卡")
            print("   建议：")
            print("   1. 出库时选择卡类型为'流量池卡'")
            print("   2. 通过同步功能激活卡片")
            print("   3. 激活后会自动创建流量池并加入")
        elif len(pools) == 0:
            print("⚠️  有已激活的流量池卡，但没有流量池")
            print("   可能原因：")
            print("   1. 卡片激活时自动组池功能未触发")
            print("   2. 代码逻辑有问题")
            print("   建议：手动触发同步，或检查后端日志")
        else:
            print("✅ 系统正常，已有流量池")

if __name__ == "__main__":
    asyncio.run(test_auto_pool())


"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.db.models.iot_card import IotCardModel, CardType, CardStatus
from app.db.models.pool import TrafficPoolModel
from app.crud.pool_crud import pool_crud

async def test_auto_pool():
    # 创建数据库连接
    engine = create_async_engine(
        "mysql+aiomysql://root:2026huihui$$@localhost:3306/iot_card_platform",
        echo=True
    )
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        print("=" * 60)
        print("1. 检查流量池卡数量")
        print("=" * 60)
        
        # 查询流量池卡
        query = select(IotCardModel).where(
            IotCardModel.card_type == CardType.pool,
            IotCardModel.is_deleted == 0
        )
        result = await session.execute(query)
        pool_cards = result.scalars().all()
        
        print(f"流量池卡总数: {len(pool_cards)}")
        
        # 按状态统计
        status_count = {}
        for card in pool_cards:
            status = card.status.value
            status_count[status] = status_count.get(status, 0) + 1
        
        print("\n按状态统计:")
        for status, count in status_count.items():
            print(f"  {status}: {count}")
        
        # 查询已激活的流量池卡
        activated_cards = [c for c in pool_cards if c.status == CardStatus.activated]
        print(f"\n已激活的流量池卡: {len(activated_cards)}")
        
        if activated_cards:
            print("\n已激活流量池卡详情:")
            for card in activated_cards[:5]:  # 只显示前5张
                print(f"  ICCID: {card.iccid}")
                print(f"    用户ID: {card.user_id}")
                print(f"    流量池ID: {card.pool_id}")
                print(f"    运营商: {card.carrier.value}")
                print(f"    流量: {card.flow_size}MB")
                print(f"    周期: {card.period_type.value}")
                print()
        
        print("=" * 60)
        print("2. 检查流量池数量")
        print("=" * 60)
        
        # 查询流量池
        query2 = select(TrafficPoolModel).where(
            TrafficPoolModel.is_deleted == 0
        )
        result2 = await session.execute(query2)
        pools = result2.scalars().all()
        
        print(f"流量池总数: {len(pools)}")
        
        if pools:
            print("\n流量池列表:")
            for pool in pools:
                print(f"  ID: {pool.id}")
                print(f"    名称: {pool.name}")
                print(f"    用户ID: {pool.user_id}")
                print(f"    运营商: {pool.carrier.value}")
                print(f"    流量: {pool.flow_size}MB")
                print(f"    周期: {pool.period_type.value}")
                print(f"    卡片数: {pool.card_count}")
                print(f"    状态: {pool.status.value}")
                print()
        
        print("=" * 60)
        print("3. 测试 find_or_create_pool 方法")
        print("=" * 60)
        
        if activated_cards:
            test_card = activated_cards[0]
            print(f"使用测试卡片: {test_card.iccid}")
            print(f"  用户ID: {test_card.user_id}")
            print(f"  运营商: {test_card.carrier.value}")
            print(f"  流量: {test_card.flow_size}MB")
            print(f"  周期: {test_card.period_type.value}")
            
            try:
                pool = await pool_crud.find_or_create_pool(
                    db=session,
                    user_id=test_card.user_id,
                    carrier=test_card.carrier.value,
                    flow_size=test_card.flow_size,
                    period_type=test_card.period_type.value,
                    created_by=test_card.user_id
                )
                
                print(f"\n✅ 成功找到或创建流量池:")
                print(f"  ID: {pool.id}")
                print(f"  名称: {pool.name}")
                print(f"  卡片数: {pool.card_count}")
                
                await session.commit()
                
            except Exception as e:
                print(f"\n❌ 测试失败: {str(e)}")
                import traceback
                traceback.print_exc()
        else:
            print("没有已激活的流量池卡，无法测试")
        
        print("=" * 60)
        print("4. 建议")
        print("=" * 60)
        
        if len(activated_cards) == 0:
            print("⚠️  没有已激活的流量池卡")
            print("   建议：")
            print("   1. 出库时选择卡类型为'流量池卡'")
            print("   2. 通过同步功能激活卡片")
            print("   3. 激活后会自动创建流量池并加入")
        elif len(pools) == 0:
            print("⚠️  有已激活的流量池卡，但没有流量池")
            print("   可能原因：")
            print("   1. 卡片激活时自动组池功能未触发")
            print("   2. 代码逻辑有问题")
            print("   建议：手动触发同步，或检查后端日志")
        else:
            print("✅ 系统正常，已有流量池")

if __name__ == "__main__":
    asyncio.run(test_auto_pool())


"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.db.models.iot_card import IotCardModel, CardType, CardStatus
from app.db.models.pool import TrafficPoolModel
from app.crud.pool_crud import pool_crud

async def test_auto_pool():
    # 创建数据库连接
    engine = create_async_engine(
        "mysql+aiomysql://root:2026huihui$$@localhost:3306/iot_card_platform",
        echo=True
    )
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        print("=" * 60)
        print("1. 检查流量池卡数量")
        print("=" * 60)
        
        # 查询流量池卡
        query = select(IotCardModel).where(
            IotCardModel.card_type == CardType.pool,
            IotCardModel.is_deleted == 0
        )
        result = await session.execute(query)
        pool_cards = result.scalars().all()
        
        print(f"流量池卡总数: {len(pool_cards)}")
        
        # 按状态统计
        status_count = {}
        for card in pool_cards:
            status = card.status.value
            status_count[status] = status_count.get(status, 0) + 1
        
        print("\n按状态统计:")
        for status, count in status_count.items():
            print(f"  {status}: {count}")
        
        # 查询已激活的流量池卡
        activated_cards = [c for c in pool_cards if c.status == CardStatus.activated]
        print(f"\n已激活的流量池卡: {len(activated_cards)}")
        
        if activated_cards:
            print("\n已激活流量池卡详情:")
            for card in activated_cards[:5]:  # 只显示前5张
                print(f"  ICCID: {card.iccid}")
                print(f"    用户ID: {card.user_id}")
                print(f"    流量池ID: {card.pool_id}")
                print(f"    运营商: {card.carrier.value}")
                print(f"    流量: {card.flow_size}MB")
                print(f"    周期: {card.period_type.value}")
                print()
        
        print("=" * 60)
        print("2. 检查流量池数量")
        print("=" * 60)
        
        # 查询流量池
        query2 = select(TrafficPoolModel).where(
            TrafficPoolModel.is_deleted == 0
        )
        result2 = await session.execute(query2)
        pools = result2.scalars().all()
        
        print(f"流量池总数: {len(pools)}")
        
        if pools:
            print("\n流量池列表:")
            for pool in pools:
                print(f"  ID: {pool.id}")
                print(f"    名称: {pool.name}")
                print(f"    用户ID: {pool.user_id}")
                print(f"    运营商: {pool.carrier.value}")
                print(f"    流量: {pool.flow_size}MB")
                print(f"    周期: {pool.period_type.value}")
                print(f"    卡片数: {pool.card_count}")
                print(f"    状态: {pool.status.value}")
                print()
        
        print("=" * 60)
        print("3. 测试 find_or_create_pool 方法")
        print("=" * 60)
        
        if activated_cards:
            test_card = activated_cards[0]
            print(f"使用测试卡片: {test_card.iccid}")
            print(f"  用户ID: {test_card.user_id}")
            print(f"  运营商: {test_card.carrier.value}")
            print(f"  流量: {test_card.flow_size}MB")
            print(f"  周期: {test_card.period_type.value}")
            
            try:
                pool = await pool_crud.find_or_create_pool(
                    db=session,
                    user_id=test_card.user_id,
                    carrier=test_card.carrier.value,
                    flow_size=test_card.flow_size,
                    period_type=test_card.period_type.value,
                    created_by=test_card.user_id
                )
                
                print(f"\n✅ 成功找到或创建流量池:")
                print(f"  ID: {pool.id}")
                print(f"  名称: {pool.name}")
                print(f"  卡片数: {pool.card_count}")
                
                await session.commit()
                
            except Exception as e:
                print(f"\n❌ 测试失败: {str(e)}")
                import traceback
                traceback.print_exc()
        else:
            print("没有已激活的流量池卡，无法测试")
        
        print("=" * 60)
        print("4. 建议")
        print("=" * 60)
        
        if len(activated_cards) == 0:
            print("⚠️  没有已激活的流量池卡")
            print("   建议：")
            print("   1. 出库时选择卡类型为'流量池卡'")
            print("   2. 通过同步功能激活卡片")
            print("   3. 激活后会自动创建流量池并加入")
        elif len(pools) == 0:
            print("⚠️  有已激活的流量池卡，但没有流量池")
            print("   可能原因：")
            print("   1. 卡片激活时自动组池功能未触发")
            print("   2. 代码逻辑有问题")
            print("   建议：手动触发同步，或检查后端日志")
        else:
            print("✅ 系统正常，已有流量池")

if __name__ == "__main__":
    asyncio.run(test_auto_pool())

