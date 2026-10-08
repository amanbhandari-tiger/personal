import glob
import os
import sys

import requests
import urllib3

# Suppress SSL warnings if verify=False is used locally
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

OPENROUTER_API_KEY = (os.getenv("OPENROUTER_API_KEY") or "").strip()
MODEL_NAME = (os.getenv("OPENROUTER_MODEL") or "openrouter/free").strip()


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
        verify=False,  # Set to True on GitHub Actions, False locally if hitting SSL cert issues
    )
    response.raise_for_status()

    result = response.json()

    # Safely extract message content
    review_output = None
    if "choices" in result and len(result["choices"]) > 0:
        review_output = result["choices"][0].get("message", {}).get("content")

    # Fallback if OpenRouter returned None or an unexpected payload structure
    if not review_output:
        print("⚠️ Warning: OpenRouter returned an empty message payload.")
        print("Raw API Response:", result)
        review_output = f"# Code Review Output\n\nUnable to retrieve review from model `{MODEL_NAME}`.\n\nRaw Response:\n```json\n{result}\n```"

    # 4. Save review output
    os.makedirs("output", exist_ok=True)
    report_path = "output/code_review_report.md"
    with open(report_path, "w", encoding="utf-8") as file:
        file.write(str(review_output))

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
