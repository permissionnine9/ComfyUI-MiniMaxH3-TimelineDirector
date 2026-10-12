"""MiniMax H3 Timeline Director for ComfyUI."""

from .minimax_h3_timeline_director import (
    MiniMaxH3TimelineDirector,
    MiniMaxH3TimelineEncoder,
    MiniMaxH3OmniPromptBridge,
    MiniMaxH3TimelinePlanner,
)
from .minimax_h3_finite_segments import (
    MiniMaxH3FiniteLatentContinuation,
    MiniMaxH3FiniteAudioTrimTail,
    MiniMaxH3FiniteFrameSpool,
    MiniMaxH3FiniteFramesMaterialize,
    MiniMaxH3FiniteOutputTrim,
    MiniMaxH3FiniteSegmentFinalize,
    MiniMaxH3FiniteSegmentSampler,
    MiniMaxH3LockedAudioSlice,
    MiniMaxH3LockAudioLatent,
    MiniMaxH3LockedAudioMaster,
)

NODE_CLASS_MAPPINGS = {
    "MiniMaxH3TimelineDirector": MiniMaxH3TimelineDirector,
    "MiniMaxH3TimelinePlanner": MiniMaxH3TimelinePlanner,
    "MiniMaxH3TimelineEncoder": MiniMaxH3TimelineEncoder,
    "MiniMaxH3OmniPromptBridge": MiniMaxH3OmniPromptBridge,
    "MiniMaxH3FiniteSegmentSampler": MiniMaxH3FiniteSegmentSampler,
    "MiniMaxH3FiniteAudioTrimTail": MiniMaxH3FiniteAudioTrimTail,
    "MiniMaxH3FiniteFrameSpool": MiniMaxH3FiniteFrameSpool,
    "MiniMaxH3FiniteFramesMaterialize": MiniMaxH3FiniteFramesMaterialize,
    "MiniMaxH3FiniteOutputTrim": MiniMaxH3FiniteOutputTrim,
    "MiniMaxH3FiniteLatentContinuation": MiniMaxH3FiniteLatentContinuation,
    "MiniMaxH3FiniteSegmentFinalize": MiniMaxH3FiniteSegmentFinalize,
    "MiniMaxH3LockedAudioSlice": MiniMaxH3LockedAudioSlice,
    "MiniMaxH3LockAudioLatent": MiniMaxH3LockAudioLatent,
    "MiniMaxH3LockedAudioMaster": MiniMaxH3LockedAudioMaster,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MiniMaxH3TimelineDirector": "MiniMax H3 Timeline Director",
    "MiniMaxH3TimelinePlanner": "MiniMax H3 Material Planner",
    "MiniMaxH3TimelineEncoder": "MiniMax H3 Plan Encoder",
    "MiniMaxH3OmniPromptBridge": "MiniMax H3 Omni Media Prompt Bridge",
    "MiniMaxH3FiniteSegmentSampler": "MiniMax H3 Finite Segment Sampler",
    "MiniMaxH3FiniteAudioTrimTail": "MiniMax H3 Finite Audio Tail Trim (Internal)",
    "MiniMaxH3FiniteFrameSpool": "MiniMax H3 Finite Frame Spool (Internal)",
    "MiniMaxH3FiniteFramesMaterialize": "MiniMax H3 Finite Frames Materialize (Internal)",
    "MiniMaxH3FiniteOutputTrim": "MiniMax H3 Finite Output Trim (Internal)",
    "MiniMaxH3FiniteLatentContinuation": "MiniMax H3 Finite Latent Continuation (Internal)",
    "MiniMaxH3FiniteSegmentFinalize": "MiniMax H3 Finite Segment Finalize (Internal)",
    "MiniMaxH3LockedAudioSlice": "MiniMax H3 Locked Audio Slice (Internal)",
    "MiniMaxH3LockAudioLatent": "MiniMax H3 Lock Audio Latent (Internal)",
    "MiniMaxH3LockedAudioMaster": "MiniMax H3 Locked Audio Master (Internal)",
}

WEB_DIRECTORY = "./js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
