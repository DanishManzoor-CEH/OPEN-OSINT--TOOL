from datetime import datetime, timezone


def build_markdown_report(prompt, answer, tool_log, model):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    lines = [
        "# OpenOSINT AI Agent Report",
        "",
        f"**Generated:** {now}",
        f"**Model:** `{model}`",
        "",
        "## Scope / User Request",
        "",
        prompt,
        "",
        "## AI Analysis",
        "",
        answer,
        "",
        "## Tool Execution Log",
        "",
    ]

    if not tool_log:
        lines.append("No tools were executed.")
    else:
        for index, item in enumerate(tool_log, 1):
            lines.extend([
                f"### {index}. `{item['tool']}`",
                "",
                f"**Status:** {item['status']}",
                "",
                "**Arguments:**",
                "```json",
                json_safe(item.get("arguments", {})),
                "```",
                "",
                "**Result:**",
                "```text",
                item.get("result", ""),
                "```",
                "",
            ])

    lines.extend([
        "## Limitations",
        "",
        "- Results come from public or explicitly configured third-party services.",
        "- Public profile presence does not prove identity or account ownership.",
        "- IP geolocation is approximate and should not be treated as precise physical location.",
        "- Absence of a result does not prove absence of the underlying information.",
        "- This report should be used only for authorized security research, defensive work, or legitimate investigations.",
    ])

    return "\n".join(lines)


def json_safe(value):
    import json
    return json.dumps(value, ensure_ascii=False, indent=2)
