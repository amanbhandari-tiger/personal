import glob
import os
import sys

import requests

OPENROUTER_API_KEY = (os.getenv("OPENROUTER_API_KEY") or "").strip()
MODEL_NAME = (os.getenv("OPENROUTER_MODEL") or "google/gemini-2.5-flash").strip()


def load_file(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as file:
            return file.read()
    return ""


def main():
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY environment variable is not set.")

    # 1. Load review guidelines
    skill_content = load_file("skill/code-reviewer/skill.md")
    if not skill_content:
        raise FileNotFoundError(
            "Could not find 'skill/code-reviewer/skill.md'. Ensure the path is correct."
        )

    # 2. Collect Python source files
    files_payload = ""
    for py_file in glob.glob("*.py"):
        if py_file == "run_review.py":
            continue
        content = load_file(py_file)
        files_payload += f"\n\n--- START OF FILE: {py_file} ---\n{content}\n--- END OF FILE: {py_file} ---\n"

    # 3. Construct prompt
    full_prompt = f"{skill_content}\n\nTarget Source Code to Analyze:\n{files_payload}"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/code-reviewer-action",
        "X-Title": "Automated AI Code Reviewer",
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": "You are an expert static analyzer following skill.md strictly.",
            },
            {"role": "user", "content": full_prompt},
        ],
        "temperature": 0.1,
        "max_tokens": 4000,
    }

    print(f"Sending code to OpenRouter ({MODEL_NAME}) for analysis...")
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=300,
    )
    response.raise_for_status()

    result = response.json()
    review_output = result["choices"][0]["message"]["content"]

    # 4. Save review output
    os.makedirs("output", exist_ok=True)
    report_path = "output/code_review_report.md"
    with open(report_path, "w", encoding="utf-8") as file:
        file.write(review_output)

    print(f"Review report successfully generated at: {report_path}")

    # 5. BLOCK PR MERGE ON FAILURE
    if (
        "BUILD STATUS: FAIL" in review_output.upper()
        or "**BUILD STATUS:** `FAIL`" in review_output.upper()
    ):
        print(
            "❌ AI Review failed with critical issues. Failing workflow step to block PR merge."
        )
        sys.exit(1)
    else:
        print("✅ AI Review passed successfully.")


if __name__ == "__main__":
    main()
