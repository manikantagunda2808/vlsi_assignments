import os
import sys
import json
import yaml
import requests

GROQ_API_KEY = os.environ["GROQ_API_KEY"]
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
REPO = os.environ["GITHUB_REPOSITORY"]
PR_NUMBER = os.environ["PR_NUMBER"]
PR_DESCRIPTION = os.environ["PR_DESCRIPTION"]
CHANGED_FILES = os.environ["CHANGED_FILES"].split(",")

def detect_review_type():
    desc = PR_DESCRIPTION.upper()
    if "[RTL]" in desc:
        return "rtl"
    elif "[TB]" in desc:
        return "tb"
    elif "[UVM]" in desc:
        return "uvm"
    else:
        return None

def load_rules(review_type):
    rules_path = f"rules/{review_type}_rules.yaml"
    with open(rules_path, "r") as f:
        data = yaml.safe_load(f)
    rules_text = ""
    for r in data["rules"]:
        rules_text += f"- [{r['id']}] ({r['severity'].upper()}) {r['rule']}\n"
    return rules_text

def load_code_files():
    code = ""
    for filepath in CHANGED_FILES:
        filepath = filepath.strip()
        if filepath.endswith((".v", ".sv", ".uvm")):
            if os.path.exists(filepath):
                with open(filepath, "r") as f:
                    code += f"\n\n### File: {filepath}\n```\n{f.read()}\n```"
    return code

def call_groq(rules, code, review_type):
    system_prompt = f"""You are a strict VLSI code reviewer for {review_type.upper()} code.
Review the submitted code against the rules below and return ONLY a JSON object.

Rules:
{rules}

Return this exact JSON format:
{{
  "score": <number 0-10>,
  "violations": [
    {{"rule_id": "XXXXX", "message": "...", "file": "...", "line": "approx line number or N/A"}}
  ],
  "warnings": [
    {{"rule_id": "XXXXX", "message": "...", "file": "...", "line": "approx line number or N/A"}}
  ],
  "passed": ["brief description of what passed"],
  "summary": "2-3 sentence overall summary"
}}

Be specific. Reference actual code. Do not add any text outside the JSON."""

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Review this code:\n{code}"}
            ],
            "temperature": 0.1
        }
    )
    return response.json()["choices"][0]["message"]["content"]

def format_comment(result, review_type):
    score = result["score"]
    emoji = "✅" if score >= 7 else "⚠️" if score >= 5 else "❌"

    comment = f"## {emoji} AI Code Review — {review_type.upper()}\n\n"
    comment += f"**Score: {score}/10**\n\n"

    if result["violations"]:
        comment += "### ❌ Violations (must fix before merge)\n"
        for v in result["violations"]:
            comment += f"- `[{v['rule_id']}]` **{v['file']}** (line {v['line']}): {v['message']}\n"
        comment += "\n"

    if result["warnings"]:
        comment += "### ⚠️ Warnings\n"
        for w in result["warnings"]:
            comment += f"- `[{w['rule_id']}]` **{w['file']}** (line {w['line']}): {w['message']}\n"
        comment += "\n"

    if result["passed"]:
        comment += "### ✅ Passed\n"
        for p in result["passed"]:
            comment += f"- {p}\n"
        comment += "\n"

    comment += f"### 📋 Summary\n{result['summary']}\n\n"
    comment += "---\n*Reviewed by VLSI Review Bot · Rules updated in `rules/` folder*"
    return comment

def post_comment(comment):
    url = f"https://api.github.com/repos/{REPO}/issues/{PR_NUMBER}/comments"
    requests.post(
        url,
        headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        },
        json={"body": comment}
    )

def main():
    review_type = detect_review_type()
    if not review_type:
        print("No [RTL]/[TB]/[UVM] tag found in PR description. Skipping review.")
        sys.exit(0)

    rules = load_rules(review_type)
    code = load_code_files()

    if not code.strip():
        print("No .v/.sv/.uvm files found in PR. Skipping.")
        sys.exit(0)

    raw = call_groq(rules, code, review_type)

    clean = raw.strip().replace("```json", "").replace("```", "").strip()
    result = json.loads(clean)

    comment = format_comment(result, review_type)
    post_comment(comment)
    print("Review posted successfully.")

if __name__ == "__main__":
    main()
