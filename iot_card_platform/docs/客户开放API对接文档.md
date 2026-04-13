# 物联网卡开放 API 对接文档

## 1. 文档说明

本文档用于提供给客户进行系统对接。

适用对象：

- 平台一级用户
- 需要通过接口查询名下物联网卡与流量池数据的客户系统

每个一级用户对应一套独立的接口凭证：

- `APPID`
- `AppSecret`

请妥善保管，如怀疑泄露，请立即联系平台侧重置密钥。

## 2. 接口基础信息

- 接口版本：`v1`
- Base URL：`/api/v1/open`
- 请求格式：`application/json`
- 字符编码：`UTF-8`

示例地址：

- 测试环境：`http://localhost:8000/api/v1/open`
- 正式环境：以平台实际提供地址为准

## 3. 认证方式

所有接口均通过请求头认证。

请求头要求：

```http
X-APP-ID: 您的APPID
X-APP-SECRET: 您的AppSecret
Content-Type: application/json
```

示例：

```bash
curl --request GET 'http://localhost:8000/api/v1/open/cards?page=1&page_size=20' \
  --header 'X-APP-ID: APP1234567890ABCD' \
  --header 'X-APP-SECRET: your_app_secret'
```

## 4. 凭证获取方式

平台后台支持以下方式获取：

- 超级管理员可为一级用户查看和重置 API 凭证
- 一级用户可在后台查看自己的 API 凭证

注意事项：

- `APPID` 用于标识调用方
- `AppSecret` 仅在重置时完整展示一次
- 重置后旧 `AppSecret` 立即失效

## 5. 通用返回格式

### 5.1 成功返回

```json
{
  "code": 200,
  "msg": "success",
  "data": {}
}
```

### 5.2 失败返回

```json
{
  "code": 400,
  "msg": "错误信息",
  "data": null
}
```

### 5.3 常见状态说明

| code | 说明 |
|------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 401 | 认证失败 |
| 403 | 无权限访问 |
| 404 | 数据不存在 |
| 500 | 服务端异常 |

## 6. 物联网卡接口

### 6.1 获取卡片列表

- 方法：`GET /cards`

查询参数：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| keyword | string | 否 | ICCID / MSISDN / ICCID后6位 |
| status | string | 否 | 卡状态 |
| carrier | string | 否 | 运营商 |
| page | int | 否 | 页码，默认 1 |
| page_size | int | 否 | 每页数量，默认 20，最大 100 |

请求示例：

```bash
curl --request GET 'http://localhost:8000/api/v1/open/cards?page=1&page_size=20&keyword=8986' \
  --header 'X-APP-ID: APP1234567890ABCD' \
  --header 'X-APP-SECRET: your_app_secret'
```

返回示例：

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "total": 1,
    "page": 1,
    "page_size": 20,
    "items": [
      {
        "id": 1001,
        "iccid": "8986001234567890123",
        "msisdn": "14400001111",
        "carrier": "china_mobile",
        "carrier_name": "中国移动",
        "flow_size": 3072,
        "flow_size_display": "3G",
        "data_used": 2048,
        "data_used_month": 2048,
        "data_total": 3072,
        "data_remain": 1024,
        "data_usage_percent": 66.67,
        "status": "activated",
        "status_name": "已激活",
        "pool_id": 88,
        "is_pool_member": true,
        "data_sync_at": "2026-04-10T08:30:00"
      }
    ]
  }
}
```

### 6.2 获取卡片详情

- 方法：`GET /cards/{card_id}`

说明：

- 返回单张卡的完整详情
- 包含卡状态、当月用量、总用量、剩余流量、流量池归属等信息

请求示例：

```bash
curl --request GET 'http://localhost:8000/api/v1/open/cards/1001' \
  --header 'X-APP-ID: APP1234567890ABCD' \
  --header 'X-APP-SECRET: your_app_secret'
```

### 6.3 获取卡片用量摘要

- 方法：`GET /cards/{card_id}/usage-summary`

用途：

- 获取卡片单日用量信息
- 获取卡片月用量信息
- 获取卡片状态
- 获取当前是否属于流量池

返回示例：

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "card_id": 1001,
    "iccid": "8986001234567890123",
    "status": "activated",
    "status_name": "已激活",
    "daily_usage": {
      "snapshot_date": "2026-04-10",
      "used_mb": 125,
      "total_used_mb": 2048
    },
    "monthly_usage": {
      "snapshot_month": "2026-04",
      "used_mb": 2048,
      "total_mb": 3072,
      "remaining_mb": 1024,
      "usage_percent": 66.67
    },
    "pool_info": {
      "pool_id": 88,
      "is_pool_member": true
    },
    "data_sync_at": "2026-04-10T08:30:00"
  }
}
```

字段说明：

- `daily_usage.used_mb`：单日新增用量，单位 MB
- `monthly_usage.used_mb`：当前月份累计用量，单位 MB
- `status`：卡状态编码
- `status_name`：卡状态中文名称

### 6.4 获取卡片用量历史

- 方法：`GET /cards/{card_id}/usage-history`

查询参数：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| start_date | string | 否 | 开始日期，格式 `YYYY-MM-DD` |
| end_date | string | 否 | 结束日期，格式 `YYYY-MM-DD` |

说明：

- 返回每日用量历史
- `daily_used` 表示当日新增用量
- `data_used` 表示截至当日累计用量

请求示例：

```bash
curl --request GET 'http://localhost:8000/api/v1/open/cards/1001/usage-history?start_date=2026-04-01&end_date=2026-04-10' \
  --header 'X-APP-ID: APP1234567890ABCD' \
  --header 'X-APP-SECRET: your_app_secret'
```

返回示例：

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "card_id": 1001,
    "start_date": "2026-04-01",
    "end_date": "2026-04-10",
    "items": [
      {
        "snapshot_date": "2026-04-08",
        "data_used": 1800,
        "daily_used": 150,
        "data_total": 3072
      },
      {
        "snapshot_date": "2026-04-09",
        "data_used": 1923,
        "daily_used": 123,
        "data_total": 3072
      },
      {
        "snapshot_date": "2026-04-10",
        "data_used": 2048,
        "daily_used": 125,
        "data_total": 3072
      }
    ]
  }
}
```

### 6.5 获取卡片统计

- 方法：`GET /cards/stats`

说明：

- 返回当前客户名下卡片整体统计信息
- 可用于首页概览或仪表盘展示

请求示例：

```bash
curl --request GET 'http://localhost:8000/api/v1/open/cards/stats' \
  --header 'X-APP-ID: APP1234567890ABCD' \
  --header 'X-APP-SECRET: your_app_secret'
```

### 6.6 批量查询卡片

- 方法：`POST /cards/batch-query`

请求体：

```json
[
  "8986001234567890123",
  "8986001234567890456"
]
```

说明：

- 单次最多支持 10000 个 ICCID
- 返回找到的卡片和未找到的 ICCID 列表

请求示例：

```bash
curl --request POST 'http://localhost:8000/api/v1/open/cards/batch-query' \
  --header 'Content-Type: application/json' \
  --header 'X-APP-ID: APP1234567890ABCD' \
  --header 'X-APP-SECRET: your_app_secret' \
  --data '[
    "8986001234567890123",
    "8986001234567890456"
  ]'
```

## 7. 流量池接口

### 7.1 获取流量池列表

- 方法：`GET /pools`

查询参数：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 否 | 流量池名称 |
| carrier | string | 否 | 运营商 |
| status | string | 否 | 状态 |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |

请求示例：

```bash
curl --request GET 'http://localhost:8000/api/v1/open/pools?page=1&page_size=20' \
  --header 'X-APP-ID: APP1234567890ABCD' \
  --header 'X-APP-SECRET: your_app_secret'
```

### 7.2 获取流量池详情

- 方法：`GET /pools/{pool_id}`

说明：

- 返回流量池基本信息
- 包含总流量、已用流量、剩余流量、用量百分比、流量池状态等信息

请求示例：

```bash
curl --request GET 'http://localhost:8000/api/v1/open/pools/88' \
  --header 'X-APP-ID: APP1234567890ABCD' \
  --header 'X-APP-SECRET: your_app_secret'
```

### 7.3 获取流量池用量详情

- 方法：`GET /pools/{pool_id}/usage`

用途：

- 获取流量池详情页展示数据
- 获取池内卡片明细用量

返回示例：

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "pool_id": 88,
    "pool_name": "移动共享池A",
    "spec_name": "中国移动3G/月包",
    "card_count": 20,
    "data_total": 61440,
    "data_used": 28672,
    "data_remain": 32768,
    "usage_percent": 46.67,
    "alert_threshold_1": 80,
    "alert_threshold_2": 90,
    "alert_threshold_3": 100,
    "is_alert": false,
    "is_exceed": false,
    "cards": [
      {
        "card_id": 1001,
        "iccid": "8986001234567890123",
        "data_used": 2048,
        "data_total": 3072,
        "usage_percent": 66.67
      }
    ]
  }
}
```

## 8. 状态字段说明

### 8.1 卡状态

| status | 说明 |
|--------|------|
| stock | 库存 |
| testing | 测试期 |
| silent | 沉默期 |
| activated | 已激活 |
| expired | 已到期 |
| suspended | 已停机 |
| cancelled | 已销卡 |

### 8.2 流量池状态

| status | 说明 |
|--------|------|
| enable | 启用 |
| disable | 停用 |

## 9. 对接建议

- 建议由客户服务端保存 `APPID` 与 `AppSecret`
- 不建议在浏览器前端直接暴露接口密钥
- 建议调用方自行增加重试、日志记录和超时控制
- 如需更高频率调用，请提前与平台确认接口频率限制

## 10. 技术支持

如需新增接口字段、扩展查询条件或协助联调，请联系平台技术支持人员。

## 11. 多语言调用示例

以下示例以获取卡片列表接口为例：

- 接口地址：`GET /api/v1/open/cards?page=1&page_size=20`
- 认证方式：请求头传入 `X-APP-ID` 与 `X-APP-SECRET`

请将以下示例中的地址和凭证替换为实际值。

### 11.1 Java 调用示例

```java
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;

public class OpenApiJavaDemo {
    public static void main(String[] args) throws Exception {
        String baseUrl = "http://localhost:8000";
        String appId = "APP1234567890ABCD";
        String appSecret = "your_app_secret";

        String apiUrl = baseUrl + "/api/v1/open/cards?page=1&page_size=20";
        URL url = new URL(apiUrl);
        HttpURLConnection connection = (HttpURLConnection) url.openConnection();
        connection.setRequestMethod("GET");
        connection.setRequestProperty("X-APP-ID", appId);
        connection.setRequestProperty("X-APP-SECRET", appSecret);
        connection.setRequestProperty("Content-Type", "application/json");
        connection.setConnectTimeout(10000);
        connection.setReadTimeout(10000);

        int statusCode = connection.getResponseCode();
        BufferedReader reader = new BufferedReader(
            new InputStreamReader(
                statusCode >= 200 && statusCode < 400
                    ? connection.getInputStream()
                    : connection.getErrorStream(),
                "UTF-8"
            )
        );

        StringBuilder response = new StringBuilder();
        String line;
        while ((line = reader.readLine()) != null) {
            response.append(line);
        }
        reader.close();
        connection.disconnect();

        System.out.println("HTTP Status: " + statusCode);
        System.out.println("Response: " + response);
    }
}
```

如项目使用 `OkHttp`，也可按以下方式调用：

```java
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;

public class OpenApiOkHttpDemo {
    public static void main(String[] args) throws Exception {
        OkHttpClient client = new OkHttpClient();

        Request request = new Request.Builder()
            .url("http://localhost:8000/api/v1/open/cards?page=1&page_size=20")
            .addHeader("X-APP-ID", "APP1234567890ABCD")
            .addHeader("X-APP-SECRET", "your_app_secret")
            .addHeader("Content-Type", "application/json")
            .build();

        try (Response response = client.newCall(request).execute()) {
            System.out.println("HTTP Status: " + response.code());
            System.out.println("Response: " + response.body().string());
        }
    }
}
```

### 11.2 PHP 调用示例

```php
<?php

$baseUrl = 'http://localhost:8000';
$appId = 'APP1234567890ABCD';
$appSecret = 'your_app_secret';

$url = $baseUrl . '/api/v1/open/cards?page=1&page_size=20';

$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, $url);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_CUSTOMREQUEST, 'GET');
curl_setopt($ch, CURLOPT_HTTPHEADER, [
    'X-APP-ID: ' . $appId,
    'X-APP-SECRET: ' . $appSecret,
    'Content-Type: application/json'
]);
curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 10);
curl_setopt($ch, CURLOPT_TIMEOUT, 10);

$response = curl_exec($ch);
$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);

if (curl_errno($ch)) {
    echo 'Curl Error: ' . curl_error($ch) . PHP_EOL;
} else {
    echo 'HTTP Status: ' . $httpCode . PHP_EOL;
    echo 'Response: ' . $response . PHP_EOL;
}

curl_close($ch);
```

如果需要调用 `POST /api/v1/open/cards/batch-query`，可参考：

```php
<?php

$baseUrl = 'http://localhost:8000';
$appId = 'APP1234567890ABCD';
$appSecret = 'your_app_secret';

$url = $baseUrl . '/api/v1/open/cards/batch-query';
$data = json_encode([
    '8986001234567890123',
    '8986001234567890456'
], JSON_UNESCAPED_UNICODE);

$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, $url);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_POSTFIELDS, $data);
curl_setopt($ch, CURLOPT_HTTPHEADER, [
    'X-APP-ID: ' . $appId,
    'X-APP-SECRET: ' . $appSecret,
    'Content-Type: application/json',
    'Content-Length: ' . strlen($data)
]);

$response = curl_exec($ch);
$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
echo 'HTTP Status: ' . $httpCode . PHP_EOL;
echo 'Response: ' . $response . PHP_EOL;
curl_close($ch);
```

### 11.3 Python 调用示例

推荐使用 `requests` 库。

```python
import requests

BASE_URL = "http://localhost:8000"
APP_ID = "APP1234567890ABCD"
APP_SECRET = "your_app_secret"

url = f"{BASE_URL}/api/v1/open/cards"
headers = {
    "X-APP-ID": APP_ID,
    "X-APP-SECRET": APP_SECRET,
    "Content-Type": "application/json",
}
params = {
    "page": 1,
    "page_size": 20,
}

response = requests.get(url, headers=headers, params=params, timeout=10)
print("HTTP Status:", response.status_code)
print("Response:", response.text)
```

获取卡片用量摘要示例：

```python
import requests

BASE_URL = "http://localhost:8000"
APP_ID = "APP1234567890ABCD"
APP_SECRET = "your_app_secret"
CARD_ID = 1001

url = f"{BASE_URL}/api/v1/open/cards/{CARD_ID}/usage-summary"
headers = {
    "X-APP-ID": APP_ID,
    "X-APP-SECRET": APP_SECRET,
    "Content-Type": "application/json",
}

response = requests.get(url, headers=headers, timeout=10)
data = response.json()

print("HTTP Status:", response.status_code)
print("Code:", data.get("code"))
print("Message:", data.get("msg"))
print("Data:", data.get("data"))
```

获取流量池详情示例：

```python
import requests

BASE_URL = "http://localhost:8000"
APP_ID = "APP1234567890ABCD"
APP_SECRET = "your_app_secret"
POOL_ID = 88

url = f"{BASE_URL}/api/v1/open/pools/{POOL_ID}/usage"
headers = {
    "X-APP-ID": APP_ID,
    "X-APP-SECRET": APP_SECRET,
    "Content-Type": "application/json",
}

response = requests.get(url, headers=headers, timeout=10)
print("HTTP Status:", response.status_code)
print("Response:", response.text)
```

## 12. 附加说明

- 如客户使用其他语言，对接方式相同，核心是请求头中带上 `X-APP-ID` 与 `X-APP-SECRET`
- 若需平台方提供指定语言 SDK 示例，可继续补充
