#!/bin/sh
# deciferer installer: get a self-contained venv install from this repo onto any mac/linux box.
# Usage:  curl -fsSL https://raw.githubusercontent.com/Aryanshaw/captcha-deciferer/main/install.sh | bash
set -eu

REPO="Aryanshaw/captcha-deciferer"
BRANCH="main"
DEST="${DECIFERER_HOME:-$HOME/.tools/captcha-deciferer}"
BIN_DIR="${DECIFERER_BIN:-$HOME/.local/bin}"

# need python3 with venv support; error loudly if missing
if ! python3 -m venv --help >/dev/null 2>&1; then
  echo "error: python3 with venv support is required (macOS: xcode-select --install)" >&2
  exit 1
fi

echo "==> fetching $REPO into $DEST"
rm -rf "$DEST"
mkdir -p "$(dirname "$DEST")"
curl -fsSL "https://codeload.github.com/$REPO/tar.gz/refs/heads/$BRANCH" \
  | tar xz -C "$DEST" --strip-components=1

echo "==> creating venv at $DEST/venv"
python3 -m venv "$DEST/venv"

# linux default torch pulls ~2GB of cuda wheels; the cpu-only index is all this tool needs
PYPI_TORCH_ARGS=""
case "$(uname)" in
  Linux) PYPI_TORCH_ARGS="--extra-index-url https://download.pytorch.org/whl/cpu" ;;
esac

echo "==> installing dependencies (this is the slow part: torch + transformers)"
"$DEST/venv/bin/pip" install --quiet --upgrade pip
"$DEST/venv/bin/pip" install --quiet $PYPI_TORCH_ARGS -r "$DEST/requirements.txt"

# write the launcher so `deciferer` runs the venv python against the repo script
mkdir -p "$BIN_DIR"
cat > "$BIN_DIR/deciferer" <<EOF
#!/bin/sh
exec "$DEST/venv/bin/python" "$DEST/src/deciferer.py" "\$@"
EOF
chmod 755 "$BIN_DIR/deciferer"

case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *) echo "note: $BIN_DIR is not on your PATH — add it to your shell profile" >&2 ;;
esac

echo ""
echo "installed. try it:    deciferer -q path/to/image.png"
echo "models download from hugging face on first use and are cached afterwards"
