import json
from groq import Groq
from tools import TOOL_FUNCTIONS, TOOL_SCHEMAS, configure

SYSTEM_PROMPT = """
You are OpenOSINT AI V2, an evidence-first assistant for authorized OSINT and defensive research.
Use only public or explicitly authorized information. Prefer passive reconnaissance.
Never invent tool results. A username match is not proof of identity or ownership.
IP geolocation is approximate. Do not bypass authentication, exploit systems, brute force credentials,
access private accounts, or provide instructions for obtaining secrets.
Use tools when useful. Clearly separate observed evidence, inference, and unknowns.
End investigations with Scope, Key Findings, Evidence/Tools, Limitations, and legitimate next steps.
"""

class OSINTAgent:
    def __init__(self, api_key, model, max_iterations=6, timeout=15, hibp_api_key=None):
        self.client = Groq(api_key=api_key)
        self.model = model
        self.max_iterations = max(1, min(int(max_iterations), 10))
        configure(timeout, hibp_api_key)

    def run(self, prompt):
        messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}]
        log = []
        for _ in range(self.max_iterations):
            response = self.client.chat.completions.create(
                model=self.model, messages=messages, tools=TOOL_SCHEMAS,
                tool_choice="auto", temperature=0.1, max_completion_tokens=4500
            )
            message = response.choices[0].message
            if not message.tool_calls:
                return {"answer": message.content or "No final answer returned.", "tool_log": log}
            messages.append(message)
            for call in message.tool_calls:
                name = call.function.name
                try:
                    args = json.loads(call.function.arguments or "{}")
                except json.JSONDecodeError:
                    args, result, status = {}, {"error": "Invalid JSON tool arguments."}, "ERROR"
                else:
                    fn = TOOL_FUNCTIONS.get(name)
                    if not fn:
                        result, status = {"error": f"Unknown tool: {name}"}, "ERROR"
                    else:
                        try:
                            result, status = fn(**args), "OK"
                        except Exception as e:
                            result, status = {"error": f"{type(e).__name__}: {str(e)[:600]}"}, "ERROR"
                text = json.dumps(result, ensure_ascii=False, indent=2)
                if len(text) > 18000:
                    text = text[:18000] + "\n...[truncated]"
                log.append({"tool": name, "status": status, "arguments": args, "result": text})
                messages.append({"role": "tool", "tool_call_id": call.id, "name": name, "content": text})
        messages.append({"role": "user", "content": "Stop tool use and summarize only the evidence already collected."})
        final = self.client.chat.completions.create(model=self.model, messages=messages, temperature=0.1, max_completion_tokens=3500)
        return {"answer": final.choices[0].message.content or "No final answer returned.", "tool_log": log}
