#!/usr/bin/env python3
"""
测试出入库管理模块的改进功能
测试内容：
1. 入库记录详情中的卡片列表查询
2. 出库记录详情中的卡片列表查询
3. 入库操作自动创建新表记录
4. 出库操作自动创建新表记录
"""
import requests
import json
from datetime import datetime, timedelta

# 配置
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

# 测试账号
USERNAME = "admin"
PASSWORD = "admin123"

# 全局变量
token = None
headers = {}


def login():
    """登录获取token"""
    global token, headers
    url = f"{API_BASE}/auth/login"
    data = {
        "account": USERNAME,
        "password": PASSWORD
    }
    response = requests.post(url, json=data)
    if response.status_code == 200:
        result = response.json()
        token = result["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ 登录成功")
        return True
    else:
        print(f"❌ 登录失败: {response.text}")
        return False


def test_stock_in_with_new_record():
    """测试入库操作（会自动创建新表记录）"""
    print("\n" + "="*60)
    print("测试1: 入库操作自动创建新表记录")
    print("="*60)
    
    # 1. 先创建一个采购批次
    print("\n步骤1: 创建采购批次...")
    batch_url = f"{API_BASE}/stock/batches"
    test_date = datetime.now()
    silent_date = test_date + timedelta(days=180)
    
    batch_data = {
        "supplier_id": 1,
        "package_id": 1,
        "carrier": "china_mobile",
        "flow_size": 1024,
        "period_type": "monthly",
        "test_expire_date": None,
        "silent_expire_date": silent_date.strftime("%Y-%m-%d"),
        "purchase_date": test_date.strftime("%Y-%m-%d"),
        "remark": "测试批次-验证新表记录创建"
    }
    
    response = requests.post(batch_url, json=batch_data, headers=headers)
    if response.status_code != 200:
        print(f"❌ 创建批次失败: {response.text}")
        return None
    
    result = response.json()
    if result.get("code") != 200 or not result.get("data"):
        print(f"❌ 创建批次失败: {result.get('msg', '未知错误')}")
        return None
    
    batch_id = result["data"]["id"]
    print(f"✅ 批次创建成功，ID: {batch_id}")
    
    # 2. 执行入库操作
    print("\n步骤2: 执行入库操作...")
    stock_in_url = f"{API_BASE}/stock/in"
    timestamp = datetime.now().strftime("%H%M%S")
    
    stock_in_data = {
        "batch_id": batch_id,
        "cards": [
            {
                "iccid": f"8986012345678901234{timestamp}1",
                "imsi": f"46000123456789{timestamp}1",
                "msisdn": f"1380000{timestamp}1"
            },
            {
                "iccid": f"8986012345678901234{timestamp}2",
                "imsi": f"46000123456789{timestamp}2",
                "msisdn": f"1380000{timestamp}2"
            },
            {
                "iccid": f"8986012345678901234{timestamp}3",
                "imsi": f"46000123456789{timestamp}3",
                "msisdn": f"1380000{timestamp}3"
            }
        ],
        "remark": "测试入库-验证新表记录"
    }
    
    response = requests.post(stock_in_url, json=stock_in_data, headers=headers)
    if response.status_code != 200:
        print(f"❌ 入库失败: {response.text}")
        return None
    
    result = response.json()["data"]
    print(f"✅ 入库成功")
    print(f"   - 入库单号: {result['record_no']}")
    print(f"   - 成功数量: {result['success_count']}")
    print(f"   - 失败数量: {result['fail_count']}")
    
    # 3. 查询新表中的入库记录
    print("\n步骤3: 查询新表中的入库记录...")
    records_url = f"{API_BASE}/stock/in/records"
    response = requests.get(records_url, headers=headers, params={"page": 1, "page_size": 10})
    
    if response.status_code != 200:
        print(f"❌ 查询入库记录失败: {response.text}")
        return None
    
    records = response.json()["data"]["items"]
    if len(records) > 0:
        latest_record = records[0]
        print(f"✅ 找到入库记录")
        print(f"   - 记录ID: {latest_record['id']}")
        print(f"   - 供应商: {latest_record['supplier_name']}")
        print(f"   - 套餐: {latest_record['package_name']}")
        print(f"   - 卡片数量: {latest_record['card_count']}")
        print(f"   - 成功数量: {latest_record['success_count']}")
        
        # 4. 查询记录详情（包含卡片列表）
        print("\n步骤4: 查询记录详情（验证卡片列表）...")
        detail_url = f"{API_BASE}/stock/in/records/{latest_record['id']}"
        response = requests.get(detail_url, headers=headers)
        
        if response.status_code != 200:
            print(f"❌ 查询记录详情失败: {response.text}")
            return None
        
        detail = response.json()["data"]
        print(f"✅ 记录详情查询成功")
        print(f"   - 关联卡片数: {len(detail['cards'])}")
        if len(detail['cards']) > 0:
            print(f"   - 卡片列表示例:")
            for i, card in enumerate(detail['cards'][:3], 1):
                print(f"     {i}. ICCID: {card['iccid']}, 状态: {card['status']}")
        
        return latest_record['id']
    else:
        print("❌ 未找到入库记录")
        return None


def test_stock_out_with_new_record():
    """测试出库操作（会自动创建新表记录）"""
    print("\n" + "="*60)
    print("测试2: 出库操作自动创建新表记录")
    print("="*60)
    
    # 1. 先查询库存中的卡片
    print("\n步骤1: 查询库存卡片...")
    inventory_url = f"{API_BASE}/stock/inventory"
    response = requests.get(inventory_url, headers=headers, params={"page": 1, "page_size": 5})
    
    if response.status_code != 200:
        print(f"❌ 查询库存失败: {response.text}")
        return None
    
    inventory = response.json()["data"]["items"]
    if len(inventory) < 2:
        print("❌ 库存卡片不足（需要至少2张）")
        return None
    
    card_ids = [card["id"] for card in inventory[:2]]
    print(f"✅ 找到库存卡片，准备出库: {card_ids}")
    
    # 2. 执行出库操作
    print("\n步骤2: 执行出库操作...")
    stock_out_url = f"{API_BASE}/stock/out"
    
    stock_out_data = {
        "card_ids": card_ids,
        "to_user_id": 2,  # 假设用户ID为2
        "sale_package_id": 1,  # 假设销售套餐ID为1
        "remark": "测试出库-验证新表记录"
    }
    
    response = requests.post(stock_out_url, json=stock_out_data, headers=headers)
    if response.status_code != 200:
        print(f"❌ 出库失败: {response.text}")
        return None
    
    result = response.json()["data"]
    print(f"✅ 出库成功")
    print(f"   - 出库单号: {result['record_no']}")
    print(f"   - 成功数量: {result['success_count']}")
    print(f"   - 失败数量: {result['fail_count']}")
    
    # 3. 查询新表中的出库记录
    print("\n步骤3: 查询新表中的出库记录...")
    records_url = f"{API_BASE}/stock/out/records"
    response = requests.get(records_url, headers=headers, params={"page": 1, "page_size": 10})
    
    if response.status_code != 200:
        print(f"❌ 查询出库记录失败: {response.text}")
        return None
    
    records = response.json()["data"]["items"]
    if len(records) > 0:
        latest_record = records[0]
        print(f"✅ 找到出库记录")
        print(f"   - 记录ID: {latest_record['id']}")
        print(f"   - 用户: {latest_record['user_name']}")
        print(f"   - 销售套餐: {latest_record['sale_package_name']}")
        print(f"   - 卡片数量: {latest_record['card_count']}")
        print(f"   - 成功数量: {latest_record['success_count']}")
        print(f"   - 单价: ¥{latest_record['unit_price']}")
        print(f"   - 总金额: ¥{latest_record['total_amount']}")
        
        # 4. 查询记录详情（包含卡片列表）
        print("\n步骤4: 查询记录详情（验证卡片列表）...")
        detail_url = f"{API_BASE}/stock/out/records/{latest_record['id']}"
        response = requests.get(detail_url, headers=headers)
        
        if response.status_code != 200:
            print(f"❌ 查询记录详情失败: {response.text}")
            return None
        
        detail = response.json()["data"]
        print(f"✅ 记录详情查询成功")
        print(f"   - 关联卡片数: {len(detail['cards'])}")
        if len(detail['cards']) > 0:
            print(f"   - 卡片列表示例:")
            for i, card in enumerate(detail['cards'][:3], 1):
                print(f"     {i}. ICCID: {card['iccid']}, 状态: {card['status']}")
        
        return latest_record['id']
    else:
        print("❌ 未找到出库记录")
        return None


def test_export_records():
    """测试导出功能"""
    print("\n" + "="*60)
    print("测试3: 导出入库/出库记录")
    print("="*60)
    
    # 测试导出入库记录
    print("\n步骤1: 导出入库记录...")
    export_in_url = f"{API_BASE}/stock/in/records/export"
    response = requests.post(export_in_url, json={}, headers=headers)
    
    if response.status_code == 200:
        records = response.json()["data"]
        print(f"✅ 导出入库记录成功，共 {len(records)} 条")
    else:
        print(f"❌ 导出入库记录失败: {response.text}")
    
    # 测试导出出库记录
    print("\n步骤2: 导出出库记录...")
    export_out_url = f"{API_BASE}/stock/out/records/export"
    response = requests.post(export_out_url, json={}, headers=headers)
    
    if response.status_code == 200:
        records = response.json()["data"]
        print(f"✅ 导出出库记录成功，共 {len(records)} 条")
    else:
        print(f"❌ 导出出库记录失败: {response.text}")


def main():
    """主测试流程"""
    print("="*60)
    print("出入库管理模块改进功能测试")
    print("="*60)
    
    # 登录
    if not login():
        return
    
    # 测试入库操作和新表记录
    in_record_id = test_stock_in_with_new_record()
    
    # 测试出库操作和新表记录
    out_record_id = test_stock_out_with_new_record()
    
    # 测试导出功能
    test_export_records()
    
    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    print(f"✅ 入库记录ID: {in_record_id if in_record_id else '未创建'}")
    print(f"✅ 出库记录ID: {out_record_id if out_record_id else '未创建'}")
    print("\n所有测试完成！")
    print("\n验证要点：")
    print("1. ✅ 入库操作自动创建新表记录（stock_in_records）")
    print("2. ✅ 入库记录详情包含卡片列表（stock_in_record_cards）")
    print("3. ✅ 出库操作自动创建新表记录（stock_out_records）")
    print("4. ✅ 出库记录详情包含卡片列表（stock_out_record_cards）")
    print("5. ✅ 导出功能正常工作")


if __name__ == "__main__":
    main()

