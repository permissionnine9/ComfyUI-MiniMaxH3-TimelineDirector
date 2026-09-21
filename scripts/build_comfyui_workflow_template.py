"""从 UI 格式工作流生成 API 格式模板（供 money-printer 后端提交 /prompt 使用）

用法（需先启动 SSH 隧道，保证 127.0.0.1:8188 可达）：
    python3 scripts/build_comfyui_workflow_template.py

在工程根目录（ComfyUI-MiniMaxH3-TimelineDirector）下执行。读取
example_workflows 下的 UI 格式工作流（nodes/links），结合远程 ComfyUI
/object_info 的输入定义，转换为 API 格式（{node_id: {class_type, inputs}}），
输出到 example_workflows/MiniMaxH3全功能合一完全体导演台工作流_api.json。
money-printer 后端（COMFYUI_WORKFLOW_PATH）直接加载该文件。

转换规则：
- 连接输入：inputs[name] = ["<origin_node_id>", origin_slot]（links 表解析）
- widget 输入：按 required 定义顺序从 widgets_values 依序取值；
  带 control_after_generate 的输入（如 seed）消耗 2 个值（值 + 模式，模式丢弃）
- optional 未连接输入（如 TimelinePlanner.prompt_index）不写入；已连接的 optional
  输入（如 CreateVideo.audio）照常写入连线

工作流改版后（模型/步数/分辨率等）重跑本脚本即可重新生成模板。
"""
import json
import urllib.request
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent  # 工程根目录

UI_WORKFLOW_PATH = PROJECT_DIR / "example_workflows/MiniMaxH3全功能合一完全体导演台工作流.json"
OUTPUT_PATH = PROJECT_DIR / "example_workflows/MiniMaxH3全功能合一完全体导演台工作流_api.json"
COMFYUI_BASE_URL = "http://127.0.0.1:8188"


def fetch_object_info() -> dict:
    with urllib.request.urlopen(f"{COMFYUI_BASE_URL}/object_info", timeout=15) as resp:
        return json.loads(resp.read())


def convert(ui: dict, object_info: dict) -> dict:
    # links: [link_id, origin_id, origin_slot, target_id, target_slot, type]
    link_map = {link[0]: (link[1], link[2]) for link in ui["links"]}

    api_workflow = {}
    for node in ui["nodes"]:
        class_type = node["type"]
        definition = object_info.get(class_type)
        if definition is None:
            raise KeyError(f"远程 ComfyUI 无节点 {class_type}，请先安装对应 custom node")

        connected = {
            inp["name"]: link_map[inp["link"]]
            for inp in node.get("inputs", [])
            if inp.get("link") is not None
        }

        inputs = {}
        widget_values = list(node.get("widgets_values", []))
        required = definition["input"].get("required", {})
        for name, spec in required.items():
            if name in connected:
                origin_id, origin_slot = connected[name]
                inputs[name] = [str(origin_id), origin_slot]
                continue
            if not widget_values:
                raise ValueError(f"节点 {class_type}(id={node['id']}) 输入 {name} 无对应 widget 值")
            value = widget_values.pop(0)
            # control_after_generate 的 widget 会序列化成 [值, 模式] 两个值，模式丢弃
            options = spec[1] if len(spec) > 1 and isinstance(spec[1], dict) else {}
            if options.get("control_after_generate"):
                widget_values.pop(0)
            inputs[name] = value

        # optional 输入：已连线的必须导出（如 CreateVideo.audio，丢线会导致成品无音轨），
        # 未连线的省略即用默认值，不写入
        optional = definition["input"].get("optional", {}) or {}
        for name in optional:
            if name in connected:
                origin_id, origin_slot = connected[name]
                inputs[name] = [str(origin_id), origin_slot]

        # 剩余未消费的 widget 值属于 optional 输入（如 bit_depth/动态 combo 子选项），
        # API 格式下省略即用默认值，仅提示不阻断
        if widget_values:
            print(f"   ⚠️ 节点 {class_type}(id={node['id']}) 未消费 widget 值（optional 默认值兜底）: {widget_values}")

        api_workflow[str(node["id"])] = {"class_type": class_type, "inputs": inputs}
    return api_workflow


def main():
    if not UI_WORKFLOW_PATH.exists():
        raise FileNotFoundError(f"UI 工作流不存在: {UI_WORKFLOW_PATH}")

    ui = json.loads(UI_WORKFLOW_PATH.read_text(encoding="utf-8"))
    object_info = fetch_object_info()
    api_workflow = convert(ui, object_info)

    OUTPUT_PATH.write_text(json.dumps(api_workflow, ensure_ascii=False, indent=2), encoding="utf-8")

    # 摘要
    planner = next(
        (n for n in api_workflow.values() if n["class_type"] == "MiniMaxH3TimelinePlanner"), None
    )
    print(f"✅ 已生成 {OUTPUT_PATH.name}（{len(api_workflow)} 个节点）")
    if planner:
        has_timeline = isinstance(planner["inputs"].get("timeline_data"), str)
        print(f"   MiniMaxH3TimelinePlanner.timeline_data 为字符串输入: {has_timeline}")


if __name__ == "__main__":
    main()
