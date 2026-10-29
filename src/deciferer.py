#!/usr/bin/env python3
"""Deciferer: solve obfuscated/puzzle images with Graf-J recognition models.

Loads one model, predicts the token for each input image, prints results.
The exact preprocessing / CTC decode replicates the upstream Space demo.
"""
import argparse
import os
import string
import sys
import urllib.request
from pathlib import Path

DEFAULT_MODEL = "Graf-J/captcha-crnn-finetuned"

# model display name -> HF repo id
MODELS = {
    "crnn-finetuned": "Graf-J/captcha-crnn-finetuned",
    "crnn-base": "Graf-J/captcha-crnn-base",
    "ct-finetuned": "Graf-J/captcha-conv-transformer-finetuned",
    "ct-base": "Graf-J/captcha-conv-transformer-base",
}


def load_image(source: str):
    import torch
    from PIL import Image

    if source.lower().startswith(("http://", "https://")):
        tmp = Path(os.path.join("/tmp", os.path.basename(source.split("?")[0]) or "deciferer_img"))
        tmp.write_bytes(urllib.request.urlopen(source).read())
        return Image.open(tmp).convert("RGB")
    return Image.open(source).convert("RGB")


def predict(sources, model_id: str, show_conf: bool):
    import torch
    import torchvision.transforms.functional as F
    from transformers import AutoModel, AutoProcessor

    # load model once, reuse for every input
    processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
    processor.vocab = string.ascii_lowercase + string.ascii_uppercase + string.digits
    processor.idx_to_char = {i + 1: c for i, c in enumerate(processor.vocab)}
    processor.idx_to_char[0] = ""

    model = AutoModel.from_pretrained(model_id, trust_remote_code=True)
    model.eval()

    results = []
    for src in sources:
        img = load_image(src)
        # grayscale, resize to the CRNN input shape, scale to [0, 1]
        img_t = F.to_tensor(img.convert("L").resize((150, 40)))
        pixel_values = img_t.unsqueeze(0)
        with torch.no_grad():
            logits = model(pixel_values).logits
        # CTC decode: collapse repeated non-blank tokens
        tokens = torch.argmax(logits, dim=-1).squeeze(0)
        text = "".join(
            processor.idx_to_char.get(int(t), "")
            for i, t in enumerate(tokens)
            if int(t) != 0 and not (i > 0 and tokens[i] == tokens[i - 1])
        )
        conf = None
        if show_conf:
            probs = torch.softmax(logits, dim=-1)
            conf = probs.max(dim=-1).values.mean().item()
        results.append((src, text, conf))
    return results


def main():
    ap = argparse.ArgumentParser(prog="deciferer", description=__doc__)
    ap.add_argument("images", nargs="+", help="image paths or http(s) URLs")
    ap.add_argument(
        "-m", "--model",
        choices=[*MODELS.keys(), *MODELS.values()],
        default="crnn-finetuned",
        help="model shorthand or full HF repo id (default: crnn-finetuned)",
    )
    ap.add_argument("-q", "--quiet", action="store_true", help="no confidence column")
    args = ap.parse_args()

    model_id = MODELS.get(args.model, args.model)
    try:
        for src, text, conf in predict(args.images, model_id, not args.quiet):
            line = f"{text}"
            gt = Path(src).name.rsplit(".", 1)[0]
            # filenames that are plain alnum tokens double as ground truth
            if gt.isalnum() and 1 <= len(gt) <= 10:
                mark = "ok" if gt == text else "MISMATCH"
                line += f"  [{gt} {mark}]"
            if conf is not None:
                line += f"  (conf {conf:.1%})"
            print(line)
    except (FileNotFoundError, OSError, urllib.error.URLError) as e:
        sys.exit(f"deciferer: {e}")


if __name__ == "__main__":
    main()
