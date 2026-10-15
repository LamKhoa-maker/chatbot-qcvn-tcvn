"""Deploy app len HuggingFace Spaces.
Doc HF_TOKEN tu bien moi truong, doc GEMINI_API_KEY tu file .env local
de dat lam Space secret (khong upload file .env).
"""
import os
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
SPACE_NAME = sys.argv[1] if len(sys.argv) > 1 else "chatbot-qcvn-tcvn"

IGNORE = [".env", "chroma_db", "data", "__pycache__", "*.pyc", ".git", "test_*"]


def main() -> None:
    from huggingface_hub import HfApi, login

    token = os.getenv("HF_TOKEN", "").strip()
    if not token:
        raise SystemExit("Thieu HF_TOKEN")
    login(token=token)
    api = HfApi()

    me = api.whoami(token=token)
    username = me["name"]
    repo_id = f"{username}/{SPACE_NAME}"
    print(f"user={username} repo={repo_id}")

    api.create_repo(
        repo_id=repo_id,
        repo_type="space",
        space_sdk="docker",
        exist_ok=True,
    )
    print("create_repo OK")

    api.upload_folder(
        folder_path=str(BASE),
        repo_id=repo_id,
        repo_type="space",
        ignore_patterns=IGNORE,
    )
    print("upload_folder OK")

    # Dat Gemini key lam secret (doc tu .env local)
    gemini_key = ""
    env_file = BASE / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("GEMINI_API_KEY="):
                gemini_key = line.split("=", 1)[1].strip()
    if gemini_key:
        api.add_space_secret(repo_id=repo_id, key="GEMINI_API_KEY", value=gemini_key)
        print("secret GEMINI_API_KEY OK")
    else:
        print("CANH BAO: khong tim thay GEMINI_API_KEY trong .env, tu them trong Settings -> Secrets")

    print(f"URL: https://huggingface.co/spaces/{repo_id}")


if __name__ == "__main__":
    main()
