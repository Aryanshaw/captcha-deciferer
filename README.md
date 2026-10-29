# deciferer

Reads a token / puzzle-style code out of an image, locally, from the command line.
Runs the [Graf-J](https://huggingface.co/Graf-J) recognition models on your own
machine — nothing is uploaded anywhere, and models are cached after their first use.

```
$ deciferer -q ~/Downloads/code.png
7htq4
```

## Install

```
curl -fsSL https://raw.githubusercontent.com/Aryanshaw/captcha-deciferer/main/install.sh | bash
```

Creates a self-contained venv under `~/.tools/captcha-deciferer` and puts a
`deciferer` launcher in `~/.local/bin`. Requires python3 with venv support.
Set `DECIFERER_HOME` / `DECIFERER_BIN` to install somewhere else.

## Usage

```
deciferer image.png another.png https://example.com/image.jpg              # try this image
deciferer -q image.png                                                     # no confidence column
deciferer -m ct-finetuned image.png                                        # pick a model
```

- The first positional argument can be a file path or an http(s) URL.
- If you pass `-m model` after images with a single image, drop `-q` first —
  argument order matters to argparse.

## Models

| flag | HF model | notes |
|---|---|---|
| (default) | `Graf-J/captcha-crnn-finetuned` | best on typical machine-generated tokens |
| `crnn-base` | `Graf-J/captcha-crnn-base` | fallback when the finetuned one looks off |
| `ct-finetuned` | `Graf-J/captcha-conv-transformer-finetuned` | different architecture — good second guess for a retry |
| `ct-base` | `Graf-J/captcha-conv-transformer-base` | same, unfine-tuned |

Retry with a different `-m` whenever the guessed token looks malformed.

## License

MIT
