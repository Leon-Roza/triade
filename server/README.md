# TRÍADE — API de detecção de harmonia (YouTube)

Serviço que recebe um link do YouTube, baixa o áudio (yt-dlp) e devolve a
**tonalidade** e a **progressão de acordes** detectadas.

> O site (`index.html`) roda 100% estático no GitHub Pages e já detecta acordes
> de **arquivos de áudio enviados**. Este backend adiciona a análise direta de
> **links do YouTube**, que não é possível fazer no navegador (CORS + ToS).

## Endpoint

`POST /analyze`

```json
// requisição
{ "url": "https://www.youtube.com/watch?v=XXXXXXXXXXX" }

// resposta
{
  "segments": [
    { "start": 0.0, "end": 2.1, "root": 0, "quality": "maj", "chord": "C" },
    { "start": 2.1, "end": 4.3, "root": 7, "quality": "maj", "chord": "G" }
  ],
  "key": { "root": 0, "mode": "maior" },
  "duration": 214.5,
  "chordCount": 87
}
```

`GET /health` → `{ "ok": true }`

## Rodando localmente

Precisa de **ffmpeg** instalado e Python 3.11+.

```bash
cd server
python -m venv .venv
# Windows: .venv\Scripts\activate    |    Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload --port 8000
```

Teste:

```bash
curl -X POST http://localhost:8000/analyze -H "Content-Type: application/json" \
  -d "{\"url\":\"https://www.youtube.com/watch?v=dQw4w9WgXcQ\"}"
```

## Deploy (Docker)

O `Dockerfile` já instala o ffmpeg. Exemplos de plataformas que aceitam Docker:

- **Render**: New > Web Service > Deploy from repo, runtime *Docker*, root `server/`.
- **Railway**: New Project > Deploy from repo (detecta o Dockerfile).
- **Fly.io**: `fly launch` dentro de `server/`.

### Conectar o site ao backend

Depois do deploy, abra `index.html` e preencha a constante no topo do script:

```js
const DET_API = 'https://SEU-SERVICO.onrender.com';
```

Enquanto `DET_API` estiver vazio, o site mostra o player do YouTube e instrui a
enviar o arquivo de áudio para a análise local.

## Limitações

- O yt-dlp pode falhar em vídeos protegidos / com detecção de bot; atualize o
  pacote (`pip install -U yt-dlp`) periodicamente.
- A análise é limitada aos primeiros **8 minutos** do vídeo.
- Baixar áudio do YouTube pode violar os Termos de Uso — use com responsabilidade
  e apenas em conteúdo que você tenha direito de analisar.
