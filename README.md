# 女装退货率计算器 - GitHub Actions 自动更新

## 功能

每天 18:00（北京时间）自动从飞书表格拉取最新「有货退」数据，并部署到 Firebase Hosting。

## 首次配置步骤

### 1. 创建 GitHub 仓库

1. 打开 https://github.com/new
2. 仓库名：`return-rate-calculator`
3. **不要勾选** "Add a README file"
4. 点击 "Create repository"
5. 仓库创建好后，继续下一步

### 2. 生成 Firebase CI Token

在本地终端运行（需要在电脑上已登录 Firebase）：

```bash
firebase login:ci
```

会打开浏览器确认授权，授权后在终端会得到一串 token（格式：`1//xxx...`）。

**复制这个 token**，下一步要用。

### 3. 生成 GitHub Personal Access Token

1. 打开 https://github.com/settings/tokens/new
2. Note 填写：`return-rate-calc-deploy`
3. 勾选 `repo`（完整仓库权限）
4. 点击 "Generate token"，复制生成的 token

### 4. 配置 GitHub Secrets

在 GitHub 仓库页面：
1. 进入 **Settings → Secrets and variables → Actions**
2. 点击 **New repository secret**，添加两个：

| Secret 名称 | 值 |
|---|---|
| `FIREBASE_TOKEN` | 第2步得到的 Firebase CI token |
| `GH_TOKEN` | 第3步得到的 GitHub Personal Access Token |

### 5. 推送代码到 GitHub

在本地终端运行（把 `YOUR_USERNAME` 换成你的 GitHub 用户名）：

```bash
cd /Users/amorfati/.openclaw/workspace/return-rate-calculator
git add .
git commit -m "feat: 初始版本 + GitHub Actions 自动更新"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/return-rate-calculator.git
git push -u origin main
```

### 6. 验证

推送成功后：
1. 打开 https://github.com/YOUR_USERNAME/return-rate-calculator/actions
2. 可以看到「更新飞书退货率数据」workflow
3. 手动点 "Run workflow" 测试一次

---

## 文件说明

- `index.html` — 退货率计算器网页
- `feishu_rates.json` — 飞书「有货退」数据（自动生成）
- `update_feishu_rates.py` — 更新脚本（飞书 → JSON → HTML → 部署）
- `.github/workflows/update.yml` — GitHub Actions 定时任务配置

## 手动触发

需要手动更新时，在 GitHub Actions 页面点 "Run workflow" 即可。

## 修改定时时间

编辑 `.github/workflows/update.yml`，修改 `cron: '0 10 * * *'`
（格式：`分 时 日 月 星期`，10:00 UTC = 18:00 北京时间）
