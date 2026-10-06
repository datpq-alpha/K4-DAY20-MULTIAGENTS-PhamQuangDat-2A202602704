"""GUIDE Phần 1 - Định nghĩa subagent (tác tử con).   >>> SINH VIÊN CÀI ĐẶT <<<

Pseudo-code: guides/pseudocode/02_subagents.md
Kiểm tra:    pytest tests/test_02_agent.py
"""


def get_subagents() -> list[dict]:
    """Trả về danh sách subagent (ít nhất 2, tên khác nhau).

    Mỗi phần tử là một dict có các khóa bắt buộc:
      "name":          tên duy nhất (chữ thường, có thể có dấu gạch ngang)
      "description":   khi nào tác tử chính nên giao việc cho subagent này (viết như một hướng dẫn hành động)
      "system_prompt": chỉ dẫn cho subagent
    Gợi ý vai trò: explorer (đọc và báo cáo), implementer (thực hiện), reviewer (kiểm tra độc lập).
    """
    # raise NotImplementedError("TODO: cài đặt get_subagents (xem guides/pseudocode/02_subagents.md)")
    return [
        {
            "name": "explorer",
            "description": (
                "Use when the task requires inspecting documentation, source files, data samples, "
                "or repository structure before implementation; report verified facts and do not modify files."
            ),
            "system_prompt": (
                "You are a careful repository explorer. Read the relevant files, verify claims with evidence, "
                "and return a concise report with paths and important constraints. Do not modify any file."
            ),
        },
        {
            "name": "implementer",
            "description": (
                "Use when a non-trivial change must be implemented and validated with focused tests or scripts."
            ),
            "system_prompt": (
                "You are an implementation specialist. Follow every supplied task rule, make only necessary "
                "changes, run focused validation, and report the files changed and the exact test results."
            ),
        },
        {
            "name": "reviewer",
            "description": (
                "Use after implementation when the result needs an independent check against requirements, "
                "edge cases, and test evidence; review without editing files."
            ),
            "system_prompt": (
                "You are an independent reviewer. Inspect the requested result against all stated requirements, "
                "look for edge cases and regressions, run relevant checks when useful, and report findings. "
                "Do not modify files."
            ),
        },
    ]
