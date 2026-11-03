"""Build the small, source-only Devpost upload without private runtime files."""
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "submission" / "AgentGate-Devpost-Upload.zip"
MAX_BYTES = 35_000_000


def files(patterns: tuple[str, ...]) -> set[Path]:
    return {path for pattern in patterns for path in ROOT.glob(pattern) if path.is_file()}


def package_files() -> list[Path]:
    selected = files((
        ".github/workflows/ci.yml", ".gitignore", "LICENSE", "README.md", "render.yaml",
        "backend/agentgate/*.py", "backend/benchmarks/*.json", "backend/reports/*.json",
        "backend/tests/*.py", "backend/pytest.ini", "backend/requirements*.txt",
        "docs/*.md", "examples/*.py", "scripts/bootstrap.py", "scripts/start_demo.py",
        "frontend/app/*.tsx", "frontend/app/*.ts", "frontend/app/*.css",
        "frontend/app/api/auth/*/*.ts", "frontend/app/api/gateway/*/*.ts",
        "frontend/app/components/*.tsx", "frontend/lib/*.ts", "frontend/next.config.ts",
        "frontend/package.json", "frontend/package-lock.json", "frontend/tsconfig.json",
        "frontend/public/fonts/PublicSans-OFL.txt", "frontend/public/fonts/PublicSans.ttf",
        "submission/DEVPOST.md", "submission/YOUTUBE.md", "submission/package_devpost.py",
        "submission/render-v2/AgentGate-Thumbnail.png",
    ))
    return sorted(selected)


def main() -> None:
    members = package_files()
    if not members:
        raise SystemExit("No source files found; refusing to create an empty upload.")
    names = [path.relative_to(ROOT).as_posix() for path in members]
    forbidden = (".env", ".pem", ".key", ".sqlite", ".db", ".mp4", ".webm")
    if any(Path(name).name.lower().endswith(forbidden) for name in names):
        raise SystemExit("Private configuration or generated media matched the package allowlist.")
    if any("node_modules/" in name or "/tmp/" in name or "__pycache__/" in name for name in names):
        raise SystemExit("Generated dependencies or runtime files matched the package allowlist.")

    readme = """AgentGate — Devpost source upload

This compact archive contains the MIT-licensed app source, dependency locks, judge instructions, evaluation and security notes, submission copy, and thumbnail. It excludes credentials, local databases, downloaded dependencies, raw recordings, and the full video.

Judge quick start: see README.md. Run `python scripts/start_demo.py` for the isolated, simulated workspace. The hosted preview is https://agentgate-demo-console-2026.onrender.com; it uses simulated payments and rate-limited live AI planning.

Demo video: https://www.youtube.com/watch?v=1ey3pn47ujk
"""
    temporary = OUTPUT.with_suffix(".zip.tmp")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        archive.writestr("PACKAGE-README.txt", readme)
        for path, name in zip(members, names):
            archive.write(path, name)
    size = temporary.stat().st_size
    if size > MAX_BYTES:
        temporary.unlink(missing_ok=True)
        raise SystemExit(f"Upload archive is {size} bytes, exceeding the 35 MiB limit.")
    with zipfile.ZipFile(temporary) as archive:
        bad = archive.testzip()
        if bad:
            temporary.unlink(missing_ok=True)
            raise SystemExit(f"Corrupt archive member: {bad}")
    temporary.replace(OUTPUT)
    print(f"Created {OUTPUT} ({size:,} bytes; {len(members) + 1} files).")


if __name__ == "__main__":
    main()
