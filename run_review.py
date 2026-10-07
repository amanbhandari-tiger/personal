import glob
import os
import requests

OPENROUTER_API_KEY = (os.getenv("OPENROUTER_API_KEY") or "").strip()
MODEL_NAME = (os.getenv("OPENROUTER_MODEL") or "google/gemini-2.5-flash").strip()

if not MODEL_NAME:
    raise ValueError("OPENROUTER_MODEL environment variable is not set.")
    
def load_file(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as file:
            return file.read()
    return ""


def main():
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY environment variable is not set.")

    if not MODEL_NAME:
        raise ValueError("OPENROUTER_MODEL environment variable is not set.")

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
        files_payload += (
            f"\n\n--- START OF FILE: {py_file} ---\n"
            f"{content}\n"
            f"--- END OF FILE: {py_file} ---\n"
        )

    # 3. Construct prompt
    full_prompt = (
        f"{skill_content}\n\nTarget Source Code to Analyze:\n{files_payload}"
    )

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
                "content": (
                    "You are an expert static analyzer following the provided"
                    " skill.md strictly."
                ),
            },
            {
                "role": "user",
                "content": full_prompt,
            },
        ],
        "temperature": 0.1,
        "max_tokens": 4000,
    }

    print(f"Sending code to OpenRouter AI ({MODEL_NAME}) for analysis...")

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=300,
    )

    if response.status_code == 404:
        raise RuntimeError(
            f"OpenRouter could not route model '{MODEL_NAME}'. "
            "Check that OPENROUTER_MODEL is a currently available model ID on OpenRouter. "
            f"Response: {response.text}"
        )

    if not response.ok:
        print(f"OpenRouter Error ({response.status_code}): {response.text}")

    response.raise_for_status()

    result = response.json()
    choices = result.get("choices", [])
    if not choices:
        raise ValueError(f"OpenRouter response contained no choices: {result}")

    review_output = choices[0].get("message", {}).get("content", "")
    if not review_output:
        raise ValueError(
            f"OpenRouter response contained no review content: {result}"
        )

    os.makedirs("output", exist_ok=True)
    report_path = "output/code_review_report.md"

    with open(report_path, "w", encoding="utf-8") as file:
        file.write(review_output)

    print(f"Review report successfully generated at: {report_path}")


if __name__ == "__main__":
    main()