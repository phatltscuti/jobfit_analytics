import os
import json
import sys
import openai
from dotenv import load_dotenv


def main():
    # load .env from project root
    load_dotenv()
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        print("ERROR: OPENAI_API_KEY is not set in environment.")
        sys.exit(1)

    openai.api_key = key
    # Print masked key for verification
    try:
        masked = key[:6] + "..." + key[-4:] if len(key) > 12 else "(short)"
        print("KEY:", masked)
    except Exception:
        pass
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say OK"}],
            max_tokens=5,
            temperature=0.0,
            timeout=15,
        )
        text = (resp.choices[0].message.content or "").strip()
        print("OK:" if text else "NO_TEXT:", text)
        sys.exit(0)
    except Exception as e:
        print("OPENAI_ERROR:", str(e))
        sys.exit(2)


if __name__ == "__main__":
    main()


