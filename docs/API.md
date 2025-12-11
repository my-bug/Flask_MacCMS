# API接口说明

## 采集API格式

### 视频列表接口

请求格式:
```
GET {base_url}?ac=detail&t={category_id}&pg={page}
```

参数说明:
- `ac`: 操作类型，`detail` 表示获取详细列表
- `t`: 分类ID（可选）
- `pg`: 页码

返回格式:
```json
{
  "code": 1,
  "msg": "数据列表",
  "page": 1,
  "pagecount": 9351,
  "limit": "20",
  "total": 187016,
  "list": [
    {
      "vod_id": 419807,
      "vod_name": "视频名称",
      "type_id": 23,
      "type_name": "分类名称",
      "vod_pic": "封面图URL",
      "vod_play_url": "第1集$播放地址",
      "vod_time": "2025-12-07 13:52:37"
    }
  ]
}
```

### 分类列表接口

请求格式:
```
GET {base_url}?ac=list
```

返回格式:
```json
{
  "code": 1,
  "class": [
    {
      "type_id": 20,
      "type_name": "国产视频"
    },
    {
      "type_id": 21,
      "type_name": "中文字幕"
    }
  ]
}
```

## 内部API路由

### 后台管理API

#### 获取采集源的分类
```
GET /admin/collect/source/<source_id>/categories
```

响应:
```json
{
  "success": true,
  "categories": [
    {"id": "20", "name": "国产视频"},
    {"id": "21", "name": "中文字幕"}
  ],
  "source_name": "奥斯影视"
}
```

#### 获取采集状态
```
GET /admin/collect/status
```

响应:
```json
{
  "is_running": true,
  "current_page": 5,
  "success_count": 98,
  "failed_count": 2,
  "skip_count": 15,
  "consecutive_duplicates": 3
}
```

#### 测试采集地址
```
POST /admin/collect/test
Content-Type: application/json

{"url": "https://example.com/api.php/provide/vod?ac=detail"}
```

响应:
```json
{
  "success": true,
  "message": "采集地址有效，检测到 20 个视频",
  "count": 20
}
```

## URL清理规则

### 输入格式
```
第1集$https:\/\/krevonix.com\/20221129\/YLikZezX\/index.m3u8
```

### 清理步骤
1. 移除集数名称: `第1集$` → 删除
2. 移除转义字符: `\/` → `/`
3. 提取纯URL

### 输出格式
```
https://krevonix.com/20221129/YLikZezX/index.m3u8
```

### 多集处理
```
输入: 第1集$url1#第2集$url2
输出: url1#url2
```
