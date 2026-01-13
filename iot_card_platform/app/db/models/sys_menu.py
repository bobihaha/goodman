"""
系统菜单模型
"""
from sqlalchemy import Column, String, Enum, BigInteger, SmallInteger, Integer
from enum import Enum as PyEnum
from app.db.models.base import BaseModel


class MenuType(str, PyEnum):
    """菜单类型枚举 - 值必须与数据库 ENUM 一致"""
    directory = "directory"
    menu = "menu"
    button = "button"


class MenuStatus(str, PyEnum):
    """菜单状态枚举 - 值必须与数据库 ENUM 一致"""
    enable = "enable"
    disable = "disable"


class SysMenuModel(BaseModel):
    __tablename__ = "sys_menus"

    parent_id = Column(BigInteger, default=0, index=True, comment="父菜单ID")
    user_level = Column(SmallInteger, default=0, comment="适用层级")
    code = Column(String(50), unique=True, nullable=False, comment="菜单编码")
    name = Column(String(50), nullable=False, comment="菜单名称")
    type = Column("type", Enum(MenuType), default=MenuType.menu, comment="类型")
    icon = Column(String(50), nullable=True, comment="图标")
    path = Column(String(255), nullable=True, comment="路由路径")
    component = Column(String(255), nullable=True, comment="组件路径")
    permission = Column(String(100), nullable=True, comment="权限标识")
    sort_order = Column(Integer, default=0, comment="排序")
    is_visible = Column(SmallInteger, default=1, comment="是否可见")
    status = Column(Enum(MenuStatus), default=MenuStatus.enable, comment="状态")


class SysUserMenuModel(BaseModel):
    __tablename__ = "sys_user_menus"

    user_id = Column(BigInteger, nullable=False, index=True, comment="用户ID")
    menu_id = Column(BigInteger, nullable=False, index=True, comment="菜单ID")
