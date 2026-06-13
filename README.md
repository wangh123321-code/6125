# 🏊 省游泳队训练管理平台

专业的游泳队训练管理系统，支持智能设备数据接入、训练计划管理、AI训练建议、自动月度报告。

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端 | **Vue 3** + Vite | Composition API |
| UI组件库 | **Element Plus** | 深蓝色体育主题 |
| 图表 | **ECharts 5** | 心率/配速/划距趋势等 |
| 后端 | **FastAPI** + Python 3.11 | 异步高性能，Swagger自动生成 |
| 主数据库 | **MongoDB 7** (motor异步驱动) | 存储非结构化训练数据 |
| 缓存/实时计算 | **Redis 7** | Stream+List缓存实时数据 |
| 部署 | **Docker Compose** | 4容器一键部署 |
| PDF导出 | **ReportLab + Matplotlib** | 图表嵌入月报 |

## 目录结构

```
6125/
├── backend/                     # FastAPI 后端
│   ├── app/
│   │   ├── config.py            # 环境变量配置
│   │   ├── database.py          # MongoDB + Redis 连接
│   │   ├── main.py              # FastAPI 入口 (CORS + 路由注册)
│   │   ├── models/__init__.py   # 数据模型定义
│   │   ├── schemas/__init__.py  # Pydantic Schema
│   │   ├── routers/
│   │   │   ├── auth.py          # 认证+用户+演示数据初始化
│   │   │   ├── data.py          # 三路数据接入 + SSE实时流 + Session管理
│   │   │   ├── training.py      # 训练计划+建议+统计
│   │   │   └── reports.py       # 月度报告生成+PDF下载
│   │   ├── services/__init__.py # 业务服务（扩展）
│   │   └── utils/
│   │       ├── auth.py          # 密码哈希/JWT签发/角色依赖
│   │       └── helpers.py       # 时间戳对齐/配速计算/心率区间
│   ├── .env                     # 运行时环境变量
│   ├── .env.example
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                    # Vue 3 前端
│   ├── src/
│   │   ├── layouts/             # 教练布局 + 运动员布局（差异化）
│   │   ├── views/
│   │   │   ├── Login.vue
│   │   │   ├── coach/           # 教练端5个页面
│   │   │   ├── athlete/         # 运动员端3个只读页面
│   │   │   └── headcoach/       # 总教练跨组数据总览
│   │   ├── stores/              # Pinia 用户+训练状态
│   │   ├── router/              # 路由 + 角色权限守卫
│   │   └── utils/               # axios封装 + token管理
│   ├── Dockerfile               # 多阶段构建(Nginx部署)
│   ├── nginx.conf               # 反向代理/api→backend
│   ├── package.json
│   └── vite.config.js
├── docker-compose.yml           # 四容器编排
└── .gitignore
```

## 三路数据流设计

```
智能手环 (1Hz心率+划频) ─┐
                         ├─→ Redis Stream ──对齐合并──→ MongoDB 归档
泳池触壁计时器 (每圈)    ─┤         │
                         │         └─→ SSE 实时推送给教练/运动员端
水下摄像头动作分析 ──────┘
```

### 关键数据格式

| 来源 | 频率 | 关键字段 | Redis键 |
|------|------|---------|---------|
| 手环 | 1/秒 | timestamp, bpm, stroke_rate | `band:{athlete_id}:{session_id}` |
| 触壁 | 每圈 | lap_number, distance_m, time_sec, pace | `touchwall:{athlete_id}:{session_id}` |
| 摄像头 | 每帧 | timestamp, stroke_length_cm, body_rotation_deg | `camera:{athlete_id}:{session_id}` |

三路数据在`/api/data/session/{id}/end`时调用 [helpers.py align_timestamps](file:///d:/bz/612/6125/backend/app/utils/helpers.py#L52-L95) 做时间戳插值对齐后入库。

## 权限体系 (Role-Based Access)

| 角色 | 可见范围 | 主要功能 |
|------|---------|---------|
| **运动员 athlete** | 仅自己 | 看计划、看数据、下载自己的报告 |
| **教练 coach** | 本组 (~15人) | CRUD计划、修改建议、启动/结束训练、生成本组报告 |
| **总教练 headcoach** | 全队 (45人) | 跨组查看、跨组调数据、批量生成报告 |

权限通过 [auth.py require_role](file:///d:/bz/612/6125/backend/app/utils/auth.py#L79-L87) 依赖工厂 + 接口内二次校验实现。

## 核心功能

### ✅ 数据接入与实时处理
- **高并发写入**：asyncio.gather并发处理，40人×1条/秒 ≈ 40 QPS轻松应对
- **SSE实时流**：`/api/data/realtime/{session_id}` 订阅Redis Stream推送心率/圈数
- **自动归档**：训练结束后从Redis取出→对齐→入库→清理临时键

### ✅ AI训练建议
基于本次平均心率、平均配速+同组历史对比给出：
- 建议配速（秒/100m）
- 建议间歇时长（秒）
- 建议原因（文字）
- **教练可手动修改**并持久化保存

### ✅ 月度报告自动生成
报告包含：
1. **总览卡片**：总距离/训练次数/平均心率/进步指数
2. **泳姿占比饼图**（Matplotlib绘制嵌入）
3. **心率区间柱状图**（热身/有氧/无氧/极限）
4. **技术指标趋势折线**（划距、身体转动）
5. **与上月对比表格**（退步>10%项标红）
6. **一键导出PDF**（A4、报告标题+所有图表）

批量生成：`POST /api/reports/group-generate` 用asyncio.gather并发生成整组报告

## 接口文档 (Swagger)

后端启动后自动生成：
- **Swagger UI**：http://localhost:8000/docs
- **ReDoc**：http://localhost:8000/redoc
- **OpenAPI JSON**：http://localhost:8000/openapi.json

所有 30+ 端点全部列出，支持在线调试。

---

## 快速启动

### 方式一：Docker Compose 一键部署 (推荐) ⭐

```bash
# 进入项目根目录
cd d:\bz\612\6125

# 构建并启动所有容器（首次约3-5分钟）
docker-compose up -d --build

# 查看日志
docker-compose logs -f

# 停止
docker-compose down
```

服务启动后访问：
| 服务 | 地址 |
|------|------|
| 前端平台 | http://localhost:5173 |
| 后端Swagger | http://localhost:5173/docs 或 http://localhost:8000/docs |
| MongoDB | localhost:27017 (root/password) |
| Redis | localhost:6379 (redis_password) |

---

### 方式二：本地开发模式

需要本机已安装 MongoDB 7 和 Redis 7。

#### 步骤 1：启动后端

```bash
cd backend

# （可选）创建虚拟环境
python -m venv venv
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 复制并编辑.env
copy .env.example .env
# 确认 .env 中 MongoDB 和 Redis URL 指向本地

# 启动服务 (热重载)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

后端Swagger: http://localhost:8000/docs

#### 步骤 2：启动前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器 (自动打开浏览器)
npm run dev
```

前端地址: http://localhost:5173

Vite代理 `/api` → `http://localhost:8000`，无需配置跨域。

---

## 初始化演示数据

前端或后端启动后，**首次使用需要初始化演示账号**：

调用 Swagger 中的 `POST /api/auth/init-demo-data` 或直接：

```bash
curl -X POST http://localhost:8000/api/auth/init-demo-data
```

成功后可使用以下账号登录：

| 角色 | 用户名 | 密码 | 组 |
|------|--------|------|-----|
| 🎯 总教练 | `headcoach001` | `123456` | - |
| 👨‍🏫 教练A | `coach001` | `123456` | 自由泳组 (15人) |
| 👨‍🏫 教练B | `coach002` | `123456` | 蛙泳组 (15人) |
| 👨‍🏫 教练C | `coach003` | `123456` | 混合组 (15人) |
| 🏊 运动员 | `athlete001` ~ `athlete045` | `123456` | 对应组分 |

## 主要API速览

### 认证管理 `/api/auth`
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/register` | 注册用户 |
| POST | `/login` | 登录获取token |
| GET | `/me` | 当前用户信息 |
| POST | `/init-demo-data` | 重置并初始化演示数据 |
| GET | `/athletes` | 教练/总教练查看运动员列表 |

### 数据接入 `/api/data`
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/band` | 批量上传手环心率数据 |
| POST | `/touchwall` | 上传触壁计时器圈数 |
| POST | `/camera` | 上传摄像头动作分析 |
| POST | `/session/start` | 启动训练课 |
| POST | `/session/{id}/end` | 结束训练课（自动对齐归档） |
| GET | `/session/{id}` | 获取单次训练详情 |
| GET | `/sessions` | 查询训练列表(按权限过滤) |
| GET | `/realtime/{id}` | **SSE实时数据流** |

### 训练计划与建议 `/api/training`
| 方法 | 路径 | 说明 |
|------|------|------|
| POST/GET | `/plan` `/plans` | 训练计划增改查 |
| PUT/DELETE | `/plan/{id}` | 计划修改/软删除 |
| GET | `/suggestions` | 查询AI训练建议 |
| PUT | `/suggestion/{id}` | 教练修改建议 |
| GET | `/stats/athlete/{id}` | 统计指标(30天距离/配速等) |
| GET | `/peer-comparison/{id}` | 同组对比百分位排名 |

### 月度报告 `/api/reports`
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/generate` | 生成单个运动员月报+PDF |
| GET | `/list` | 报告列表 |
| GET | `/{id}` | 报告详情 |
| GET | `/{id}/download` | **下载PDF** |
| GET | `/group-summary` | 组内月度摘要 |
| POST | `/group-generate` | 批量生成整组报告 |

## 生产部署注意事项

1. **修改所有默认密码**
   - `docker-compose.yml` 中 `MONGO_INITDB_ROOT_PASSWORD`
   - `redis` 容器的 `--requirepass`
   - `backend` 环境的 `SECRET_KEY` 设为64+位随机字符串

2. **HTTPS**：在Nginx层(frontend容器)部署SSL证书

3. **数据备份**：
   ```bash
   # MongoDB 导出
   docker exec swim_mongodb mongodump -u root -p password --db swim_db --out /data/backup
   # Redis AOF已启用 appendonly yes
   ```

4. **性能调优**：
   - 高峰期40人×1条/秒：MongoDB建议WiredTiger cache 2GB+
   - Redis建议配置maxmemory-policy allkeys-lru
   - Nginx配置worker_processes auto

## 常见问题

**Q: 前端登录404？**
A: 确认后端已启动，Vite代理`/api`已指向8000端口，或通过docker-compose统一访问5173端口。

**Q: 报告PDF中文字体乱码？**
A: Docker镜像使用系统默认字体，建议在backend/Dockerfile中安装中文字体包。

**Q: 手环数据上传失败？**
A: 检查session_id是否存在（需先调用`/api/data/session/start`），确认token有效。

## 代码参考

- 后端入口 [main.py](file:///d:/bz/612/6125/backend/app/main.py)
- 三路数据接入核心 [data.py](file:///d:/bz/612/6125/backend/app/routers/data.py)
- 训练建议与计划 [training.py](file:///d:/bz/612/6125/backend/app/routers/training.py)
- PDF报告生成 [reports.py](file:///d:/bz/612/6125/backend/app/routers/reports.py)
- 权限校验 [utils/auth.py](file:///d:/bz/612/6125/backend/app/utils/auth.py)
- 时间戳对齐算法 [utils/helpers.py](file:///d:/bz/612/6125/backend/app/utils/helpers.py#L52-L95)
- 前端路由权限守卫 [router/index.js](file:///d:/bz/612/6125/frontend/src/router/index.js)
- Docker编排 [docker-compose.yml](file:///d:/bz/612/6125/docker-compose.yml)

---

© 2024 省游泳队训练管理平台 | 专业 · 高效 · 科学
