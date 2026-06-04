# A股利好监控 v3 — GitHub Actions 版

A-stock bullish news monitor that runs on GitHub Actions (cloud) instead of your local machine.

## 快速上手

### 1. 创建 GitHub 仓库

1. 登录 GitHub → New Repository
2. 仓库名：`a-stock-monitor`（或任意名称）
3. 选择 **Private**（推荐）

### 2. 推送代码

```bash
# 在 github-deploy 目录下执行

# 初始化 git
git init
git add -A
git commit -m "Initial commit: A-stock monitor v3"

# 关联远程仓库（替换 YOUR_USERNAME）
git remote add origin https://github.com/YOUR_USERNAME/a-stock-monitor.git
git branch -M main
git push -u origin main
```

### 3. 配置 Netlify 部署

由于 Netlify 的自动部署会从 GitHub 仓库拉取，而 GitHub Actions 会生成 dashboard 到 deploy/ 目录，需要：

**方法一（推荐）：通过 GitHub Actions 部署**

1. 在 [Netlify](https://app.netlify.com) 创建新站点（手动 or Drop）
2. 获取 Netlify Personal Access Token：
   - Netlify → User Settings → Applications → Personal access tokens
   - 生成一个新 token
3. 回到 GitHub 仓库 → Settings → Secrets and variables → Actions
4. 添加以下 Secrets：
   - `NETLIFY_AUTH_TOKEN`：你生成的 Netlify token
   - `TELEGRAM_BOT_TOKEN`：（可选）Telegram Bot Token
   - `TELEGRAM_CHAT_ID`：（可选）Telegram Chat ID
   - `SERVERCHAN_KEY`：（可选）ServerChan 推送 Key
   - `BARK_KEY`：（可选）Bark iOS 推送 Key

### 4. 首次手动触发

1. 打开 GitHub 仓库 → Actions → A-Stock Monitor
2. 点击 **Run workflow** → 手动触发一次
3. 等待 ~2 分钟，检查 Actions 日志

### 5. 查看 Dashboard

- Netlify 会生成一个 `xxx.netlify.app` 域名
- 每次 GitHub Actions 运行后自动更新

## 运行频率

- 周一到周五，A 股交易时段 09:20 - 15:00（北京时间）
- 每 5 分钟扫描一次
- GitHub Actions 免费额度足够覆盖

## 项目结构

```
.
├── .github/workflows/monitor.yml   # GitHub Actions 配置
├── run.py                          # 主入口
├── monitor/                        # 监控模块
│   ├── config.py                   # 配置（关键词、通知、来源）
│   ├── scraper.py                  # 新闻抓取
│   ├── analyzer.py                 # 评分引擎
│   ├── dashboard.py                # 看板生成
│   ├── notifier.py                 # 推送通知
│   ├── auto_deploy.py              # 部署文件同步
│   ├── recommender.py              # 多因子推荐
│   ├── keyword_learner.py          # 自学习引擎
│   ├── heat_tracker.py             # 热点追踪
│   └── market_data.py              # 市场数据
├── deploy/                         # 部署目录
│   ├── index.html                  # 看板（由脚本生成）
│   └── netlify.toml
├── outputs/                        # 运行输出
├── requirements.txt
├── netlify.toml
└── README.md
```

## 推送配置（可选）

### Telegram
1. 在 Telegram 搜索 @BotFather，创建 Bot 获取 Token
2. 获取 Chat ID（向 Bot 发消息后访问 `https://api.telegram.org/bot<TOKEN>/getUpdates`）
3. 设置 GitHub Secrets：`TELEGRAM_BOT_TOKEN`、`TELEGRAM_CHAT_ID`

### ServerChan（微信推送）
1. 访问 https://sct.ftqq.com 注册
2. 获取 SendKey
3. 设置 GitHub Secrets：`SERVERCHAN_KEY`

### Bark（iOS 推送）
1. 安装 Bark App
2. 获取 Key
3. 设置 GitHub Secrets：`BARK_KEY`

## 注意事项

- 代码只依赖 Python 标准库 + requests/beautifulsoup4/lxml
- 所有数据来自东方财富、财联社、新浪财经公开接口
- 不涉及任何 API Key 需求（推送到通知渠道除外）
- GitHub Actions 日志中不会泄露 Secrets
