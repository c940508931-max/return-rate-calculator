#!/usr/bin/env python3
"""
飞书退货率数据更新脚本
用法: python3 update_feishu_rates.py
更新完成后会自动部署到 Firebase Hosting
"""
import urllib.request
import urllib.parse
import json
import re
import sys
import os

FEISHU_APP_ID = "cli_a928e28f0ff6dbca"
FEISHU_APP_SECRET = "nc7WEIwxiLrB72ID0T4RygVp45CuNQcj"
SPREADSHEET_TOKEN = "XheSscvcBhMURPtzrxocDp3NnFg"
SHEET_ID = "5c7d0c"
HTML_FILE = os.path.join(os.path.dirname(__file__), "index.html")


def get_feishu_token():
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    data = json.dumps({"app_id": FEISHU_APP_ID, "app_secret": FEISHU_APP_SECRET}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        result = json.load(resp)
    if result.get("code") != 0:
        raise Exception(f"获取飞书 Token 失败: {result.get('msg')}")
    return result["tenant_access_token"]


def fetch_all_return_rates(token):
    all_rates = {}
    batch_size = 500
    start_row = 2

    while True:
        end_row = start_row + batch_size - 1
        range_str = f"{SHEET_ID}!B{start_row}:M{end_row}"
        api_url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{SPREADSHEET_TOKEN}/values/{urllib.parse.quote(range_str)}?valueRenderOption=FormattedValue"

        req = urllib.request.Request(api_url, headers={"Authorization": f"Bearer {token}"})
        with urllib.request.urlopen(req) as resp:
            result = json.load(resp)

        if result.get("code") != 0:
            print(f"  ⚠ API 返回错误: {result.get('msg')}，停止在第 {start_row} 行")
            break

        rows = result.get("data", {}).get("valueRange", {}).get("values", [])
        if not rows:
            break

        count = 0
        for r in rows:
            if r and len(r) > 11 and r[0] and r[11] and "%" in str(r[11]):
                code = str(r[0]).strip()
                try:
                    pct = float(str(r[11]).replace("%", ""))
                    all_rates[code] = pct
                    count += 1
                except ValueError:
                    pass

        print(f"  行 {start_row}-{end_row}: 获得 {count} 条有效数据（累计 {len(all_rates)} 条）")

        if len(rows) < batch_size:
            break
        start_row = end_row + 1

    return all_rates


def build_js_object(rates):
    lines = ["var FEISHU_RETURN_RATES = {"]
    for k in sorted(rates.keys()):
        lines.append(f'"{k}":{rates[k]},')
    lines.append("};")
    return "\n".join(lines)


def update_html_file(html_path, new_obj_str, total_count):
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 找到 FEISHU_RETURN_RATES 的起止位置
    start = content.find("var FEISHU_RETURN_RATES = {")
    end = content.find("};", start) + 2
    if start == -1 or end == -1:
        raise Exception("未找到 FEISHU_RETURN_RATES 在 HTML 文件中的位置")

    # 替换
    new_content = content[:start] + new_obj_str + content[end:]

    # 更新状态栏文字
    new_content = re.sub(r"✓ 飞书退货率已就绪（[^）]+）",
                         f"✓ 飞书退货率已就绪（共 {total_count} 条）",
                         new_content)
    new_content = re.sub(r"（共\d+条）", f"（共{total_count}条）", new_content)

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"\n✅ HTML 文件已更新（共 {total_count} 条）")


def save_json_file(rates, json_path, updated_time):
    import json as jsonmod
    output = {
        "meta": {
            "updated": updated_time,
            "count": len(rates),
            "source": "5c7d0c"
        },
        "rates": rates
    }
    with open(json_path, "w", encoding="utf-8") as f:
        jsonmod.dump(output, f, ensure_ascii=False, separators=(',', ':'))
    print(f"✅ feishu_rates.json 已生成（共 {len(rates)} 条）")


def deploy():
    print("\n🚀 正在部署到 Firebase Hosting...")
    result = os.system("cd " + os.path.dirname(os.path.abspath(__file__)) + " && firebase deploy --only hosting 2>&1")
    if result != 0:
        print("⚠️  部署失败，请检查 Firebase CLI 配置")
        return False
    print("✅ 部署完成！")
    return True


def main():
    print("=" * 50)
    print("🦈 飞书退货率数据更新脚本")
    print("=" * 50)

    print("\n📡 正在获取飞书 Access Token...")
    token = get_feishu_token()
    print("  ✅ Token 获取成功")

    print("\n📥 正在拉取飞书表格数据（自动翻页）...")
    rates = fetch_all_return_rates(token)
    print(f"\n  共获取 {len(rates)} 条有货退数据")

    if len(rates) == 0:
        print("❌ 未获取到任何数据，退出")
        sys.exit(1)

    print("\n🔧 正在更新 HTML 文件...")
    js_obj = build_js_object(rates)
    update_html_file(HTML_FILE, js_obj, len(rates))

    print("\n🔧 正在生成 feishu_rates.json...")
    import time
    json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "feishu_rates.json")
    save_json_file(rates, json_path, time.strftime("%Y-%m-%d %H:%M"))

    # 检查 --yes 参数（GitHub Actions 模式：自动部署）
    auto_deploy = '--yes' in sys.argv
    if not auto_deploy:
        choice = input("\n是否立即部署到 Firebase？（y/n，默认 y）: ").strip().lower()
        if choice == 'n':
            print("跳过部署。请手动运行: cd " + os.path.dirname(os.path.abspath(__file__)) + " && firebase deploy --only hosting")
            print("\n✅ 全部完成！")
            return
    if auto_deploy:
        print("\n🚀 [Auto] 自动部署模式，跳过确认")
    deploy()
    print("\n✅ 全部完成！")


if __name__ == "__main__":
    main()
