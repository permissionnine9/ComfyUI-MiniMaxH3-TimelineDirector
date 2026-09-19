 你的所有诉求（外部上传图片/音频、指定每段时长、段间
  overlap、每段参考图/参考声音/提示词）都能覆盖。核心原因有两个：

  为什么可行
  
  1. 节点后端的全部输入就是一个 JSON 字符串 timeline_data

  前端时间轴 UI 只是这个 JSON 的编辑器（js/timeline_director.js:320)。执行时
  MiniMaxH3TimelinePlanner.execute() 只读 timeline_data
  字符串（minimax_h3_timeline_director.py:1598)，完全不依赖浏览器。所以外部系统只要按同样格式构造好这个
  JSON，通过 ComfyUI 原生 POST /prompt 提交工作流即可，JS 不运行也没关系。

  2. ComfyUI 自带两个 HTTP 接口刚好够用

  - POST /upload/image(multipart 表单，图片/音频/视频都能传）→ 返回 {name, subfolder}，文件落进 input 目录
  - POST /prompt(API 格式工作流 JSON)→ 排队执行；再用 WebSocket /ws 或 GET /history/{prompt_id} 拿结果

  你的每项需求 → timeline_data 字段映射

  ┌────────────────────┬─────────────────────────────────────────────────────────────────────────────────┐
  │        需求        │                                      字段                                       │
  ├────────────────────┼─────────────────────────────────────────────────────────────────────────────────┤
  │ 上传图片/音频/视频 │ 先走 /upload/image，然后把返回的路径填进 images[].file / audios[].file /        │
  │                    │ videoClips[].file（相对 input 目录）                                            │
  ├────────────────────┼─────────────────────────────────────────────────────────────────────────────────┤
  │ 每段时长           │ segmentConfig.segments[i].startFrame / endFrame(24fps，时长=(end-start)/24 秒） │
  ├────────────────────┼─────────────────────────────────────────────────────────────────────────────────┤
  │ 段间 overlap       │ 不用单独传，由窗口自然重叠算出：overlap = 前一段endFrame − 本段startFrame       │
  ├────────────────────┼─────────────────────────────────────────────────────────────────────────────────┤
  │ 每段参考图         │ images 数组定义素材（带 id),segments[i].images: ["id1", ...] 按 id 分配         │
  ├────────────────────┼─────────────────────────────────────────────────────────────────────────────────┤
  │ 每段参考声音       │ audios 数组定义素材，segments[i].audios: ["id1", ...] 分配；audioMode 可选      │
  │                    │ reference/locked                                                                │
  ├────────────────────┼─────────────────────────────────────────────────────────────────────────────────┤
  │ 每段提示词         │ segments[i].prompt（要么每段都写，要么都不写走 globalPrompt，不能混）           │
  └────────────────────┴─────────────────────────────────────────────────────────────────────────────────┘

  必须遵守的对齐规则（后端会校验）

  构造 startFrame/endFrame 时注意（minimax_h3_finite_segments.py:289-303):

  - 每段长度必须是 5 + 17×n 帧(n≥0)，最长 3592 帧（150 秒）
  - 第一段必须从帧 0 开始；段与段之间不能有空隙、必须前进
  - overlap 为 0，或满足 overlap % 17 == 5(即 5、22、39…帧），且小于相邻两段长度
  - 参考图 ≤9、参考音频 ≤3、参考视频 ≤3
  - segmentConfig.mode 必须为 "timeline",count 与 segments 数组长度一致

调用流程示例

  jsonc
  // 1) POST /upload/image 上传 seg1.png、voice.wav → 得到文件名
  // 2) 组装 timeline_data,塞进工作流里 MiniMaxH3TimelinePlanner 节点的 timeline_data 输入
  {
    "version": 5, "fps": 24,
    "globalPrompt": "",
    "selection": {"start": 0, "duration": 9},
    "videoAudioEnabled": true,
    "videoClips": [],
    "images": [
      {"id": "img1", "file": "seg1.png"},
      {"id": "img2", "file": "seg2.png"}
    ],
    "audios": [
      {"id": "aud1", "file": "voice.wav", "audioMode": "reference"}
    ],
    "segmentConfig": {
      "count": 2, "activeIndex": 0, "mode": "timeline",
      "segments": [
        // 段1:0~120帧 = 5秒
        {"startFrame": 0,   "endFrame": 120, "images": ["img1"], "audios": ["aud1"], "prompt": "段1提示词"},
        // 段2:98~218帧 = 5秒;overlap = 120-98 = 22帧(22%17=5 ✓)
        {"startFrame": 98,  "endFrame": 218, "images": ["img2"], "audios": ["aud1"], "prompt": "段2提示词"}
      ]
    }
        // 段1:0~120帧 = 5秒
        {"startFrame": 0,   "endFrame": 120, "images": ["img1"], "audios": ["aud1"], "prompt": "段1提示词"},
        // 段2:98~218帧 = 5秒;overlap = 120-98 = 22帧(22%17=5 ✓)
        {"startFrame": 98,  "endFrame": 218, "images": ["img2"], "audios": ["aud1"], "prompt": "段2提示词"}
      ]
    }
  }
  // 3) POST /prompt,工作流里其余节点(CLIP/VAE/Sampler等)照你现有导出的 API 格式工作流填