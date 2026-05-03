import os
from pathlib import Path

from google import genai
from dotenv import load_dotenv


def main():
    env_path = Path(__file__).resolve().with_name(".env")
    loaded = load_dotenv(dotenv_path=env_path, override=True)
    # Windows consoles often default to cp1252 and can crash on Unicode paths; print escaped.
    safe_env_path = env_path.as_posix().encode("unicode_escape").decode("ascii")
    print(f"Loaded .env from: {safe_env_path} (loaded={loaded})")

    key = (os.environ.get("GEMINI_API_KEY") or "").strip()
    if not key:
        raise SystemExit("GEMINI_API_KEY is not set (check your .env).")

    print(f"GEMINI_API_KEY fingerprint: prefix={key[:6]!r}, suffix={key[-4:]!r}, len={len(key)}")

    client = genai.Client(api_key=key)
    resp = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Reply with exactly: OK",
    )
    print("Gemini response:")
    print(resp.text if hasattr(resp, "text") else resp)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("Gemini request failed:")
        try:
            print(repr(e))
        except Exception:
            print(str(e).encode("unicode_escape").decode("ascii"))
        raise

