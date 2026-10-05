# TRÍADE — Roadmap: domínio próprio, hospedagem e vendas

> Plano prático para transformar o site em um produto pago, com domínio próprio,
> backend de análise e canais de aquisição.

---

## 1. Posicionamento

**O que é:** ferramenta de harmonia para guitarristas e violonistas — disco/campo
harmônico, geração de progressões, timbres de violão/guitarra e detecção de
acordes por áudio.

**Promessa:** “Descubra a harmonia de qualquer música e toque o campo harmônico
certo em segundos.”

**Público:** autodidatas, alunos de professores, igrejas, compositores, criadores
de conteúdo de música.

**Diferencial:** tudo no navegador (sem instalar), som sintetizado que parece
corda de verdade e detecção por áudio.

---

## 2. Domínio e hospedagem (passo a passo)

### 2.1 Registrar o domínio
- Prefira um nome curto e memorável: `triade.app`, `usetriade.com`, `triade.com.br`.
- **.com.br**: Registro.br (~R$ 40/ano, exige CPF/CNPJ).
- **.com / .app**: Cloudflare Registrar (preço de custo) ou Namecheap/Porkbun.
- Evite renovação caríssima de primeira compra; confira o preço de renovação.

### 2.2 DNS + proteção (grátis)
- Aponte os nameservers para o **Cloudflare** (proxy, CDN, SSL e cache grátis).
- Mantém o site rápido no Brasil e esconde o IP de origem.

### 2.3 Front-end (site) — GitHub Pages com domínio próprio
1. No repositório, crie o arquivo `CNAME` (na raiz) com o domínio, ex.: `triade.app`.
2. No Render/GH: **Settings → Pages → Custom domain** → informe o domínio.
3. No Cloudflare:
   - Domínio raiz (`triade.app`): registros **A** para `185.199.108.153`,
     `185.199.109.153`, `185.199.110.153`, `185.199.111.153`.
   - Subdomínio (`www` / `app`): **CNAME** para `leon-roza.github.io`.
4. Ative **Enforce HTTPS** no GitHub Pages.
- **Alternativa mais robusta:** migrar o front para **Netlify** ou **Vercel**
  (deploy automático, redirects, headers). Recomendado quando houver login/áreas pagas.

### 2.4 Backend de análise — subdomínio próprio
- Serviço já pronto em `server/` (Docker + FastAPI + yt-dlp).
- Deploy no Render e depois **Custom Domain** `api.triade.app` (CNAME no Cloudflare).
- Vá para um plano pago quando vender (>0,5 GB RAM evita hibernação e filas).

### 2.5 E-mail profissional
- **Zoho Mail** (plano grátis com domínio próprio) ou **Google Workspace** (pago).
- Endereços: `contato@`, `suporte@`, `vendas@`.

### 2.6 Pagamentos
- **Kiwify / Hotmart / Cakto**: mais simples no Brasil (Pix, cartão, boleto,
  assinatura, retenção de imposto e nota fiscal pela plataforma).
- **Stripe / Mercado Pago**: mais controle, exige mais configuração.
- Assinatura recorrente para Pro; plano Studio com link de “fale com vendas”.

### 2.7 Analytics e SEO
- **Cloudflare Analytics** (grátis) ou **Plausible** (pago, sem cookies).
- **Google Search Console** + **sitemap.xml** + `robots.txt`.
- Eventos-chave: clique em plano, início de análise, conversão.

### 2.8 Custo mensal estimado (início)
| Item | Custo |
|---|---|
| Domínio (.app/.com) | ~R$ 50/ano |
| GitHub Pages / Cloudflare | R$ 0 |
| Render backend (free) | R$ 0 (dorme) |
| Zoho Mail | R$ 0 |
| Plataforma de pagamento | % por venda |
| **Total** | **~R$ 5/mês + comissões** |

---

## 3. Roadmap por fases

### Fase 0 — Fundação (Semana 1)
- [ ] Registrar domínio + Cloudflare.
- [ ] Publicar o site no domínio próprio (HTTPS ativo).
- [ ] E-mail `contato@` e `suporte@`.
- [ ] Google Search Console + sitemap.
- [ ] Página de **Planos** no ar (já incluída no site).

### Fase 1 — MVP vendável (Semanas 2–4)
- [ ] Checkout de **assinatura** (Kiwify/Hotmart) para o plano Pro.
- [ ] Login simples (magic link / Auth0 / Clerk) + área do usuário.
- [ ] Botão “Assinar” apontando para o checkout (hoje é `mailto:`).
- [ ] Termos de uso e Política de Privacidade (LGPD).
- [ ] Primeiros 20 beta testers (preço fundador).

### Fase 2 — Produto (Mês 2–3)
- [ ] Reativar detecção por **YouTube** (backend + cookies/proxy).
- [ ] Salvar/organizar progressões na conta.
- [ ] **Exportar** cifra, PDF e tablatura.
- [ ] Afinador e metrônomo avançado.
- [ ] Painel do professor (plano Studio).

### Fase 3 — Growth (Mês 3–6)
- [ ] SEO: artigos (“campo harmônico de dó maior”, “como saber o tom de uma música”).
- [ ] Vídeos curtos (YouTube Shorts, TikTok, Instagram Reels) com o site em uso.
- [ ] Programa de **afiliados** (Kiwify/Hotmart já suportam).
- [ ] Parcerias com professores e canais de guitarra/violão.
- [ ] Prova social: depoimentos, casos, comunidade (Discord/WhatsApp).
- [ ] Testes A/B de preço e da página de planos.

### Fase 4 — Escala (Mês 6+)
- [ ] App instalável (PWA) e depois mobile.
- [ ] Plano anual com desconto como padrão.
- [ ] White-label para escolas/igrejas.
- [ ] Ads pagos (Meta/Google) só depois de validar conversão.
- [ ] Suporte automatizado + base de conhecimento.

---

## 4. Estratégia de vendas

**Aquisição (topo):**
- **SEO** de intenção (“tom de”, “campo harmônico de”, “acordes de”).
- **Vídeo curto** mostrando “colei o áudio → saiu a progressão” (efeito UAU).
- **Lead magnet:** versão grátis como isca; capturar e-mail.

**Conversão (meio):**
- Grátis generoso → limite natural (análises ilimitadas só no Pro).
- Página de planos clara, prova social e garantia de 7 dias.
- Onboarding em 1 clique: primeira análise em < 60s.

**Retenção (fundo):**
- Sequência de e-mails (dicas de harmonia + features novas).
- Progressões salvas criam lock-in.
- Comunidade e desafios semanais.

**Canais prioritários:** YouTube/TikTok/Reels, parcerias com professores,
grupos de música, comunidades de igrejas, indicação.

---

## 5. Métricas (KPIs)
- **MRR** (receita recorrente) e **ARR**.
- **Conversão** free → pago (meta inicial 2–5%).
- **Churn** mensal (manter < 6%).
- **CAC** x **LTV** (LTV ≥ 3× CAC).
- Ativação: % que faz a 1ª análise ou abre o disco harmônico.

---

## 6. Riscos e mitigação
| Risco | Mitigação |
|---|---|
| YouTube bloqueia IP do servidor | Cookies + proxy residencial; limite de uso no Pro |
| Direitos autorais (áudio do usuário) | Análise local no navegador; termos claros; não redistribuir áudio |
| Free tier “dorme” / lento | Migrar para plano pago conforme volume |
| Concorrência (apps de cifra) | Foco em didática + som real + progressões |
| Fiscal/legal (Brasil) | Abrir **MEI**, usar plataforma que emite NF, LGPD |

---

## 7. Próximos passos imediatos (esta semana)
1. Registrar o domínio e apontar para o GitHub Pages (seção 2.3).
2. Escolher a plataforma de pagamento e criar o link de checkout do Pro.
3. Trocar os links `mailto:` dos planos pelo checkout real.
4. Publicar 3 vídeos curtos demonstrando o site.
5. Definir e-mail e publicar Termos + Privacidade.
