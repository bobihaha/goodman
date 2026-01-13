"""
CRUD 操作模块
"""
from app.crud.base import CRUDBase
from app.crud.sys_user_crud import sys_user_crud
from app.crud.sys_menu_crud import sys_menu_crud, sys_user_menu_crud

__all__ = ["CRUDBase", "sys_user_crud", "sys_menu_crud", "sys_user_menu_crud"]
