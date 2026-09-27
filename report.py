import json
from datetime import datetime, timezone

def build_report(prompt, answer, tool_log, model, title="OpenOSINT AI V2 Report"):
    lines = [
        f"# {title}", "",
        f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"**AI model:** `{model}`", "",
        "## Scope", "", prompt, "",
        "## Key Analysis", "", answer, "",
        "## Evidence / Tool Log", ""
    ]
    if not tool_log:
        lines.append("No automated tools were executed.")
    for i, item in enumerate(tool_log, 1):
        lines += [
            f"### {i}. `{item['tool']}`", "",
            f"**Status:** {item['status']}", "",
            "**Arguments**", "", "```json",
            json.dumps(item.get("arguments", {}), ensure_ascii=False, indent=2),
            "```", "", "**Result**", "", "```text",
            item.get("result", ""), "```", ""
        ]
    lines += [
        "## Limitations", "",
        "- Public data can be incomplete, stale, or inaccurate.",
        "- A username match does not prove identity or account ownership.",
        "- IP geolocation is approximate.",
        "- A missing result is not proof that information does not exist.",
        "- Use only for authorized research, defensive work, or legitimate investigations."
    ]
    return "\n".join(lines)
