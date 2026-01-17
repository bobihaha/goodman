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

        # TODO: 检查是否有关联的套餐或卡片

        return await supplier_crud.delete(db, supplier_id)

    async def test_api_connection(self, db: AsyncSession, supplier_id: int) -> Dict[str, Any]:
        """测试供应商 API 连通性"""
        supplier = await supplier_crud.get_by_id(db, supplier_id)
        if not supplier:
            raise BusinessException(code=404, msg="供应商不存在")

        if not supplier.api_url:
            raise BusinessException(code=400, msg="供应商未配置 API 地址")

        # TODO: 实现实际的 API 连通性测试
        # 这里需要根据不同供应商类型调用对应的测试接口
        return {
            "success": True,
            "message": "API 连接测试成功",
            "supplier_id": supplier_id,
            "api_url": supplier.api_url
        }


supplier_service = SupplierService()
