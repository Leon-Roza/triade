"""
TRÍADE — API de detecção de harmonia a partir de um link do YouTube.

Fluxo: link do YouTube -> yt-dlp baixa o áudio -> librosa extrai o chroma ->
templates de acordes + Viterbi -> tom + progressão -> JSON.

Este arquivo espelha o algoritmo que roda no navegador (index.html).
"""
import os
import math
import shutil
import tempfile

import numpy as np
import librosa
import yt_dlp
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="TRÍADE — Detector de harmonia")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ROOTS = ["C", "Db", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
MODES_INTERVALS = {
    "maior": [0, 2, 4, 5, 7, 9, 11],
    "menorNatural": [0, 2, 3, 5, 7, 8, 10],
}
MAJ_PROFILE = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
MIN_PROFILE = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]

MAX_SECONDS = 240  # limita a análise (ex.: 4 min) para manter o tempo de resposta


def build_templates():
    defs = {"maj": ([0, 4, 7], 0.0), "min": ([0, 3, 7], 0.0),
            "dim": ([0, 3, 6], 0.05), "aug": ([0, 4, 8], 0.06)}
    templates = []
    for quality, (ivs, pen) in defs.items():
        for root in range(12):
            vec = np.zeros(12)
            for iv in ivs:
                vec[(root + iv) % 12] = 1.0
            vec /= np.linalg.norm(vec)
            templates.append({"root": root, "quality": quality, "vec": vec, "pen": pen})
    return templates


TEMPLATES = build_templates()
VEC_MATRIX = np.stack([t["vec"] for t in TEMPLATES], axis=0)      # (NT, 12)
PENS = np.array([t["pen"] for t in TEMPLATES])                    # (NT,)


class AnalyzeRequest(BaseModel):
    url: str


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    url = (req.url or "").strip()
    if not url.startswith("http"):
        raise HTTPException(status_code=400, detail="URL invalida")

    tmp = tempfile.mkdtemp(prefix="triade_")
    try:
        wav = _download_audio(url, tmp)
        y, sr = librosa.load(wav, sr=11025, mono=True)
        if len(y) > MAX_SECONDS * sr:
            y = y[: MAX_SECONDS * sr]
        return _detect(y, sr)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _download_audio(url: str, tmp: str) -> str:
    outtmpl = os.path.join(tmp, "audio.%(ext)s")

    # Cookies opcionais (necessários quando o YouTube bloqueia o IP do servidor).
    # Defina YT_COOKIES (conteudo do cookies.txt) ou YT_COOKIES_B64 (base64 dele).
    cookiefile = None
    raw = os.environ.get("YT_COOKIES", "").strip()
    b64 = os.environ.get("YT_COOKIES_B64", "").strip()
    if b64:
        import base64
        raw = base64.b64decode(b64).decode("utf-8", "ignore")
    if raw:
        cookiefile = os.path.join(tmp, "cookies.txt")
        with open(cookiefile, "w", encoding="utf-8") as fh:
            fh.write(raw)

    opts = {
        "format": "bestaudio/best",
        "outtmpl": outtmpl,
        "quiet": True,
        "noplaylist": True,
        "retries": 3,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "wav",
            "preferredquality": "192",
        }],
        "extractor_args": {"youtube": {"player_client": ["android", "web_safari", "tv", "mweb"]}},
    }
    if cookiefile:
        opts["cookiefile"] = cookiefile

    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])
    for name in os.listdir(tmp):
        if name.endswith(".wav"):
            return os.path.join(tmp, name)
    raise RuntimeError("Nao foi possivel extrair o audio do video")


def _detect(y, sr):
    hop = 2048
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop)  # (12, T)
    energy = librosa.feature.rms(y=y, hop_length=hop)[0]

    t = min(chroma.shape[1], energy.shape[0])
    chroma = chroma[:, :t]
    energy = energy[:t]

    norms = np.linalg.norm(chroma, axis=0, keepdims=True)
    norms[norms < 1e-9] = 1.0
    chroma = chroma / norms

    sims = VEC_MATRIX @ chroma            # (NT, T) cosseno
    sims = sims - PENS[:, None]

    if t and energy.max() > 0:
        gate = energy.max() * 0.02
        weak = energy < gate
        sims[:, weak] = -1.0

    path = _viterbi(sims)

    frame_dur = hop / sr
    nt = len(TEMPLATES)
    segments = []
    cur, start = path[0], 0
    for i in range(1, len(path)):
        if path[i] != cur:
            segments.append(_make_segment(start, i, cur, frame_dur, nt))
            start, cur = i, path[i]
    segments.append(_make_segment(start, len(path), cur, frame_dur, nt))

    merged = []
    for seg in segments:
        if merged and (seg["end"] - seg["start"]) < 0.35:
            merged[-1]["end"] = seg["end"]
        else:
            merged.append(seg)

    avg = chroma.mean(axis=1) if t else np.zeros(12)
    key = _key_from_chords(merged, avg)
    chord_count = sum(1 for s in merged if s["quality"] != "N")

    for seg in merged:
        seg["chord"] = _chord_name(seg)
        seg["start"] = round(seg["start"], 2)
        seg["end"] = round(seg["end"], 2)

    return {
        "segments": merged,
        "key": key,
        "duration": round(len(y) / sr, 2),
        "chordCount": chord_count,
    }


def _make_segment(a, b, state, frame_dur, nt):
    seg = {"start": a * frame_dur, "end": b * frame_dur}
    if state < nt:
        seg["root"] = TEMPLATES[state]["root"]
        seg["quality"] = TEMPLATES[state]["quality"]
    else:
        seg["quality"] = "N"
    return seg


def _viterbi(sims):
    nt, t = sims.shape
    s = nt + 1
    frame_max = sims.max(axis=0)

    def emit(i, state):
        if state < nt:
            return sims[state, i]
        return 0.45 + 0.55 * (1.0 - frame_max[i])

    delta = np.array([emit(0, j) for j in range(s)])
    psi = np.zeros((t, s), dtype=np.int32)

    for i in range(1, t):
        prev = delta.copy()
        for j in range(s):
            best, arg = -1e18, 0
            for p in range(s):
                v = prev[p] + (0.40 if p == j else -0.25)
                if v > best:
                    best, arg = v, p
            delta[j] = best + emit(i, j)
            psi[i, j] = arg

    last = int(np.argmax(delta))
    path = np.zeros(t, dtype=np.int32)
    path[-1] = last
    for i in range(t - 1, 0, -1):
        path[i - 1] = psi[i, path[i]]
    return path


def _chord_name(seg):
    if seg["quality"] == "N":
        return "·"
    suffix = {"maj": "", "min": "m", "dim": "º", "aug": "5+"}[seg["quality"]]
    return ROOTS[seg["root"]] + suffix


def _key_from_chords(segments, avg):
    def corr(a, b):
        a = a - a.mean()
        b = b - b.mean()
        denom = math.sqrt(float((a * a).sum()) * float((b * b).sum())) + 1e-9
        return float((a * b).sum()) / denom

    chords = [s for s in segments if s["quality"] != "N"]
    first = chords[0] if chords else None
    best = None

    for mode, profile in (("maior", MAJ_PROFILE), ("menorNatural", MIN_PROFILE)):
        dia = set(MODES_INTERVALS[mode])
        prof = np.array(profile)
        for r in range(12):
            rot = np.array([prof[(i - r) % 12] for i in range(12)])
            cc = corr(avg, rot)

            fit, total = 0.0, 0.0
            for s in chords:
                dur = s["end"] - s["start"]
                total += dur
                rel = (s["root"] - r) % 12
                if rel in dia:
                    w = 2.2 if rel == 0 else 1.6 if rel == 7 else 1.0
                else:
                    w = -0.8
                fit += w * dur
            nfit = fit / total if total > 0 else 0.0

            bonus = 0.0
            if first is not None and (first["root"] - r) % 12 == 0:
                want = "maj" if mode == "maior" else "min"
                if first["quality"] == want:
                    bonus = 0.2

            score = cc * 0.6 + nfit * 0.9 + bonus
            if best is None or score > best["score"]:
                best = {"score": score, "root": r, "mode": mode}

    return {"root": best["root"], "mode": best["mode"]}
