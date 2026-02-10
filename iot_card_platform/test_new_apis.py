"""
测试新增的出入库API端点
"""
import asyncio
import httpx

BASE_URL = "http://localhost:8000/api/v1"
TOKEN = None


async def login():
    """登录获取token"""
    global TOKEN
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/auth/login",
            json={"account": "admin", "password": "admin123"}
        )
        result = response.json()
        if result["code"] == 200:
            TOKEN = result["data"]["access_token"]
            print("✅ 登录成功")
            return True
        else:
            print(f"❌ 登录失败: {result}")
            return False


async def test_in_records_list():
    """测试：获取入库记录列表"""
    print("\n" + "="*60)
    print("测试：获取入库记录列表")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/stock/in/records",
            headers={"Authorization": f"Bearer {TOKEN}"},
            params={"page": 1, "page_size": 10}
        )
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text[:500]}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"响应: {result}")
                
                if result["code"] == 200:
                    print(f"✅ 成功 - 共 {result['data']['total']} 条记录")
                    if result['data']['items']:
                        print(f"第一条记录: {result['data']['items'][0]}")
                else:
                    print(f"❌ 失败: {result['msg']}")
            except Exception as e:
                print(f"❌ 解析响应失败: {e}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")


async def test_out_records_list():
    """测试：获取出库记录列表"""
    print("\n" + "="*60)
    print("测试：获取出库记录列表")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/stock/out/records",
            headers={"Authorization": f"Bearer {TOKEN}"},
            params={"page": 1, "page_size": 10}
        )
        result = response.json()
        print(f"状态码: {response.status_code}")
        print(f"响应: {result}")
        
        if result["code"] == 200:
            print(f"✅ 成功 - 共 {result['data']['total']} 条记录")
            if result['data']['items']:
                print(f"第一条记录: {result['data']['items'][0]}")
        else:
            print(f"❌ 失败: {result['msg']}")


async def test_recycle_records_list():
    """测试：获取回收记录列表"""
    print("\n" + "="*60)
    print("测试：获取回收记录列表")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/stock/recycle/records",
            headers={"Authorization": f"Bearer {TOKEN}"},
            params={"page": 1, "page_size": 10}
        )
        result = response.json()
        print(f"状态码: {response.status_code}")
        print(f"响应: {result}")
        
        if result["code"] == 200:
            print(f"✅ 成功 - 共 {result['data']['total']} 条记录")
            if result['data']['items']:
                print(f"第一条记录: {result['data']['items'][0]}")
        else:
            print(f"❌ 失败: {result['msg']}")


async def test_export_in_records():
    """测试：导出入库记录"""
    print("\n" + "="*60)
    print("测试：导出入库记录")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/stock/in/records/export",
            headers={"Authorization": f"Bearer {TOKEN}"},
            json={}
        )
        result = response.json()
        print(f"状态码: {response.status_code}")
        
        if result["code"] == 200:
            print(f"✅ 成功 - 导出 {len(result['data'])} 条记录")
            if result['data']:
                print(f"第一条记录: {result['data'][0]}")
        else:
            print(f"❌ 失败: {result['msg']}")


async def test_export_out_records():
    """测试：导出出库记录"""
    print("\n" + "="*60)
    print("测试：导出出库记录")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/stock/out/records/export",
            headers={"Authorization": f"Bearer {TOKEN}"},
            json={}
        )
        result = response.json()
        print(f"状态码: {response.status_code}")
        
        if result["code"] == 200:
            print(f"✅ 成功 - 导出 {len(result['data'])} 条记录")
            if result['data']:
                print(f"第一条记录: {result['data'][0]}")
        else:
            print(f"❌ 失败: {result['msg']}")


async def main():
    """主测试流程"""
    print("="*60)
    print("开始测试新增的出入库API端点")
    print("="*60)
    
    # 1. 登录
    if not await login():
        return
    
    # 2. 测试入库记录相关API
    await test_in_records_list()
    await test_export_in_records()
    
    # 3. 测试出库记录相关API
    await test_out_records_list()
    await test_export_out_records()
    
    # 4. 测试回收记录API
    await test_recycle_records_list()
    
    print("\n" + "="*60)
    print("所有测试完成！")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())

