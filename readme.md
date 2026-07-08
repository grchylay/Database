# TSAR 数据中心运行监控大屏

> **SER DATA LAB — NOC Monitoring Dashboard**  
> 数据采集与监控系统 | 20台服务器 × 7天 × 79,200条记录

---

## 大屏预览

![NOC Dashboard](dashboard_screenshot.png)

---

## 一、项目概述

基于 TSAR 服务器监控原始数据，完成以下三个核心任务：

| # | 任务 | 说明 |
|---|------|------|
| 🔗 | **ER 关系图** | 4张表的实体关系设计，主外键关联，1:N 基数标注 |
| ⏱ | **时间戳解析** | 13位毫秒 Unix 时间戳 → 北京时间 (YYYY-MM-DD HH:MM:SS) |
| 📊 | **按小时汇总** | 5分钟级磁盘采样 → 小时级 AVG/MAX/MIN/COUNT |

---

## 二、数据概览

| 文件名 | 表名 | 记录数 | 说明 |
|--------|------|--------|------|
| `host_detail.dat` | host_detail | 20 | 主机信息明细表（20台服务器） |
| `mod_detail.dat` | mod_detail | 55 | 指标MOD字典表（35个磁盘指标 + 20个性能指标） |
| `disk_tsar.dat` | disk_tsar | 12,000 | 磁盘监控采集明细（每5分钟） |
| `pref_tsar.dat` | pref_tsar | 67,200 | 性能监控采集明细（每小时） |

> 数据时间范围：`2026-07-01 00:00:00` ~ `2026-08-11 15:55:00`  
> 分隔符：制表符 `\t`（Tab）  
> 时间戳格式：毫秒级 Unix 时间戳

---

## 三、快速运行

### 环境要求
- Python 3.10+
- 浏览器（Chrome / Edge / Firefox）

### 三步启动

```bash
# Step 1: 导入数据 + 时间戳转换 → SQLite 数据库
python etl_import.py

# Step 2: 生成小时汇总 + CSV 导出
python hourly_summary.py

# Step 3: 打开监控大屏
start noc_dashboard.html
```

### 可选脚本

```bash
python generate_charts.py      # 生成 10 张 PNG 分析图表 → output/
python generate_report_doc.py  # 生成 Word 分析报告
python draw_er_diagram.py      # 单独生成 ER 关系图
python build_dashboard_premium.py  # 重新生成大屏 HTML
```

---

## 四、数据库设计

### ER 关系图

```
HOST_DETAIL (20) ──1:N──> DISK_TSAR (12,000)
       │                        │ mod
       │                        ▼
       └──1:N──> PREF_TSAR (67,200) <── MOD_DETAIL (55)
                        │
                        ▼
                 tsar_hourly (79,096)  ← 小时聚合物化表
```

### 数据库表结构

| 表名 | 类型 | 记录数 | 说明 |
|------|------|--------|------|
| `host_detail` | 维度表 | 20 | 主机信息，PK: hostid |
| `mod_detail` | 维度表 | 55 | 指标字典，PK: mod |
| `tsar_detail` | 事实表 | 79,200 | 统一采集明细 (disk+pref)，FK: hostid, mod |
| `tsar_hourly` | 汇总表 | 79,096 | 小时级聚合 (AVG/MAX/MIN/COUNT) |

### 视图

| 视图名 | 说明 |
|--------|------|
| `v_tsar_hourly` | 小时汇总视图 (长表格式) |
| `v_hourly_wide` | 宽表视图 (24个指标列 pivot，一行一主机一小时) |

---

## 五、监控大屏功能

### 布局（4列网格，响应式）

| 位置 | 面板 | 图表类型 | 数据来源 |
|------|------|----------|----------|
| 顶部 | 标题栏 + 实时时钟 + LIVE 指示 | — | — |
| 统计卡 ×4 | 在线主机 / 指标数 / 记录数 / 平均CPU | 数字卡片 | tsar_detail |
| R1 | CPU 趋势 (6主机×168小时) | 折线图 | tsar_hourly |
| R1 | 机房分布 + 数据类型 | 饼图 ×2 | host_detail / tsar_detail |
| R2 | CPU / 内存 / 磁盘 / 负载仪表 | 仪表盘 ×4 | tsar_hourly |
| R3 | CPU 主机对比 (Avg vs Peak) | 柱状图 | tsar_hourly |
| R3 | 进程监控 + 磁盘峰值 | 折线图 + 条形图 | tsar_hourly |
| R4 | 内存使用 (host001) | 折线图 | tsar_hourly |
| R4 | 网络流量 (host001) | 折线图 | tsar_hourly |
| R5 | 系统负载 load1/5/15 | 折线图 | tsar_hourly |
| R5 | 磁盘趋势 (Top 5) | 折线图 | tsar_hourly |

### 响应式适配

| 分辨率 | 布局 |
|--------|------|
| ≥1000px | 4列桌面布局 |
| 550-1000px | 2列平板布局 |
| <550px | 1列手机布局 |

### 设计特性
- 深色 NOC 主题 + Canvas 粒子星空背景
- 毛玻璃面板 + 霓虹发光边框
- 标题渐变动画 + Logo 脉冲效果
- 统计卡片 hover 上浮动画
- 仪表盘环形进度条 + 圆角端点
- 图表渐变色填充

---

## 六、文件清单

### 核心交付

| 文件 | 说明 |
|------|------|
| `noc_dashboard.html` | **监控大屏 HTML**（浏览器直接打开） |
| `etl_import.py` | 数据 ETL 导入 + 时间戳转换 |
| `hourly_summary.py` | 小时汇总 + CSV 导出 |
| `create_schema.sql` | 建库 DDL |
| `verify.sql` | 数据验证 SQL |

### 图表与报告

| 文件 | 说明 |
|------|------|
| `generate_charts.py` | 生成 10 张分析图表 |
| `draw_er_diagram.py` | ER 关系图绘制 |
| `generate_report_doc.py` | Word 分析报告生成 |
| `build_dashboard_premium.py` | 大屏 HTML 生成脚本 |
| `analysis_report.md` | Markdown 分析报告 |
| `analysis_report.docx` | Word 分析报告 |

### 数据文件

| 文件 | 说明 |
|------|------|
| `host_detail.dat` | 主机原始数据 (20行) |
| `mod_detail.dat` | 指标字典原始数据 (55行) |
| `disk_tsar.dat` | 磁盘采集原始数据 (12,000行) |
| `pref_tsar.dat` | 性能采集原始数据 (67,200行) |
| `tsar_monitor.db` | SQLite 数据库 (32MB) |
| `tsar_hourly.csv` | 小时汇总导出 (6MB) |

---

## 七、技术栈

| 层级 | 技术 |
|------|------|
| 数据处理 | Python 3 (csv, sqlite3, datetime) |
| 数据库 | SQLite 3 |
| 可视化 | ECharts 5 (CDN) |
| 前端 | Vanilla HTML5 + CSS3 + JavaScript |
| 静态图表 | Matplotlib 3.10 |
| 报告生成 | python-docx |

---

## 八、分析结论

| 维度 | 结论 | 详情 |
|------|------|------|
| CPU | 整体健康 | 平均 43.2%，峰值偶达 99%，属正常波动 |
| 磁盘 | 需关注 | 5台主机 sda 峰值超 97%，建议扩容 |
| 内存 | 充足 | swap 使用极低，物理内存配置合理 |
| 网络 | 正常 | 流量波动符合业务规律 |
| 负载 | 可控 | 整体负载在合理范围，无持续高负载 |
