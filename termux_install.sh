#!/data/data/com.termux/files/usr/bin/bash
# --- MONICO JARVIS TERMUX INSTALLER ---
#
# Why a special installer at all: a plain
#     pip install -r requirements.txt
# fails on Termux. fastapi pulls in pydantic v2, whose pydantic-core is a
# Rust extension with NO precompiled Termux wheel on PyPI (Termux is not
# glibc/manylinux), so pip falls back to compiling Rust on the phone -
# slow, and it dies outright when no Rust toolchain is present.
#
# This installer tries, in order:
#   1. The Termux User Repository (TUR) PyPI index, which ships a
#      precompiled pydantic-core wheel for Termux.
#   2. Fallback: pkg install rust + a source build (works, ~10+ min,
#      CARGO_BUILD_JOBS=1 so low-RAM phones do not OOM).
#
# Works inside a clone (bash termux_install.sh) or downloaded on its own
# (it clones the public repo first in that case).
set -e

REPO_URL="https://github.com/jaykk99/monico-Jarvis.git"
REPO_DIR="$HOME/monico-Jarvis"
TUR_INDEX="https://termux-user-repository.github.io/pypi/"

echo "[!] Initializing Monico Jarvis environment (Termux)..."

# 1. Find or fetch the repo, and work from its root.
SCRIPT_DIR="$(cd "$(dirname "$0")" 2>/dev/null && pwd || echo "")"
if [ -n "$SCRIPT_DIR" ] && [ -f "$SCRIPT_DIR/main.py" ]; then
    REPO_DIR="$SCRIPT_DIR"
elif [ -f "$REPO_DIR/main.py" ]; then
    echo "[!] Found existing clone at $REPO_DIR"
else
    echo "[!] Cloning monico-Jarvis into $REPO_DIR ..."
    git clone "$REPO_URL" "$REPO_DIR" 2>/dev/null || {
        echo "[!] git is not installed yet - installing packages first, then cloning."
        pkg update -y
        pkg install -y python git
        git clone "$REPO_URL" "$REPO_DIR"
    }
fi
cd "$REPO_DIR"
if [ -d .git ]; then
    git pull -q 2>/dev/null || echo "[!] (pull skipped - continuing with what is here)"
fi

# 2. Termux packages. No venv: Termux Python is already per-app, and a
#    venv only gets in the way of Termux-provided packages/indexes.
echo "[!] Installing Termux packages (python, git)..."
pkg update -y
pkg install -y python git

# 3. Python deps - TUR index first so pydantic-core lands as a wheel.
echo "[!] Installing Python dependencies (fastapi, uvicorn, python-dotenv)..."
python -m pip install --upgrade pip
if python -m pip install -r requirements.txt --extra-index-url "$TUR_INDEX"; then
    echo "[!] Dependencies installed (prebuilt wheels where Termux needs them)."
else
    echo "[!] Prebuilt route failed - falling back to a Rust source build."
    echo "[!] This takes a while on a phone. Keep Termux open and plugged in."
    pkg install -y rust binutils
    CARGO_BUILD_JOBS=1 python -m pip install -r requirements.txt
fi

# 4. Verify the real imports, then boot-smoke the server.
echo "[!] Verifying imports..."
python -c "import fastapi, uvicorn, pydantic, dotenv; print('[!] imports OK')"

echo "[!] Boot check on http://127.0.0.1:8000/health ..."
python main.py &
SERVER_PID=$!
trap 'kill $SERVER_PID 2>/dev/null || true' EXIT
OK=""
for i in $(seq 1 30); do
    if python -c "
import urllib.request
try:
    r = urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)
    raise SystemExit(0 if r.status == 200 else 1)
except SystemExit:
    raise
except Exception:
    raise SystemExit(1)
" 2>/dev/null; then
        OK="yes"
        break
    fi
    sleep 1
done
kill $SERVER_PID 2>/dev/null || true
trap - EXIT
if [ -z "$OK" ]; then
    echo "[!] Boot check FAILED - the server did not answer on port 8000."
    exit 1
fi
echo "[!] Boot check passed."

echo ""
echo "[!] Monico Jarvis ready. Launch it:"
echo ""
echo "    cd \"$REPO_DIR\""
echo "    python main.py"
echo ""
echo "[!] Then open this in your Android browser:"
echo ""
echo "    http://127.0.0.1:8000"
echo ""
echo "[!] No API keys needed - every skill runs locally on the phone."
