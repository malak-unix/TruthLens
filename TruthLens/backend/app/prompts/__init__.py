from app.prompts.chat_instructions import build_behavior_policy, build_context_instructions
from app.prompts.examples import FEW_SHOT_EXAMPLES
from app.prompts.system_prompt import TRUTHLENS_SYSTEM_PROMPT


__all__ = [
    "TRUTHLENS_SYSTEM_PROMPT",
    "FEW_SHOT_EXAMPLES",
    "build_behavior_policy",
    "build_context_instructions",
]
