import pymysql

conn = pymysql.connect(
    host='localhost',
    user='root',
    password='Aa112211',
    database='iot_card_platform'
)

cursor = conn.cursor()

# 查询卡片统计
print("=== 卡片统计 ===")
cursor.execute("""
    SELECT 
        card_type,
        status,
        COUNT(*) as count
    FROM iot_cards
    WHERE is_deleted = 0
    GROUP BY card_type, status
""")
for row in cursor.fetchall():
    print(f"类型: {row[0]}, 状态: {row[1]}, 数量: {row[2]}")

# 查询已激活的流量池卡
print("\n=== 已激活的流量池卡 ===")
cursor.execute("""
    SELECT iccid, user_id, pool_id, carrier, flow_size, period_type
    FROM iot_cards
    WHERE card_type = 'pool' 
    AND status = 'activated'
    AND is_deleted = 0
    LIMIT 5
""")
for row in cursor.fetchall():
    print(f"ICCID: {row[0]}, 用户ID: {row[1]}, 流量池ID: {row[2]}, 运营商: {row[3]}, 流量: {row[4]}MB, 周期: {row[5]}")

# 查询流量池
print("\n=== 流量池列表 ===")
cursor.execute("""
    SELECT id, name, user_id, carrier, flow_size, period_type, card_count, status
    FROM traffic_pools
    WHERE is_deleted = 0
""")
pools = cursor.fetchall()
print(f"流量池总数: {len(pools)}")
for row in pools:
    print(f"ID: {row[0]}, 名称: {row[1]}, 用户ID: {row[2]}, 运营商: {row[3]}, 流量: {row[4]}MB, 周期: {row[5]}, 卡片数: {row[6]}, 状态: {row[7]}")

cursor.close()
conn.close()
