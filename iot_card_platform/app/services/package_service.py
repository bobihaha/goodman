"""
套餐业务服务
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.package_crud import supplier_package_crud, sale_package_crud
from app.crud.supplier_crud import supplier_crud
from app.schemas.package import (
    SupplierPackageCreate, SupplierPackageUpdate, SupplierPackageQuery,
    SalePackageCreate, SalePackageUpdate, SalePackageQuery
)
from app.schemas.auth import CurrentUser
from app.db.models.sys_user import UserLevel
from app.utils.exceptions import BusinessException


class SupplierPackageService:
    """底层套餐服务"""

    async def create_package(self, db: AsyncSession, data: SupplierPackageCreate, created_by: int) -> Dict[str, Any]:
        """创建底层套餐"""
        # 检查供应商是否存在
        supplier = await supplier_crud.get_by_id(db, data.supplier_id)
        if not supplier:
            raise BusinessException(code=400, msg="供应商不存在")

        # 检查编码是否已存在
        existing = await supplier_package_crud.get_by_code(db, data.code)
        if existing:
            raise BusinessException(code=400, msg=f"套餐编码 {data.code} 已存在")

        package = await supplier_package_crud.create(db, data, created_by)
        result = package.to_dict()
        result['supplier_name'] = supplier.name
        return result

    async def get_package(self, db: AsyncSession, package_id: int) -> Dict[str, Any]:
        """获取套餐详情"""
        package = await supplier_package_crud.get_by_id(db, package_id)
        if not package:
            raise BusinessException(code=404, msg="套餐不存在")

        result = package.to_dict()
        # 获取供应商信息
        supplier = await supplier_crud.get_by_id(db, package.supplier_id)
        result['supplier_name'] = supplier.name if supplier else None
        return result

    async def get_package_list(self, db: AsyncSession, query: SupplierPackageQuery) -> Dict[str, Any]:
        """获取套餐列表"""
        packages, total = await supplier_package_crud.get_list(db, query)

        # 获取供应商名称映射
        supplier_ids = list(set([p.supplier_id for p in packages]))
        supplier_map = {}
        for sid in supplier_ids:
            supplier = await supplier_crud.get_by_id(db, sid)
            if supplier:
                supplier_map[sid] = supplier.name

        result_list = []
        for p in packages:
            item = p.to_dict()
            item['supplier_name'] = supplier_map.get(p.supplier_id)
            result_list.append(item)

        return {
            "list": result_list,
            "total": total,
            "page": query.page,
            "page_size": query.page_size
        }

    async def get_by_supplier(self, db: AsyncSession, supplier_id: int) -> List[Dict[str, Any]]:
        """获取供应商的所有套餐(用于下拉选择)"""
        packages = await supplier_package_crud.get_by_supplier(db, supplier_id)
        return [{"id": p.id, "name": p.name, "code": p.code, "flow_size": p.flow_size, "price_cost": float(p.price_cost)} for p in packages]

    async def update_package(self, db: AsyncSession, package_id: int, data: SupplierPackageUpdate) -> Dict[str, Any]:
        """更新套餐"""
        package = await supplier_package_crud.get_by_id(db, package_id)
        if not package:
            raise BusinessException(code=404, msg="套餐不存在")

        package = await supplier_package_crud.update(db, package_id, data)

        result = package.to_dict()
        supplier = await supplier_crud.get_by_id(db, package.supplier_id)
        result['supplier_name'] = supplier.name if supplier else None
        return result

    async def delete_package(self, db: AsyncSession, package_id: int) -> bool:
        """删除套餐"""
        package = await supplier_package_crud.get_by_id(db, package_id)
        if not package:
            raise BusinessException(code=404, msg="套餐不存在")

        # TODO: 检查是否有关联的销售套餐或卡片

        return await supplier_package_crud.delete(db, package_id)


class SalePackageService:
    """销售套餐服务"""

    async def create_package(self, db: AsyncSession, data: SalePackageCreate, current_user: CurrentUser) -> Dict[str, Any]:
        """创建销售套餐"""
        # 检查编码是否已存在
        existing = await sale_package_crud.get_by_code(db, data.code)
        if existing:
            raise BusinessException(code=400, msg=f"套餐编码 {data.code} 已存在")

        # 如果关联了底层套餐，验证其存在
        base_package_name = None
        if data.base_package_id:
            base_package = await supplier_package_crud.get_by_id(db, data.base_package_id)
            if not base_package:
                raise BusinessException(code=400, msg="关联的底层套餐不存在")
            base_package_name = base_package.name

        # 超级管理员创建的是平台套餐 (user_id=None)
        # 普通用户创建的是自己的套餐
        user_id = None if current_user.user_level == UserLevel.SUPER_ADMIN.value else current_user.id

        package = await sale_package_crud.create(db, data, user_id, current_user.id)
        result = package.to_dict()
        result['base_package_name'] = base_package_name
        return result

    async def get_package(self, db: AsyncSession, package_id: int, current_user: CurrentUser) -> Dict[str, Any]:
        """获取套餐详情"""
        package = await sale_package_crud.get_by_id(db, package_id)
        if not package:
            raise BusinessException(code=404, msg="套餐不存在")

        # 权限检查：只能查看自己的套餐或平台公开套餐
        if current_user.user_level != UserLevel.SUPER_ADMIN.value:
            if package.user_id and package.user_id != current_user.id:
                raise BusinessException(code=403, msg="无权查看此套餐")

        result = package.to_dict()
        # 获取底层套餐名称
        if package.base_package_id:
            base_package = await supplier_package_crud.get_by_id(db, package.base_package_id)
            result['base_package_name'] = base_package.name if base_package else None
        return result

    async def get_package_list(self, db: AsyncSession, query: SalePackageQuery, current_user: CurrentUser) -> Dict[str, Any]:
        """获取套餐列表"""
        # 超级管理员可以查看所有套餐，其他用户只能看自己的和公开的
        user_id = None if current_user.user_level == UserLevel.SUPER_ADMIN.value else current_user.id

        packages, total = await sale_package_crud.get_list(db, query, user_id)

        # 获取底层套餐名称映射
        base_package_ids = list(set([p.base_package_id for p in packages if p.base_package_id]))
        base_package_map = {}
        for bid in base_package_ids:
            base_package = await supplier_package_crud.get_by_id(db, bid)
            if base_package:
                base_package_map[bid] = base_package.name

        result_list = []
        for p in packages:
            item = p.to_dict()
            item['base_package_name'] = base_package_map.get(p.base_package_id) if p.base_package_id else None
            result_list.append(item)

        return {
            "list": result_list,
            "total": total,
            "page": query.page,
            "page_size": query.page_size
        }

    async def get_user_packages(self, db: AsyncSession, user_id: int) -> List[Dict[str, Any]]:
        """获取用户可用的套餐(用于下拉选择)"""
        packages = await sale_package_crud.get_user_packages(db, user_id)
        return [{
            "id": p.id, "name": p.name, "code": p.code, 
            "flow_size": p.flow_size, "price_sale": float(p.price_sale),
            "carrier": p.carrier.value if p.carrier else None
        } for p in packages]

    async def update_package(self, db: AsyncSession, package_id: int, data: SalePackageUpdate, current_user: CurrentUser) -> Dict[str, Any]:
        """更新套餐"""
        package = await sale_package_crud.get_by_id(db, package_id)
        if not package:
            raise BusinessException(code=404, msg="套餐不存在")

        # 权限检查
        if current_user.user_level != UserLevel.SUPER_ADMIN.value:
            if package.user_id != current_user.id:
                raise BusinessException(code=403, msg="无权修改此套餐")

        # 如果更新了底层套餐关联，验证其存在
        if data.base_package_id:
            base_package = await supplier_package_crud.get_by_id(db, data.base_package_id)
            if not base_package:
                raise BusinessException(code=400, msg="关联的底层套餐不存在")

        package = await sale_package_crud.update(db, package_id, data)

        result = package.to_dict()
        if package.base_package_id:
            base_package = await supplier_package_crud.get_by_id(db, package.base_package_id)
            result['base_package_name'] = base_package.name if base_package else None
        return result

    async def delete_package(self, db: AsyncSession, package_id: int, current_user: CurrentUser) -> bool:
        """删除套餐"""
        package = await sale_package_crud.get_by_id(db, package_id)
        if not package:
            raise BusinessException(code=404, msg="套餐不存在")

        # 权限检查
        if current_user.user_level != UserLevel.SUPER_ADMIN.value:
            if package.user_id != current_user.id:
                raise BusinessException(code=403, msg="无权删除此套餐")

        # TODO: 检查是否有关联的卡片

        return await sale_package_crud.delete(db, package_id)


supplier_package_service = SupplierPackageService()
sale_package_service = SalePackageService()
