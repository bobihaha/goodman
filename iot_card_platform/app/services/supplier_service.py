"""
供应商业务服务
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.supplier_crud import supplier_crud
from app.schemas.supplier import (
    SupplierCreate, SupplierUpdate, SupplierQuery, 
    SupplierInfo, SupplierListResponse
)
from app.utils.exceptions import BusinessException
from app.clients.supplier_api import get_supplier_client


class SupplierService:
    """供应商服务"""

    async def create_supplier(self, db: AsyncSession, data: SupplierCreate, created_by: int) -> Dict[str, Any]:
        """创建供应商"""
        # 检查编码是否已存在
        existing = await supplier_crud.get_by_code(db, data.code)
        if existing:
            raise BusinessException(code=400, msg=f"供应商编码 {data.code} 已存在")

        supplier = await supplier_crud.create(db, data, created_by)
        return supplier.to_dict()

    async def get_supplier(self, db: AsyncSession, supplier_id: int) -> Dict[str, Any]:
        """获取供应商详情"""
        supplier = await supplier_crud.get_by_id(db, supplier_id)
        if not supplier:
            raise BusinessException(code=404, msg="供应商不存在")
        return supplier.to_dict()

    async def get_supplier_list(self, db: AsyncSession, query: SupplierQuery) -> Dict[str, Any]:
        """获取供应商列表"""
        suppliers, total = await supplier_crud.get_list(db, query)
        return {
            "list": [s.to_dict() for s in suppliers],
            "total": total,
            "page": query.page,
            "page_size": query.page_size
        }

    async def get_all_suppliers(self, db: AsyncSession) -> List[Dict[str, Any]]:
        """获取所有启用的供应商(用于下拉选择)"""
        suppliers = await supplier_crud.get_all_enabled(db)
        return [{"id": s.id, "name": s.name, "code": s.code, "type": s.type.value if s.type else None} for s in suppliers]

    async def update_supplier(self, db: AsyncSession, supplier_id: int, data: SupplierUpdate) -> Dict[str, Any]:
        """更新供应商"""
        supplier = await supplier_crud.get_by_id(db, supplier_id)
        if not supplier:
            raise BusinessException(code=404, msg="供应商不存在")

        supplier = await supplier_crud.update(db, supplier_id, data)
        return supplier.to_dict()

    async def delete_supplier(self, db: AsyncSession, supplier_id: int) -> bool:
        """删除供应商"""
        supplier = await supplier_crud.get_by_id(db, supplier_id)
        if not supplier:
            raise BusinessException(code=404, msg="供应商不存在")

        package_count = await supplier_crud.count_packages(db, supplier_id)
        if package_count > 0:
            raise BusinessException(code=400, msg=f"供应商下存在 {package_count} 个套餐，请先删除套餐后再删除供应商")

        card_count = await supplier_crud.count_cards(db, supplier_id)
        if card_count > 0:
            raise BusinessException(code=400, msg=f"供应商下存在 {card_count} 张卡片，请先处理卡片后再删除供应商")

        return await supplier_crud.delete(db, supplier_id)

    async def test_api_connection(self, db: AsyncSession, supplier_id: int) -> Dict[str, Any]:
        """测试供应商 API 连通性"""
        supplier = await supplier_crud.get_by_id(db, supplier_id)
        if not supplier:
            raise BusinessException(code=404, msg="供应商不存在")

        if not supplier.api_url:
            raise BusinessException(code=400, msg="供应商未配置 API 地址")

        if not supplier.api_key or not supplier.api_secret:
            raise BusinessException(code=400, msg="供应商未配置 API Key 或 API Secret")

        client = get_supplier_client(
            supplier_id,
            supplier.api_url,
            supplier.api_key,
            supplier.api_secret,
        )

        try:
            # 用一个不存在的 ICCID 探测：网络通且签名正确时 upiot 返回业务错误码（非 200）
            # 但不会抛出 HTTP 层异常，说明连通性和认证均正常
            await client.get_card_usage("000000000000000")
            # 如果没抛异常说明连通且认证通过
            return {"success": True, "message": "API 连接测试成功", "supplier_id": supplier_id, "api_url": supplier.api_url}
        except Exception as e:
            err = str(e)
            # upiot 业务错误（签名对但卡不存在）也视为连通成功
            if "upiot GET error" in err:
                return {"success": True, "message": "API 连接测试成功（认证通过）", "supplier_id": supplier_id, "api_url": supplier.api_url}
            # 网络/认证失败
            return {"success": False, "message": f"API 连接失败: {err}", "supplier_id": supplier_id, "api_url": supplier.api_url}


supplier_service = SupplierService()
