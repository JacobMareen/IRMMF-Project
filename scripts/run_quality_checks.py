#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_env(env_path: Path) -> dict[str, str]:
    env = dict(os.environ)
    if not env_path.exists():
        return env
    for raw in env_path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key and key not in env:
            env[key] = value
    return env


def _run(title: str, args: list[str], env: dict[str, str]) -> int:
    print(f"\n== {title} ==")
    print("$", " ".join(args))
    return subprocess.call(args, env=env, cwd=str(REPO_ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="Run pytest + investigation smoke tests.")
    parser.add_argument("--skip-tests", action="store_true", help="Skip pytest.")
    parser.add_argument("--skip-smoke", action="store_true", help="Skip smoke test.")
    parser.add_argument("--api-base", help="Override API_BASE for smoke test.")
    parser.add_argument("--tenant-key", help="Override TENANT_KEY for smoke test.")
    parser.add_argument("--roles", help="Override X_IRMMF_ROLES for smoke test.")
    parser.add_argument("--cleanup", action="store_true", help="Cleanup case after smoke test.")
    parser.add_argument(
        "--pytest-args",
        nargs=argparse.REMAINDER,
        help="Extra args passed to pytest after --pytest-args.",
    )
    args = parser.parse_args()

    env = _load_env(REPO_ROOT / ".env")

    if args.api_base:
        env["API_BASE"] = args.api_base
    if args.tenant_key:
        env["TENANT_KEY"] = args.tenant_key
    if args.roles:
        env["X_IRMMF_ROLES"] = args.roles
    if args.cleanup:
        env["CLEANUP"] = "1"

    rc = 0
    if not args.skip_tests:
        pytest_args = [sys.executable, "-m", "pytest", "-q"]
        if args.pytest_args:
            pytest_args.extend(args.pytest_args)
        rc = _run("pytest", pytest_args, env)
        if rc != 0:
            return rc

    if not args.skip_smoke:
        smoke_args = [sys.executable, "scripts/verify_investigation_module.py"]
        rc = _run("investigation smoke test", smoke_args, env)

    return rc


if __name__ == "__main__":
    raise SystemExit(main())
