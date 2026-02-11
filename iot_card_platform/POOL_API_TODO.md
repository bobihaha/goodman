# 流量池模块后端API待实现清单

## 当前问题

前端访问流量池列表页面时，调用 `GET /api/v1/pools/stats` 接口返回 **422 错误**。

## 需要后端实现的接口

### 1. 流量池统计接口（优先级：高）

**接口**: `GET /api/v1/pools/stats`

**说明**: 获取流量池统计数据，用于列表页顶部的统计卡片展示

**请求参数**: 无

**响应格式**:
```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "total": 10,              // 流量池总数
    "enabled": 8,             // 启用中的数量
    "disabled": 2,            // 禁用的数量
    "alert_count": 3,         // 告警数量（使用率超过告警阈值的流量池数量）
    "total_cards": 150,       // 总卡片数（所有流量池中的卡片总数）
    "total_flow": 153600,     // 总流量(MB)
    "used_flow": 76800,       // 已用流量(MB)
    "by_carrier": {
      "cmcc": 5,              // 移动流量池数量
      "cucc": 3,              // 联通流量池数量
      "ctcc": 2               // 电信流量池数量
    }
  }
}
```

**实现建议**:
```python
@router.get("/pools/stats")
async def get_pool_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取流量池统计"""
    # 查询当前用户的流量池
    query = db.query(TrafficPool).filter(TrafficPool.user_id == current_user.id)
    
    total = query.count()
    enabled = query.filter(TrafficPool.status == 'enable').count()
    disabled = query.filter(TrafficPool.status == 'disable').count()
    
    # 告警数量（使用率超过告警阈值）
    alert_count = query.filter(
        TrafficPool.usage_percent >= TrafficPool.alert_threshold
    ).count()
    
    # 总卡片数
    total_cards = db.query(func.sum(TrafficPool.card_count)).filter(
        TrafficPool.user_id == current_user.id
    ).scalar() or 0
    
    # 总流量和已用流量
    total_flow = db.query(func.sum(TrafficPool.data_total)).filter(
        TrafficPool.user_id == current_user.id
    ).scalar() or 0
    
    used_flow = db.query(func.sum(TrafficPool.data_used)).filter(
        TrafficPool.user_id == current_user.id
    ).scalar() or 0
    
    # 按运营商统计
    by_carrier = {
        'cmcc': query.filter(TrafficPool.carrier == 'cmcc').count(),
        'cucc': query.filter(TrafficPool.carrier == 'cucc').count(),
        'ctcc': query.filter(TrafficPool.carrier == 'ctcc').count()
    }
    
    return {
        "total": total,
        "enabled": enabled,
        "disabled": disabled,
        "alert_count": alert_count,
        "total_cards": total_cards,
        "total_flow": total_flow,
        "used_flow": used_flow,
        "by_carrier": by_carrier
    }
```

### 2. 其他可能缺失的接口

以下接口也需要确认是否已实现：

#### 2.1 流量池列表
- `GET /api/v1/pools` - 获取流量池列表（带分页和筛选）

#### 2.2 流量池CRUD
- `POST /api/v1/pools` - 创建流量池
- `GET /api/v1/pools/{id}` - 获取流量池详情
- `PUT /api/v1/pools/{id}` - 更新流量池
- `DELETE /api/v1/pools/{id}` - 删除流量池
- `PUT /api/v1/pools/{id}/status` - 启用/禁用流量池

#### 2.3 卡片管理
- `POST /api/v1/pools/{id}/cards` - 添加卡片到流量池
- `DELETE /api/v1/pools/{id}/cards` - 从流量池移除卡片
- `GET /api/v1/pools/{id}/cards` - 获取池内卡片列表

#### 2.4 用量趋势
- `GET /api/v1/pools/{id}/usage/trend` - 获取用量趋势（最近N天）

#### 2.5 加油包相关
- `GET /api/v1/pools/packages` - 获取加油包列表
- `POST /api/v1/pools/{id}/recharge` - 充值加油包
- `GET /api/v1/pools/{id}/recharge-logs` - 获取充值记录

#### 2.6 导出
- `POST /api/v1/pools/export` - 导出流量池列表

## 临时解决方案

前端已做如下调整：
1. ✅ 统计数据获取失败时不显示错误提示
2. ✅ 使用默认值（全部为0）显示统计卡片
3. ✅ 不影响流量池列表的正常显示

## 测试步骤

后端实现接口后，请按以下步骤测试：

1. **测试统计接口**
   ```bash
   curl -X GET "http://localhost:3000/api/v1/pools/stats" \
     -H "Authorization: Bearer {token}"
   ```

2. **测试流量池列表**
   ```bash
   curl -X GET "http://localhost:3000/api/v1/pools?page=1&page_size=20" \
     -H "Authorization: Bearer {token}"
   ```

3. **测试创建流量池**
   ```bash
   curl -X POST "http://localhost:3000/api/v1/pools" \
     -H "Authorization: Bearer {token}" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "测试流量池",
       "carrier": "cmcc",
       "flow_size": 1024,
       "period_type": "monthly",
       "alert_threshold": 80,
       "stop_threshold": 100
     }'
   ```

## 数据库表结构参考

流量池表 `traffic_pools` 应包含以下字段：

```sql
CREATE TABLE traffic_pools (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL COMMENT '流量池名称',
    user_id BIGINT NOT NULL COMMENT '所属用户ID',
    carrier ENUM('cmcc', 'cucc', 'ctcc') NOT NULL COMMENT '运营商',
    flow_size INT NOT NULL COMMENT '单卡流量(MB)',
    period_type ENUM('monthly', 'yearly') NOT NULL COMMENT '周期类型',
    pool_type ENUM('manual', 'auto') DEFAULT 'manual' COMMENT '流量池类型',
    package_id VARCHAR(50) COMMENT '关联的套餐ID（自动池使用）',
    card_count INT DEFAULT 0 COMMENT '卡片数量',
    data_total BIGINT DEFAULT 0 COMMENT '总流量(MB)',
    data_used BIGINT DEFAULT 0 COMMENT '已用流量(MB)',
    data_remaining BIGINT DEFAULT 0 COMMENT '剩余流量(MB)',
    usage_percent DECIMAL(5,2) DEFAULT 0 COMMENT '使用率(%)',
    alert_threshold INT DEFAULT 80 COMMENT '告警阈值(%)',
    stop_threshold INT DEFAULT 100 COMMENT '停卡阈值(%)',
    is_alert BOOLEAN DEFAULT FALSE COMMENT '是否触发告警',
    status ENUM('enable', 'disable') DEFAULT 'enable' COMMENT '状态',
    remark TEXT COMMENT '备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_carrier (carrier),
    INDEX idx_status (status),
    INDEX idx_package_id (package_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='流量池表';
```

## 联系方式

如有问题，请联系前端开发人员进行接口对接。



