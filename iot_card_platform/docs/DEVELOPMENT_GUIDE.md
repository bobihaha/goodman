# 开发指南

## 命名规范

- **组件**：PascalCase (`UserList.vue`)
- **文件**：kebab-case (`user-list.ts`)
- **变量/函数**：camelCase (`getUserList`)
- **常量**：UPPER_SNAKE_CASE (`API_BASE_URL`)
- **CSS类**：BEM (`card__header--active`)

---

## 代码规范

### TypeScript
- 使用严格模式
- 禁止使用 `any`
- 明确类型定义
- 组件使用 Composition API + `<script setup>`

### 前端
- 使用 ESLint + Prettier
- 避免深层嵌套（>4层）
- 函数保持简短（<50行）
- 文件保持精简（<800行）

### 后端
- 遵循 PEP 8 规范
- 使用类型注解
- 函数文档字符串
- 异步优先（async/await）

---

## Git 提交规范

```
<type>: <description>

<optional body>
```

**类型**：
- `feat`: 新功能
- `fix`: 修复bug
- `refactor`: 重构
- `docs`: 文档更新
- `style`: 代码格式调整
- `test`: 测试
- `chore`: 构建/工具链

**示例**：
```
feat: 添加卡片批量查询功能

- 支持输入最多10000个ICCID
- 查询结果直接显示在主列表
- 添加未找到卡号提示
```

---

## 前后端对接规范

### 1. 接口文档必须明确
- 请求参数（类型、必填、默认值）
- 响应格式（统一结构）
- 错误码定义
- 示例数据

### 2. 统一响应格式
```typescript
interface ApiResponse<T> {
  code: number        // 200成功，其他失败
  message: string     // 提示信息
  data: T            // 业务数据
}
```

### 3. 字段命名约定
- 后端：snake_case（`user_id`）
- 前端：camelCase（`userId`）
- 前端API层负责转换

### 4. 日期格式
- 存储：`YYYY-MM-DD`
- 显示：`YY/M/D`（如：26/1/31）

### 5. 数据校验
- 前端：表单验证
- 后端：Pydantic验证
- 双重保障

---

## 错误处理

### 前端
```typescript
const fetchData = async () => {
  loading.value = true
  try {
    const data = await api.getData()
    list.value = data
  } catch (error) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}
```

### 后端
```python
from fastapi import HTTPException

@router.get("/cards")
async def get_cards():
    try:
        cards = await card_service.get_list()
        return {"code": 200, "data": cards}
    except Exception as e:
        logger.error(f"获取卡片失败: {e}")
        raise HTTPException(status_code=500, detail="获取卡片失败")
```

---

## 性能优化

### 前端
- 表格虚拟滚动（>100条）
- 图片懒加载
- 路由懒加载
- 防抖：搜索（500ms）
- 节流：滚动（100ms）

### 后端
- 数据库索引优化
- 查询结果缓存（Redis）
- 分页查询
- 异步处理
- 连接池管理

---

## 安全规范

### 前端
- 所有用户输入进行XSS过滤
- Token加密存储
- 敏感操作二次确认
- 禁止在前端存储敏感信息

### 后端
- SQL注入防护（ORM参数化）
- XSS防护（输入验证）
- CSRF防护（Token验证）
- 密码加密（Bcrypt）
- API限流

---

## 调试技巧

### 前端
```typescript
// 开发环境日志
const logger = {
  log: (...args) => {
    if (import.meta.env.DEV) console.log('[LOG]', ...args)
  },
  error: (...args) => {
    console.error('[ERROR]', ...args)
  }
}
```

### 后端
```python
# 使用 loguru
from loguru import logger

logger.add("logs/app.log", rotation="500 MB")
logger.info("用户登录成功", user_id=user.id)
```

---

## 测试规范

### 前端
- 单元测试：Vitest
- E2E测试：Playwright
- 覆盖率：>60%

### 后端
- 单元测试：pytest
- API测试：httpx
- 覆盖率：>80%

---

## 部署流程

### 开发环境
```bash
# 前端
npm run dev

# 后端
uvicorn app.main:app --reload
```

### 生产环境
```bash
# Docker部署
docker-compose up -d --build

# 健康检查
curl http://localhost:8000/api/v1/health
```
