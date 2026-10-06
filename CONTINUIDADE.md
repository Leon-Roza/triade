# TRÍADE — Documento de continuidade

> Estado do projeto para retomar em outra sessão sem perder o ponto.
> ⚠️ Este arquivo vai para um repositório **público** — por segurança, **não** há
> tokens, senhas ou chaves aqui. Eles ficam nos painéis (links na seção 9).

Última atualização: 2026-10-05

---

## 1. O que é o projeto

**TRÍADE** — site de harmonia para guitarristas e violonistas:
- Disco/campo harmônico interativo (12 tons, escalas maior/menor natural/harmônica).
- Gerador de progressões + ritmos (8) + andamento + metrônomo.
- Síntese de corda dedilhada (Karplus-Strong): violão nylon/aço e guitarra elétrica, com distorção.
- Braço do instrumento (fretboard) marcando o acorde tocado.
- **Detector de harmonia** por upload de áudio (FFT → chroma → Viterbi) com timeline,
  tonalidade detectada, **Salvar cifra** e **▶ Tocar** a cifra salva.
- **Planos** (Grátis / Pro / Studio), conta, salvar progressões e exportar (cifra/PDF/JSON).
- **Modo compositor** (agora em página própria `compositor.html`) — ver seção 6.
- **Bateria/baixo com samples reais CC0** (Virtuosity Drums + baixo pizzicato dsmolken).

---

## 2. Links e IDs

| Item | Valor |
|---|---|
| Site (produção) | http://usetriade.com.br  (HTTPS pendente) |
| Repositório | https://github.com/Leon-Roza/triade (branch `main`) |
| Domínio | usetriade.com.br (DNS na **Hostinger**, NS `dns-parking.com`) |
| E-mail oficial | triadestudio@usetriade.com.br |
| Supabase — org | `lbuomftguodmwrzmvigz` (Triade) |
| Supabase — projeto ref | `hthidkthkgeyfxcevqkw` |
| Supabase — URL | https://hthidkthkgeyfxcevqkw.supabase.co |
| Render — serviço | `srv-db1s405g1s2s73biaqg0` (nome `triade-api`) |
| Render — URL backend | https://triade-api-rkfd.onrender.com |
| Mercado Pago — conta prod | user id `269656963` |
| Conta dona (testada) | `leonrozd@gmail.com` → Supabase user `25599249-a632-4fbc-b67b-05a63d96abdd` |

---

## 3. Arquivos do repositório

- `index.html` — **site inteiro** (HTML+CSS+JS, single file). Publicado pelo GitHub Pages.
- `server/app.py` — backend FastAPI (checkout Mercado Pago + webhook + análise YouTube dormente).
- `server/supabase.sql` — tabela `profiles` + RLS + trigger de criação de usuário.
- `server/SETUP.md` — guia de ativação (Supabase/MP/Render).
- `server/Dockerfile`, `server/requirements.txt`.
- `ROADMAP.md` — roadmap de domínio/hospedagem/vendas.
- `CNAME` (`usetriade.com.br`), `robots.txt`, `sitemap.xml`.

---

## 4. Estado — PRONTO ✅

- **GitHub Pages** no domínio próprio (HTTP 200; HTTPS ainda emitindo certificado).
- **Supabase**: projeto criado, tabela `profiles` + RLS + trigger; redirects de login
  (`site_url` = https://usetriade.com.br e allow list com http/https do domínio).
- **Login real** (magic link) — `CONFIG` no `index.html` aponta para backend + Supabase.
- **Render** com env vars: `BACKEND_URL`, `SITE_URL`, `SUPABASE_URL`,
  `SUPABASE_SERVICE_ROLE_KEY`, `MP_ACCESS_TOKEN` (produção), `MP_WEBHOOK_SECRET`.
- **Mercado Pago**: `/checkout` (Checkout Pro) + `/webhooks/mercadopago` (valida assinatura
  e grava `plan`/`expires_at` no Supabase). **Testado com usuário de teste**: pagamento
  aprovado → webhook → perfil virou `plan='pro'`, `expires_at=2026-11-04`.
- **Preços/planos** (em `index.html`): Grátis R$0 · Pro R$19/mês ou R$149/ano · Studio R$49/mês ou R$499/ano.
  Pro anual R$149, Pro mensal R$19. Studio = "fale com vendas".
- **Links Mercado Pago** (fallback, sem backend): `mpago.la/1vHWRFX` (Pro mensal), `mpago.la/1knT8cu` (Pro anual).
- **Gating**: Free = 3 análises/sessão, 3 progressões salvas, sem exportar; Pro = ilimitado.

---

## 5. PENDÊNCIAS (retomar por aqui)

### 5.1 [BLOQUEADOR de login real] Verificar domínio no Resend
- **Sintoma**: magic link retorna erro 500 "Error sending magic link email"; Resend diz
  *"The usetriade.com.br domain is not verified"*.
- **SMTP do Supabase JÁ configurado** (via API): host `smtp.resend.com`, porta `465`,
  user `resend`, pass = API key do Resend, remetente `triadestudio@usetriade.com.br`, nome `TRÍADE`.
- **Falta**: no Resend (**Domains**) adicionar `usetriade.com.br` e criar os **registros DNS**
  na **Hostinger** (hPanel → Domínio → DNS/Zona DNS), depois clicar em **Verify** no Resend.
  Registros típicos: MX em `send.` , TXT SPF em `send.`, TXT DKIM em `resend._domainkey.`,
  TXT DMARC em `_dmarc.` (o valor do DKIM é gerado pelo Resend).
- **Alternativa para eu automatizar**: gerar uma API key do Resend com **Full access**
  (a key atual é só de envio, não lê `/domains`).

### 5.2 HTTPS do GitHub Pages
- Certificado em emissão. Quando estiver pronto: ativar **Enforce HTTPS**
  (`gh api --method PUT /repos/Leon-Roza/triade/pages -f cname=usetriade.com.br -F https_enforced=true`)
  e conferir `https://usetriade.com.br`.

### 5.3 Segurança (fazer quando encerrar os testes)
- **Revogar**: PAT do Supabase (Account → Access Tokens) e API key do Render
  (dashboard.render.com/u/settings/api-keys) — foram expostas no chat.
- **Rotacionar**: Access Token e secret do Mercado Pago; API key do Resend.
- Senha do banco Supabase: redefinível no painel; **não** está neste arquivo.

### 5.4 Ajustes opcionais
- Resetar o plano do usuário de teste (`leonrozd@gmail.com`) de `pro` para `free`, se quiser.
- Conferir no painel do Mercado Pago o **webhook** cadastrado:
  `https://triade-api-rkfd.onrender.com/webhooks/mercadopago` (evento *Payments*).
- Reativar a análise de YouTube no detector (código em `server/app.py`, hoje desconectado do site).

---

## 6. Como retomar (checklist)

1. Verificar DNS do domínio no Resend → Resend **Verify** → testar magic link.
2. Se o login por e-mail funcionar, testar login real e o gating Free/Pro no site.
3. Conferir HTTPS do GitHub Pages e ativar Enforce HTTPS.
4. Revogar/rotacionar tokens.
5. (Opcional) configurar e testar a análise de YouTube.

---

## 7. Comandos úteis

```powershell
# Publicar alterações do site
git add index.html; git commit -m "update"; git push

# Redeploy do backend no Render (usar a API key do Render)
# POST https://api.render.com/v1/services/srv-db1s405g1s2s73biaqg0/deploys

# Status do GitHub Pages
gh api /repos/Leon-Roza/triade/pages --jq '{cname,status,https_enforced}'
```

Teste de pagamento (sandbox): no backend, definir env `MP_SANDBOX=1` + usar token de
**usuário de teste**; o `init_point` vira `sandbox_init_point`. Depois remover `MP_SANDBOX`
e restaurar o token de produção.

---

## 8. Onde ficam as credenciais (não estão aqui)

| Credencial | Onde |
|---|---|
| Supabase URL / anon key | `index.html` (`CONFIG`) e painel Supabase → Settings → API |
| Supabase service_role | Render env `SUPABASE_SERVICE_ROLE_KEY` |
| Mercado Pago token/secret | Render env `MP_ACCESS_TOKEN`, `MP_WEBHOOK_SECRET`; painel MP |
| Resend API key | Render/Supabase SMTP (pass) e painel Resend |
| Render API key | painel Render |
| Senha do banco | painel Supabase (redefinível) |

---

## 9. Compositor (`compositor.html`) — recursos

Página dedicada (link no cabeçalho do site e card "Modo compositor"). Reproduz a melodia
com banda de acompanhamento, com features inspiradas no **Band-in-a-Box**.

**Teoria e melodia**
- Tonalidade (12), **Escalas** (maior, menor natural/harmônica/melódica, pentatônicas, blues, cromática)
  e **Modos gregos** (jônio, dórico, frígio, lídio, mixolídio, eólio, lócrio).
- **Técnicas de guitarra**: palm mute, bend, slide, hammer/pull, vibrato, harmônico (no som, na tab e no MIDI).
- **Harmonia da melodia** (voz diatônica): 3ª/6ª/8ª acima/abaixo.
- Densidade, registro, estilo (cantável/arpejado/saltos/pentatônica).
- **Acordes**: Tríades ou **Sétimas** (7M/7/m7/m7b5). Botão **Reharmonizar** (substituições diatônicas).

**Forma e arranjo**
- **Formas**: Unária, Binária, Ternária, Rondó, Tema e Variações, Cânone, Invenção, Fuga, Prelúdio,
  Fantasia, Tocata, Poema Sinfônico, Rapsódia, Sonata, Sinfonia/Suíte.
- **Intro/Final** de 2 compassos; **Push** (antecipação); **Acentos** (holds/rests/shots por compasso);
  **Repetições (chorus)** 1–4x; **sub-estilos A/B** (seções B/C/D mais cheias).
- Letras de seção (A/B/C/I/F) marcadas na tablatura.

**Banda, groove e mix**
- Instrumentos: **melodia** (guitarra Karplus-Strong), **pad/teclado** (synth **ou piano amostrado CC0**),
  **baixo** (samples CC0 dsmolken pizzicato), **bateria** (samples CC0 Virtuosity Drums, com camadas).
- **Editor de forma**: sequência de seções editável (Verso/Refrão/Ponte/Solo/Intro/Final) + **casas 1ª/2ª** (fim alternativo).
- **Song Builder**: arranjos completos por estilo — Pop, Rock, Rock & Roll, Metal, **Black Metal**, **Psytrance**,
  **Progressive Psy**, **Dark Progressive Psy**, Trance melódico, Balada e Blues — com estrutura
  (intro/verso/refrão/ponte/solo/final), **bateria de gênero** (4x4, psy, dark psy, metal, blast beat) e
  **baixo offbeat** (rolling bass) no psy/trance.
- **Mixer**: volume por trilha + **Pan** por trilha + **Reverb** (bus com convolução).
- **Humanizar** (variação de tempo/intensidade), **Swing**, **Contagem** (count-in).
- **Andamento** (Largo→Presto + slider), **Compasso** (4/4, 3/4, 2/4), **Loop**.

**Som e saída**
- Síntese de corda (Karplus-Strong) para guitarra/violão, com **distorção**.
- **Tablatura horizontal rolante** (estilo Guitar Pro) com acordes, casas e marcadores de técnica.
- **Export**: Tab (`.txt`) e **MIDI** (4 trilhas: melodia, acompanhamento, e percussão no canal 10).
- Composições salvas (localStorage `triade_comps`).

**Samples (CC0)** — ver `samples/CREDITS.md`:
- `samples/drums/*.wav` — Virtuosity Drums (bumbo, caixa, chimbais, pratos, tons) em camadas.
- `samples/bass/*.wav` — dsmolken double-bass pizzicato (11 notas, mapeadas por afinação).
- `samples/piano/*.wav` — VCSL Grand Piano Kawai (36 notas, mapeadas por afinação).

**Próximos possíveis (ainda não feitos):** mais RealTracks (cordas/cello amostrados), notação em partitura
além da tablatura, e estilos de banda nomeados.
