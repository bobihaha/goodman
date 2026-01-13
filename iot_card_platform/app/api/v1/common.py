"""
公共接口
"""
from fastapi import APIRouter
from app.schemas.common import ResponseModel

router = APIRouter()


@router.get("/health", summary="健康检查", response_model=ResponseModel)
async def health_check():
    return ResponseModel(data={
        "status": "healthy",
        "service": "iot-card-platform",
        "version": "1.0.0"
    })


@router.get("/carriers", summary="获取运营商列表", response_model=ResponseModel)
async def get_carriers():
    return ResponseModel(data=[
        {"code": "china_mobile", "name": "中国移动"},
        {"code": "china_unicom", "name": "中国联通"},
        {"code": "china_telecom", "name": "中国电信"},
    ])


@router.get("/card-status", summary="获取卡片状态列表", response_model=ResponseModel)
async def get_card_status():
    return ResponseModel(data=[
        {"code": "inactive", "name": "未激活"},
        {"code": "active", "name": "已激活"},
        {"code": "suspended", "name": "已停机"},
        {"code": "deactivated", "name": "已销户"},
        {"code": "testing", "name": "测试期"},
    ])
