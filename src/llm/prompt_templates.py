"""
Compatibility shim that re-exports prompt builders split into dedicated modules.
Modules live under src/llm/prompts/ for easier maintenance:
- prompts/one_shot.py      → one-shot outline+mapping (and filtered variant)
- prompts/two_pass.py      → outline-from-plan (two-pass branch)
- prompts/writer.py        → writer prompts (structured and legacy)
"""

from typing import List

from .prompts.one_shot import (
    ONE_SHOT_SYSTEM_PROMPT,
    build_outline_and_mapping_prompt,
    build_outline_and_mapping_prompt_no_admin,
)
from .prompts.two_pass import OUTLINE_FROM_PLAN_SYSTEM_PROMPT
from .prompts.two_pass import build_mapping_prompt as _two_pass_build_mapping_prompt
from .prompts.writer import (
    WRITER_SYSTEM_PROMPT,
    build_assistant_prompt,
    build_assistant_prompt_structured,
    build_prompt_fill_content,
    build_prompt_fill_content_structured,
    build_system_prompt,
    build_system_prompt_structured,
    build_user_prompt,
)


def build_mapping_prompt(outline_json: str, slides: List[dict]) -> str:
  """Backward-compatible wrapper to the two-pass mapping prompt builder."""
  return _two_pass_build_mapping_prompt(outline_json, slides)


__all__ = [
  # one-shot
  "ONE_SHOT_SYSTEM_PROMPT",
  "build_outline_and_mapping_prompt",
  "build_outline_and_mapping_prompt_no_admin",
  # two-pass
  "OUTLINE_FROM_PLAN_SYSTEM_PROMPT",
  "build_mapping_prompt",
  # writer
  "WRITER_SYSTEM_PROMPT",
  "build_assistant_prompt",
  "build_assistant_prompt_structured",
  "build_prompt_fill_content",
  "build_prompt_fill_content_structured",
  "build_system_prompt",
  "build_system_prompt_structured",
  "build_user_prompt",
]
