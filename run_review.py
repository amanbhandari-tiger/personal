import glob
import os
import sys

import requests
import urllib3

# Suppress SSL warnings for local environment testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

OPENROUTER_API_KEY = (os.getenv("OPENROUTER_API_KEY") or "").strip()


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
            "Could not find 'skill/code-reviewer/skill.md'. Ensure the file path is correct."
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

    # Payload with OpenRouter server-side fallback models array
    payload = {
        "model": "google/gemma-4-31b-it:free",  # Required by API: Primary model
        "models": [  # Optional: Fallback models if primary fails
            "liquid/lfm-2.5-2.6b:free",
            "nvidia/nemotron-3.5-lightning:free",
            "cohere/north-mini-code:free",
        ],
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an expert static analyzer following skill.md strictly. "
                    "Output ONLY the final markdown code review report directly without conversational preamble or internal reasoning logs."
                ),
            },
            {"role": "user", "content": full_prompt},
        ],
        "temperature": 0.1,
        "max_tokens": 4000,
    }

    print("Sending code to OpenRouter for analysis...")

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=180,
            verify=False,  # Set to False to bypass local SSL proxy issues
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as err:
        print(f"❌ API Request failed: {err}")
        sys.exit(1)

    result = response.json()

    # Safely extract message content
    review_output = None
    if "choices" in result and len(result["choices"]) > 0:
        review_output = result["choices"][0].get("message", {}).get("content")

    # Fallback check if response payload is empty or invalid
    if not review_output or not str(review_output).strip():
        print("⚠️ Warning: OpenRouter returned an empty message payload.")
        print("Raw API Response:", result)
        sys.exit(1)

    # 4. Save review output
    os.makedirs("output", exist_ok=True)
    report_path = "output/code_review_report.md"
    with open(report_path, "w", encoding="utf-8") as file:
        file.write(str(review_output))

    print(f"Review report successfully generated at: {report_path}")

    # 5. BLOCK PR MERGE ON FAILURE
    if (
        "BUILD STATUS: FAIL" in str(review_output).upper()
        or "**BUILD STATUS:** `FAIL`" in str(review_output).upper()
    ):
        print(
            "❌ AI Review failed with critical issues. Failing workflow step to block PR merge."
        )
        sys.exit(1)
    else:
        print("✅ AI Review passed successfully.")


if __name__ == "__main__":
    main()
