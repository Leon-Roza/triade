"""
TRÍADE — API de detecção de harmonia a partir de um link do YouTube.

Fluxo: link do YouTube -> yt-dlp baixa o áudio -> librosa extrai o chroma ->
templates de acordes + Viterbi -> tom + progressão -> JSON.

Este arquivo espelha o algoritmo que roda no navegador (index.html).
"""
import os
import json
import math
import hmac
import shutil
import hashlib
import tempfile
import urllib.request
from datetime import datetime, timedelta

import numpy as np
import librosa
import yt_dlp
from fastapi import FastAPI, HTTPException, Request
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


# =====================================================================
#  Assinatura / pagamento (Mercado Pago) + ativação no Supabase
#  Configure as variáveis de ambiente (Render > Environment):
#    MP_ACCESS_TOKEN, MP_WEBHOOK_SECRET, BACKEND_URL, SITE_URL,
#    SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
# =====================================================================

SITE_URL = os.environ.get("SITE_URL", "https://usetriade.com.br")
BACKEND_URL = os.environ.get("BACKEND_URL", "").rstrip("/")
MP_ACCESS_TOKEN = os.environ.get("MP_ACCESS_TOKEN", "")
MP_WEBHOOK_SECRET = os.environ.get("MP_WEBHOOK_SECRET", "")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

PLANS = {
    ("pro", "mensal"):     {"title": "TRÍADE Pro — mensal",     "price": 19.0,  "months": 1},
    ("pro", "anual"):      {"title": "TRÍADE Pro — anual",      "price": 149.0, "months": 12},
    ("studio", "mensal"):  {"title": "TRÍADE Studio — mensal",  "price": 49.0,  "months": 1},
    ("studio", "anual"):   {"title": "TRÍADE Studio — anual",   "price": 499.0, "months": 12},
}


class CheckoutRequest(BaseModel):
    plan: str
    cycle: str = "mensal"
    userId: str | None = None
    email: str | None = None


def _http_json(method, url, headers, body=None):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    for k, v in headers.items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            txt = resp.read().decode("utf-8") or "{}"
            return json.loads(txt)
    except urllib.error.HTTPError as exc:  # noqa: F821
        detail = exc.read().decode("utf-8", "ignore")
        raise HTTPException(status_code=502, detail=detail or exc.reason)


@app.post("/checkout")
def checkout(req: CheckoutRequest):
    """Cria uma preferência de pagamento (Checkout Pro) e devolve o init_point."""
    if not MP_ACCESS_TOKEN:
        raise HTTPException(status_code=400, detail="Checkout indisponivel (MP_ACCESS_TOKEN nao configurado)")
    plan = PLANS.get((req.plan, req.cycle))
    if not plan:
        raise HTTPException(status_code=400, detail="Plano invalido")

    body = {
        "items": [{
            "title": plan["title"],
            "quantity": 1,
            "currency_id": "BRL",
            "unit_price": plan["price"],
        }],
        "external_reference": req.userId or "",
        "metadata": {"plan": req.plan, "cycle": req.cycle, "user_id": req.userId or ""},
        "back_urls": {"success": SITE_URL, "pending": SITE_URL, "failure": SITE_URL},
        "auto_return": "approved",
    }
    if req.email:
        body["payer"] = {"email": req.email}
    if BACKEND_URL:
        body["notification_url"] = BACKEND_URL + "/webhooks/mercadopago"

    r = _http_json("POST", "https://api.mercadopago.com/checkout/preferences",
                   {"Authorization": "Bearer " + MP_ACCESS_TOKEN}, body)
    init = r.get("init_point") or r.get("sandbox_init_point")
    if not init:
        raise HTTPException(status_code=502, detail="Mercado Pago nao retornou init_point")
    return {"init_point": init}


def _verify_mp_signature(request: Request, raw: bytes, data_id: str) -> bool:
    if not MP_WEBHOOK_SECRET:
        return True
    sig = request.headers.get("x-signature", "")
    req_id = request.headers.get("x-request-id", "")
    ts, v1 = "", ""
    for part in sig.split(","):
        if part.startswith("ts="):
            ts = part[3:]
        elif part.startswith("v1="):
            v1 = part[3:]
    manifest = f"id:{data_id};request-id:{req_id};ts:{ts};"
    calc = hmac.new(MP_WEBHOOK_SECRET.encode(), manifest.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(calc, v1)


def _activate(user_id, plan, cycle):
    if not (SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY and user_id):
        return
    months = 12 if cycle == "anual" else 1
    expires = (datetime.utcnow() + timedelta(days=30 * months)).strftime("%Y-%m-%dT%H:%M:%SZ")
    _http_json("PATCH",
               f"{SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}",
               {"apikey": SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": "Bearer " + SUPABASE_SERVICE_ROLE_KEY,
                "Prefer": "return=minimal"},
               {"plan": plan, "expires_at": expires})


@app.post("/webhooks/mercadopago")
async def mp_webhook(request: Request):
    raw = await request.body()
    try:
        data = json.loads(raw.decode("utf-8") or "{}")
    except Exception:
        data = {}
    topic = data.get("type") or data.get("topic") or request.query_params.get("topic")
    data_id = str((data.get("data") or {}).get("id") or data.get("id")
                  or request.query_params.get("data.id") or request.query_params.get("id") or "")

    if not _verify_mp_signature(request, raw, data_id):
        raise HTTPException(status_code=401, detail="assinatura invalida")

    if topic in ("payment", "merchant_order") and data_id:
        pay = _http_json("GET", f"https://api.mercadopago.com/v1/payments/{data_id}",
                         {"Authorization": "Bearer " + MP_ACCESS_TOKEN})
        if pay.get("status") == "approved":
            meta = pay.get("metadata") or {}
            _activate(pay.get("external_reference"), meta.get("plan", "pro"), meta.get("cycle", "anual"))
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
