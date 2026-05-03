import argparse
import json
import os
import re
import sqlite3
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types


ANALYSIS_PROMPT = """You are an AI machinery condition inspector. Analyze the machine shown in the image.

Tasks:
1. Identify all visible issues such as rust, dents, scratches, broken parts, worn tires, paint fade, leaks, or structural damage.
2. Based on your analysis, generate a "Condition Score" from 0 to 10:
   - 9–10: Excellent condition, almost no damage
   - 7–8: Good condition, minor cosmetic issues
   - 5–6: Moderate condition, noticeable wear or rust
   - 3–4: Poor condition, obvious damage, maintenance needed
   - 0–2: Very bad condition, unsafe or unusable
3. Provide a detailed explanation of why you gave that score.
4. Keep output in structured JSON format:

{
  "condition_score": <number>,
  "issues_found": [list of problems - keep each very short, max 5 items],
  "summary": "Short explanation of condition (one sentence)",
  "recommendation": "What the renter should know (one sentence)"
}

Analyze only what is visible in the image. Keep issues_found list items very brief (3-5 words each)."""


def _detect_mime(path: Path) -> str:
    ext = path.suffix.lower()
    return {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }.get(ext, "image/jpeg")


def _pick_image_from_db(db_path: Path) -> Path | None:
    if not db_path.exists():
        return None
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(
            "SELECT id, main_image FROM listings WHERE main_image IS NOT NULL AND TRIM(main_image) != '' ORDER BY id DESC LIMIT 20"
        ).fetchall()
    except sqlite3.Error:
        return None
    finally:
        conn.close()

    root = Path(__file__).resolve().parent
    for _id, main_image in rows:
        candidate = root / "static" / str(main_image)
        if candidate.exists():
            return candidate
    return None


def main():
    parser = argparse.ArgumentParser(description="Test Gemini machine condition analysis.")
    parser.add_argument("--image", help="Path to an image file to analyze.")
    parser.add_argument("--db", help="Path to SQLite DB (default: ./agrorent.db).", default="agrorent.db")
    args = parser.parse_args()

    env_path = Path(__file__).resolve().with_name(".env")
    load_dotenv(dotenv_path=env_path, override=True)

    safe_env_path = env_path.as_posix().encode("unicode_escape").decode("ascii")
    print(f"Loaded .env from: {safe_env_path}")

    key = (os.environ.get("GEMINI_API_KEY") or "").strip()
    if not key:
        raise SystemExit("GEMINI_API_KEY is not set (check your .env).")

    print(f"GEMINI_API_KEY fingerprint: prefix={key[:6]!r}, suffix={key[-4:]!r}, len={len(key)}")

    img_path = Path(args.image) if args.image else None
    if img_path is None:
        db_path = Path(args.db)
        img_path = _pick_image_from_db(db_path)

    if img_path is None:
        raise SystemExit(
            "No image provided and none found in DB. Run: python gemini_condition_test.py --image path/to/file.jpg"
        )

    img_path = img_path.resolve()
    safe_img_path = img_path.as_posix().encode("unicode_escape").decode("ascii")
    print(f"Using image: {safe_img_path}")

    image_bytes = img_path.read_bytes()
    image_part = types.Part.from_bytes(data=image_bytes, mime_type=_detect_mime(img_path))

    client = genai.Client(api_key=key)
    resp = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[ANALYSIS_PROMPT, image_part],
    )

    text = resp.text if hasattr(resp, "text") else str(resp)
    print("\nRaw Gemini response:\n")
    print(text)

    # Best-effort JSON extraction (same idea as app)
    match = re.search(r"\{[\s\S]*\}", text or "")
    if match:
        try:
            parsed = json.loads(match.group(0))
            print("\nParsed JSON:\n")
            print(json.dumps(parsed, indent=2, ensure_ascii=False))
        except Exception:
            pass


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("Condition test failed:")
        try:
            print(repr(e))
        except Exception:
            print(str(e).encode("unicode_escape").decode("ascii"))
        raise

