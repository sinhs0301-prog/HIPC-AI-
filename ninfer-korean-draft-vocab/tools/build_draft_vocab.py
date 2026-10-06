#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Build a language/domain-specific draft (proposal) vocabulary for MTP speculative decoding.

Counts token frequencies of your own text with the model's tokenizer and writes the
top-N token ids. Optionally merges them with an existing proposal list so the result
still covers the original (English/Chinese/code/math) tokens.

Input folders: every *.txt, *.md, *.jsonl, *.json file under each folder is read
(for JSON/JSONL, all string values of 20+ characters are used). Give several folders
with weights to balance groups, e.g. a small domain corpus against a large wiki dump:

    python build_draft_vocab.py --tokenizer tokenizer.json \
        --corpus domain_texts:0.35 --corpus prose:0.25 --corpus wiki:0.15 --corpus code_en:0.25 \
        --top 65536 --out ko_draft_vocab_65536

Merge with an existing proposal list (fill to --total, existing list order kept):

    python build_draft_vocab.py ... --top 65536 \
        --merge-with original_proposal_ids.npy --total 131072 --out ko65k_plus_orig_131072

`--merge-with` accepts a 1-D integer .npy, a text file of token ids (ranked, best first),
or `--merge-ranking FILE` for a raw little-endian int64 per-token count file (NInfer's
ranking format), which is ranked by count.

Outputs <out>.npy (int32, sorted ascending unless merged; merged keeps rank order) and
<out>.txt (one id per line). Coverage of each corpus group is printed for both the new
set and the "lowest N ids" baseline.

Requires: pip install tokenizers numpy
"""
import argparse
import collections
import json
import os
import sys

import numpy as np
from tokenizers import Tokenizer

EXTS = (".txt", ".md", ".jsonl", ".json")


def _strings(o):
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        for v in o.values():
            yield from _strings(v)
    elif isinstance(o, list):
        for v in o:
            yield from _strings(v)


def iter_texts(folder, max_chars, max_file_bytes):
    n = 0
    for root, _, files in os.walk(folder):
        for name in sorted(files):
            if not name.endswith(EXTS):
                continue
            path = os.path.join(root, name)
            try:
                if os.path.getsize(path) > max_file_bytes:
                    continue
                with open(path, encoding="utf-8", errors="ignore") as f:
                    if name.endswith(".jsonl"):
                        parts = []
                        for line in f:
                            try:
                                parts += [s for s in _strings(json.loads(line)) if len(s) >= 20]
                            except ValueError:
                                continue
                    elif name.endswith(".json"):
                        try:
                            parts = [s for s in _strings(json.load(f)) if len(s) >= 20]
                        except ValueError:
                            parts = []
                    else:
                        parts = [f.read()]
            except OSError:
                continue
            for s in parts:
                n += len(s)
                yield s
                if max_chars and n >= max_chars:
                    return


def count_tokens(tok, texts, batch_size=256):
    c = collections.Counter()
    batch, nchars = [], 0
    for s in texts:
        nchars += len(s)
        batch.append(s[:200_000])
        if len(batch) >= batch_size:
            for e in tok.encode_batch(batch, add_special_tokens=False):
                c.update(e.ids)
            batch = []
    if batch:
        for e in tok.encode_batch(batch, add_special_tokens=False):
            c.update(e.ids)
    return c, nchars


def special_ids(tokenizer_path, config_path):
    ids = set()
    with open(tokenizer_path, encoding="utf-8") as f:
        ids |= {int(a["id"]) for a in json.load(f).get("added_tokens", [])}
    if config_path and os.path.exists(config_path):
        with open(config_path, encoding="utf-8") as f:
            ids |= {int(k) for k in json.load(f).get("added_tokens_decoder", {})}
    return ids


def load_ranked_ids(path):
    if path.endswith(".npy"):
        a = np.load(path, allow_pickle=False)
        if a.ndim != 1 or a.dtype.kind not in "iu":
            sys.exit("--merge-with .npy must be a 1-D integer array")
        return [int(x) for x in a]
    words = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            words += line.split("#", 1)[0].replace(",", " ").split()
    return [int(w) for w in words]


def load_ranking_counts(path, vocab):
    total = np.fromfile(path, dtype="<i8")
    total = total[:vocab]
    return [int(i) for i in np.argsort(-total, kind="stable") if total[i] > 0]


def save(ids, out):
    arr = np.asarray(ids, dtype=np.int32)
    np.save(out + ".npy", arr)
    with open(out + ".txt", "w", encoding="utf-8") as f:
        f.write("\n".join(str(int(i)) for i in arr) + "\n")
    print(f"wrote {out}.npy / {out}.txt ({arr.size} ids)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tokenizer", required=True, help="tokenizer.json of the target model")
    ap.add_argument("--tokenizer-config", help="tokenizer_config.json (extra special tokens)")
    ap.add_argument("--corpus", action="append", required=True, metavar="FOLDER[:WEIGHT]",
                    help="folder of your own text; repeat for groups (weight default 1)")
    ap.add_argument("--max-chars", type=int, default=25_000_000, help="per group character cap")
    ap.add_argument("--max-file-bytes", type=int, default=50_000_000)
    ap.add_argument("--top", type=int, required=True, help="ids to take from your corpus (incl. specials/bytes)")
    ap.add_argument("--no-bytes", action="store_true", help="do not force ids 0..255 (byte fallback tokens)")
    ap.add_argument("--merge-with", help="existing ranked proposal ids (.npy or text) to fill up to --total")
    ap.add_argument("--merge-ranking", help="existing per-token int64 count file to fill up to --total")
    ap.add_argument("--total", type=int, help="final row count when merging (must match your engine's kernel shapes)")
    ap.add_argument("--out", required=True, help="output path without extension")
    args = ap.parse_args()

    tok = Tokenizer.from_file(args.tokenizer)
    vocab = tok.get_vocab_size(with_added_tokens=True)
    specials = {i for i in special_ids(args.tokenizer, args.tokenizer_config) if i < vocab}

    score = collections.defaultdict(float)
    counts = {}
    for spec in args.corpus:
        folder, w = spec, 1.0
        head, sep, tail = spec.rpartition(":")
        if sep and head:
            try:
                folder, w = head, float(tail)
            except ValueError:
                pass
        c, nchars = count_tokens(tok, iter_texts(folder, args.max_chars, args.max_file_bytes))
        tot = sum(c.values())
        if not tot:
            print(f"warning: no text in {folder}")
            continue
        counts[folder] = c
        for t, k in c.items():
            score[t] += w * k / tot
        print(f"{folder}: weight {w} {nchars/1e6:.1f}M chars {tot/1e6:.2f}M tokens {len(c)} distinct")

    keep = list(sorted(specials))
    if not args.no_bytes:
        keep += [i for i in range(min(256, vocab)) if i not in specials]
    seen = set(keep)
    for t, _ in sorted(score.items(), key=lambda x: (-x[1], x[0])):
        if len(keep) >= args.top:
            break
        if t not in seen:
            keep.append(int(t))
            seen.add(int(t))
    i = 0
    while len(keep) < args.top and i < vocab:  # tiny corpus: pad with lowest ids
        if i not in seen:
            keep.append(i)
            seen.add(i)
        i += 1

    mine = set(keep)
    low = set(range(args.top)) | specials
    for g, c in counts.items():
        tot = sum(c.values())
        cov = 100 * sum(k for t, k in c.items() if t in mine) / tot
        cov_low = 100 * sum(k for t, k in c.items() if t in low) / tot
        print(f"coverage {g}: new set {cov:.2f}% | lowest-{args.top}-ids baseline {cov_low:.2f}%")

    if args.merge_with or args.merge_ranking:
        if not args.total:
            sys.exit("--total is required when merging")
        ranked = load_ranked_ids(args.merge_with) if args.merge_with else load_ranking_counts(args.merge_ranking, vocab)
        merged = sorted(keep)
        for t in ranked:
            if len(merged) >= args.total:
                break
            if t not in mine and 0 <= t < vocab:
                merged.append(t)
                mine.add(t)
        if len(merged) < args.total:
            sys.exit(f"merge source too short: {len(merged)} < {args.total}")
        save(merged, args.out)
    else:
        save(sorted(keep), args.out)


if __name__ == "__main__":
    main()
