#!/bin/bash

# 权限管理系统快速测试脚本

echo "=========================================="
echo "  物联网卡管理平台 - 权限管理系统测试"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_DIR="/Users/huiren/Documents/goodman/iot_card_platform"

# 1. 检查后端服务
echo -e "${YELLOW}[1/5] 检查后端服务...${NC}"
if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 后端服务运行中 (http://localhost:8000)${NC}"
else
    echo -e "${RED}✗ 后端服务未运行${NC}"
    echo "请先启动后端服务："
    echo "  cd $PROJECT_DIR"
    echo "  source venv/bin/activate"
    echo "  python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
    exit 1
fi

# 2. 检查前端服务
echo -e "${YELLOW}[2/5] 检查前端服务...${NC}"
if lsof -i :3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 前端服务运行中 (http://localhost:3000)${NC}"
elif lsof -i :5173 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 前端服务运行中 (http://localhost:5173)${NC}"
else
    echo -e "${RED}✗ 前端服务未运行${NC}"
    echo "请先启动前端服务："
    echo "  cd $PROJECT_DIR/frontend"
    echo "  npm run dev"
    exit 1
fi

# 3. 检查数据库连接（可选）
echo -e "${YELLOW}[3/5] 检查数据库连接...${NC}"
echo -e "${GREEN}✓ 跳过数据库检查（需要手动验证）${NC}"

# 4. 检查权限表（可选）
echo -e "${YELLOW}[4/5] 检查权限表...${NC}"
echo -e "${GREEN}✓ 跳过权限表检查（需要手动验证）${NC}"

# 5. 测试权限API
echo -e "${YELLOW}[5/5] 测试权限API...${NC}"
API_RESPONSE=$(curl -s http://localhost:8000/api/v1/permissions/modules)
if echo "$API_RESPONSE" | grep -q "code"; then
    echo -e "${GREEN}✓ 权限API响应正常${NC}"
else
    echo -e "${RED}✗ 权限API响应异常${NC}"
    echo "响应内容: $API_RESPONSE"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}✓ 所有检查完成！${NC}"
echo "=========================================="
echo ""
echo "访问地址："
echo "  前端: http://localhost:3000"
echo "  后端API文档: http://localhost:8000/docs"
echo ""
echo "测试步骤："
echo "  1. 访问前端页面并登录"
echo "  2. 进入 系统设置 > 权限管理"
echo "  3. 测试权限CRUD功能"
echo "  4. 进入 客户管理"
echo "  5. 点击用户的 分配权限 按钮"
echo "  6. 测试权限分配功能"
echo ""
echo "详细测试指南："
echo "  $PROJECT_DIR/PERMISSION_TESTING_GUIDE.md"
echo ""

