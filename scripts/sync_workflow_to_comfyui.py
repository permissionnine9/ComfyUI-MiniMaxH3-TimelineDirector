"""把最近一次「导入到 ComfyUI」的 timeline_data 写回服务器 UI 工作流

money-printer 的导入链路走 API 提交（POST /prompt），ComfyUI 界面上的工作流
文件不会被更新，所以「MiniMax H3 素材规划工作台」看不到已导入的素材/提示词。
本脚本读取 money-printer 会话的 comfyui_import 暂存，把 timeline_data 注入
源 UI 工作流后通过 ComfyUI userdata API 写到服务器（界面上打开/刷新该工作流
即可看到）。

用法（需 SSH 隧道，在工程根目录执行）：
    python3 scripts/sync_workflow_to_comfyui.py [session_id]

省略 session_id 时取最近一次导入的会话。此逻辑后续会集成到 money-printer
导入链路（prepare_import），脚本保留作手动同步/调试入口。
"""
import json
import sqlite3
import sys
import urllib.parse
import urllib.request
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent      # 本工程根目录
MONEY_PRINTER_DIR = PROJECT_DIR.parent.parent             # money-printer 项目根

UI_WORKFLOW_PATH = PROJECT_DIR / "example_workflows/MiniMaxH3全功能合一完全体导演台工作流.json"
DB_PATH = MONEY_PRINTER_DIR / "data/sessions.db"
COMFYUI_BASE_URL = "http://127.0.0.1:8188"
# 写到服务器的独立工作流文件（不覆盖原工作流，避免与界面手动编辑冲突）
TARGET_FILE = "workflows/MiniMaxH3导演台-money-printer最新导入.json"


def latest_import(session_id: str | None) -> tuple[str, dict]:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT session_id, result_data FROM step_results WHERE step_name='comfyui_import'"
        " ORDER BY completed_at DESC"
    ).fetchall()
    if session_id:
        rows = [r for r in rows if r[0] == session_id] or rows
    if not rows:
        raise SystemExit("无 comfyui_import 暂存记录")
    data = json.loads(rows[0][1])
    return rows[0][0], data


def inject_ui_workflow(timeline_data: dict) -> dict:
    ui = json.loads(UI_WORKFLOW_PATH.read_text(encoding="utf-8"))
    replaced = 0
    for node in ui["nodes"]:
        if node.get("type") != "MiniMaxH3TimelinePlanner":
            continue
        for i, value in enumerate(node.get("widgets_values", [])):
            # timeline_data widget 是可解析出 segmentConfig 的 JSON 字符串
            if isinstance(value, str) and value.strip().startswith("{"):
                try:
                    parsed = json.loads(value)
                except json.JSONDecodeError:
                    continue
                if isinstance(parsed, dict) and "segmentConfig" in parsed:
                    node["widgets_values"][i] = json.dumps(timeline_data, ensure_ascii=False)
                    replaced += 1
    if not replaced:
        raise SystemExit("UI 工作流中未找到 MiniMaxH3TimelinePlanner 的 timeline_data widget")
    return ui


def push_to_comfyui(content: str, target_file: str) -> None:
    encoded = urllib.parse.quote(target_file, safe="")
    req = urllib.request.Request(
        f"{COMFYUI_BASE_URL}/api/userdata/{encoded}?full_info=true",
        data=content.encode("utf-8"),
        headers={"Content-Type": "application/json", "Comfy-User": "default"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        print(f"已写入服务器: {json.loads(resp.read())['path']}")


def main():
    session_id = sys.argv[1] if len(sys.argv) > 1 else None
    sid, data = latest_import(session_id)
    timeline = data.get("timeline_data")
    if not timeline:
        raise SystemExit("暂存记录中无 timeline_data")
    ui = inject_ui_workflow(timeline)
    push_to_comfyui(json.dumps(ui, ensure_ascii=False), TARGET_FILE)
    cfg = timeline.get("segmentConfig", {})
    print(
        f"会话 {sid[:8]}...：{cfg.get('count')} 段 / {len(timeline.get('images', []))} 图 / "
        f"{len(timeline.get('audios', []))} 音频 —— 在 ComfyUI 界面打开"
        f"「{Path(TARGET_FILE).name}」即可查看"
    )


if __name__ == "__main__":
    main()
