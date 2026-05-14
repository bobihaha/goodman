from app.services.sys_user_service import SysUserService


def test_default_user_menu_codes_cover_core_modules():
    assert {
        "dashboard",
        "card_manage",
        "card_list",
        "user_manage",
        "user_list",
        "renewal_manage",
        "system_manage",
    }.issubset(set(SysUserService.DEFAULT_USER_MENU_CODES))
