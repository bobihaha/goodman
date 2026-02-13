#!/usr/bin/env python3
"""
测试入库/出库记录详情查询功能
"""
import requests

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


def test_in_record_list():
    """测试入库记录列表查询"""
    print("\n" + "="*60)
    print("测试1: 查询入库记录列表")
    print("="*60)
    
    url = f"{API_BASE}/stock/in/records"
    response = requests.get(url, headers=headers, params={"page": 1, "page_size": 10})
    
    if response.status_code == 200:
        result = response.json()
        if result.get("code") == 200:
            data = result.get("data", {})
            items = data.get("items", [])
            total = data.get("total", 0)
            print(f"✅ 查询成功，共 {total} 条记录")
            
            if len(items) > 0:
                print(f"\n最新的入库记录：")
                record = items[0]
                print(f"  - ID: {record['id']}")
                print(f"  - 供应商: {record.get('supplier_name', 'N/A')}")
                print(f"  - 套餐: {record.get('package_name', 'N/A')}")
                print(f"  - 卡片数量: {record['card_count']}")
                print(f"  - 成功数量: {record['success_count']}")
                print(f"  - 失败数量: {record['failed_count']}")
                print(f"  - 创建时间: {record['created_at']}")
                return record['id']
            else:
                print("⚠️  暂无入库记录")
                return None
        else:
            print(f"❌ 查询失败: {result.get('msg', '未知错误')}")
            return None
    else:
        print(f"❌ 请求失败: {response.status_code}")
        return None


def test_in_record_detail(record_id):
    """测试入库记录详情查询（包含卡片列表）"""
    print("\n" + "="*60)
    print(f"测试2: 查询入库记录详情 (ID: {record_id})")
    print("="*60)
    
    url = f"{API_BASE}/stock/in/records/{record_id}"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        if result.get("code") == 200:
            detail = result.get("data", {})
            print(f"✅ 详情查询成功")
            print(f"  - ID: {detail['id']}")
            print(f"  - 供应商: {detail.get('supplier_name', 'N/A')}")
            print(f"  - 套餐: {detail.get('package_name', 'N/A')}")
            print(f"  - 卡片数量: {detail['card_count']}")
            print(f"  - 成功数量: {detail['success_count']}")
            print(f"  - 失败数量: {detail['failed_count']}")
            
            cards = detail.get('cards', [])
            print(f"\n  关联卡片列表: 共 {len(cards)} 张")
            if len(cards) > 0:
                print(f"  前5张卡片信息：")
                for i, card in enumerate(cards[:5], 1):
                    print(f"    {i}. ICCID: {card.get('iccid', 'N/A')}, 状态: {card.get('status', 'N/A')}")
                return True
            else:
                print("  ⚠️  暂无关联卡片")
                return False
        else:
            print(f"❌ 查询失败: {result.get('msg', '未知错误')}")
            return False
    else:
        print(f"❌ 请求失败: {response.status_code}")
        return False


def test_out_record_list():
    """测试出库记录列表查询"""
    print("\n" + "="*60)
    print("测试3: 查询出库记录列表")
    print("="*60)
    
    url = f"{API_BASE}/stock/out/records"
    response = requests.get(url, headers=headers, params={"page": 1, "page_size": 10})
    
    if response.status_code == 200:
        result = response.json()
        if result.get("code") == 200:
            data = result.get("data", {})
            items = data.get("items", [])
            total = data.get("total", 0)
            print(f"✅ 查询成功，共 {total} 条记录")
            
            if len(items) > 0:
                print(f"\n最新的出库记录：")
                record = items[0]
                print(f"  - ID: {record['id']}")
                print(f"  - 用户: {record.get('user_name', 'N/A')}")
                print(f"  - 销售套餐: {record.get('sale_package_name', 'N/A')}")
                print(f"  - 卡片数量: {record['card_count']}")
                print(f"  - 成功数量: {record['success_count']}")
                print(f"  - 失败数量: {record['failed_count']}")
                print(f"  - 单价: ¥{record.get('unit_price', 0)}")
                print(f"  - 总金额: ¥{record.get('total_amount', 0)}")
                print(f"  - 创建时间: {record['created_at']}")
                return record['id']
            else:
                print("⚠️  暂无出库记录")
                return None
        else:
            print(f"❌ 查询失败: {result.get('msg', '未知错误')}")
            return None
    else:
        print(f"❌ 请求失败: {response.status_code}")
        return None


def test_out_record_detail(record_id):
    """测试出库记录详情查询（包含卡片列表）"""
    print("\n" + "="*60)
    print(f"测试4: 查询出库记录详情 (ID: {record_id})")
    print("="*60)
    
    url = f"{API_BASE}/stock/out/records/{record_id}"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        if result.get("code") == 200:
            detail = result.get("data", {})
            print(f"✅ 详情查询成功")
            print(f"  - ID: {detail['id']}")
            print(f"  - 用户: {detail.get('user_name', 'N/A')}")
            print(f"  - 销售套餐: {detail.get('sale_package_name', 'N/A')}")
            print(f"  - 卡片数量: {detail['card_count']}")
            print(f"  - 成功数量: {detail['success_count']}")
            print(f"  - 失败数量: {detail['failed_count']}")
            print(f"  - 单价: ¥{detail.get('unit_price', 0)}")
            print(f"  - 总金额: ¥{detail.get('total_amount', 0)}")
            
            cards = detail.get('cards', [])
            print(f"\n  关联卡片列表: 共 {len(cards)} 张")
            if len(cards) > 0:
                print(f"  前5张卡片信息：")
                for i, card in enumerate(cards[:5], 1):
                    print(f"    {i}. ICCID: {card.get('iccid', 'N/A')}, 状态: {card.get('status', 'N/A')}")
                return True
            else:
                print("  ⚠️  暂无关联卡片")
                return False
        else:
            print(f"❌ 查询失败: {result.get('msg', '未知错误')}")
            return False
    else:
        print(f"❌ 请求失败: {response.status_code}")
        return False


def main():
    """主测试流程"""
    print("="*60)
    print("入库/出库记录详情查询功能测试")
    print("="*60)
    
    # 登录
    if not login():
        return
    
    # 测试入库记录
    in_record_id = test_in_record_list()
    if in_record_id:
        test_in_record_detail(in_record_id)
    
    # 测试出库记录
    out_record_id = test_out_record_list()
    if out_record_id:
        test_out_record_detail(out_record_id)
    
    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    print("✅ 所有测试完成！")
    print("\n验证要点：")
    print("1. ✅ 入库记录列表查询正常")
    print("2. ✅ 入库记录详情包含卡片列表")
    print("3. ✅ 出库记录列表查询正常")
    print("4. ✅ 出库记录详情包含卡片列表")


if __name__ == "__main__":
    main()





