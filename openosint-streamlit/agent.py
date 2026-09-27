import json
from typing import Any, Dict

from groq import Groq

from tools import TOOL_SCHEMAS, TOOL_FUNCTIONS


SYSTEM_PROMPT = """
You are OpenOSINT AI Agent, an assistant for authorized OSINT and defensive security research.

Operating rules:
1. Work only with public, non-authenticated information and user-authorized targets.
2. Do not help bypass authentication, access private accounts, stalk individuals, or obtain secrets.
3. Prefer passive reconnaissance and publicly available metadata.
4. Never invent tool results. If a tool returns an error or no result, say so.
5. Use tools when they materially improve the investigation.
6. You may call multiple tools and reason over their returned results.
7. Keep conclusions evidence-based. Clearly distinguish observed data, inference, and unknowns.
8. When the user asks for an investigation, summarize:
   - Scope
   - Sources/tools used
   - Key findings
   - Limitations
   - Recommended defensive next steps
9. Do not claim that a person owns an account merely because a username exists on a website.
10. Treat third-party public data as potentially stale or incorrect.
"""


class OSINTAgent:
    def __init__(
        self,
        api_key: str,
        model: str = "openai/gpt-oss-120b",
        max_iterations: int = 5,
        timeout: int = 15,
        hibp_api_key: str | None = None,
    ):
        self.client = Groq(api_key=api_key)
        self.model = model
        self.max_iterations = max_iterations
        self.timeout = timeout
        self.hibp_api_key = hibp_api_key

        # Give the HIBP key to the tool layer without putting it in prompts.
        from tools import configure
        configure(timeout=timeout, hibp_api_key=hibp_api_key)

    def run(self, user_prompt: str) -> Dict[str, Any]:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        tool_log = []

        for _ in range(self.max_iterations):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=TOOL_SCHEMAS,
                tool_choice="auto",
                temperature=0.1,
                max_completion_tokens=4000,
            )

            message = response.choices[0].message

            if not message.tool_calls:
                answer = message.content or "The agent returned no textual answer."
                return {"answer": answer, "tool_log": tool_log}

            messages.append(message)

            for call in message.tool_calls:
                name = call.function.name
                raw_args = call.function.arguments or "{}"

                try:
                    args = json.loads(raw_args)
                except json.JSONDecodeError:
                    args = {}
                    tool_result = {"error": "The model generated invalid JSON arguments."}
                    tool_log.append({
                        "tool": name,
                        "status": "ERROR",
                        "arguments": raw_args,
                        "result": json.dumps(tool_result),
                    })
                    messages.append({
                        "role": "tool",
                        "tool_call_id": call.id,
                        "name": name,
                        "content": json.dumps(tool_result),
                    })
                    continue

                function = TOOL_FUNCTIONS.get(name)

                if not function:
                    result = {"error": f"Unknown tool: {name}"}
                    status = "ERROR"
                else:
                    try:
                        result = function(**args)
                        status = "OK"
                    except Exception as exc:
                        result = {
                            "error": f"{type(exc).__name__}: {str(exc)[:500]}"
                        }
                        status = "ERROR"

                result_text = json.dumps(result, ensure_ascii=False, indent=2)

                # Keep tool results bounded so a public endpoint cannot consume
                # the entire model context.
                if len(result_text) > 18000:
                    result_text = result_text[:18000] + "\n...[truncated]"

                tool_log.append({
                    "tool": name,
                    "status": status,
                    "arguments": args,
                    "result": result_text,
                })

                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "name": name,
                    "content": result_text,
                })

        # If the model keeps requesting tools, make one final response without
        # tools so the user gets a bounded answer instead of an endless loop.
        messages.append({
            "role": "user",
            "content": (
                "Stop tool execution now. Provide the best evidence-based "
                "summary using only the tool results already returned."
            ),
        })

        final = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.1,
            max_completion_tokens=3000,
        )

        return {
            "answer": final.choices[0].message.content or "No final answer returned.",
            "tool_log": tool_log,
        }
