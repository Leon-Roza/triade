# TRÍADE — Ativar login real e pagamento (passo a passo)

Com tudo configurado, o login passa a ser real (Supabase) e o **plano Pro é
liberado automaticamente** após o pagamento no Mercado Pago.

Enquanto você não preencher as chaves, o site funciona em **modo demo**
(conta local + links de pagamento diretos) — nada quebra.

---

## 1. Supabase (login real)

1. Crie um projeto em https://supabase.com.
2. **SQL Editor → New query**, cole o conteúdo de `server/supabase.sql` e **Run**.
3. **Authentication → URL Configuration**:
   - **Site URL**: `https://usetriade.com.br`
   - **Redirect URLs**: adicione `https://usetriade.com.br/**`
4. **Project Settings → API**, copie:
   - **Project URL** (ex.: `https://xxxx.supabase.co`)
   - **anon public key**
   - **service_role key** (guardar — usada só no backend)

O login é por **magic link** (sem senha): o usuário digita o e-mail e recebe um
link de acesso.

---

## 2. Front-end (`index.html`)

No topo do `<script>`, preencha:

```js
const CONFIG = {
  backend: 'https://triade-api-rkfd.onrender.com',   // seu backend no Render
  supabaseUrl: 'https://xxxx.supabase.co',
  supabaseAnonKey: 'COLE_A_ANON_KEY'
};
```

> A **anon key** é pública por design (protegida por RLS). A **service_role**
> NUNCA vai no front — só no backend.

---

## 3. Mercado Pago (receber pagamentos)

1. Acesse https://www.mercadopago.com.br/developers/panel → sua aplicação.
2. Copie o **Access Token** (Produção).
3. Em **Webhooks/Notificações**, cadastre a URL:
   `https://SEU-BACKEND.onrender.com/webhooks/mercadopago`
   e marque o evento **Payments**.
4. Copie a **chave secreta (secret)** do webhook (para validar a assinatura).

---

## 4. Backend no Render (variáveis de ambiente)

No serviço `triade-api` → **Environment**, adicione:

| Variável | Valor |
|---|---|
| `MP_ACCESS_TOKEN` | token de produção do Mercado Pago |
| `MP_WEBHOOK_SECRET` | secret do webhook do Mercado Pago |
| `BACKEND_URL` | `https://triade-api-rkfd.onrender.com` |
| `SITE_URL` | `https://usetriade.com.br` |
| `SUPABASE_URL` | Project URL do Supabase |
| `SUPABASE_SERVICE_ROLE_KEY` | service_role key do Supabase |

Salve → o Render faz o redeploy. O endpoint `POST /checkout` cria a preferência
de pagamento e o `POST /webhooks/mercadopago` ativa o plano do usuário.

---

## 5. Fluxo completo (como vai funcionar)

1. Usuário clica em **Entrar** → recebe magic link → logado (perfil criado).
2. Clica em **Assinar Pro** → backend cria o checkout → Mercado Pago.
3. Pagamento aprovado → Mercado Pago chama o webhook → backend grava
   `plan = 'pro'` e `expires_at` no Supabase.
4. No próximo acesso o site lê o plano e **libera** análise ilimitada,
   salvar sem limite e exportação (cifra/PDF/JSON).

---

## 6. Ativação manual (fallback, sem webhook)

Para liberar alguém na mão: **Supabase → Table Editor → profiles** e edite
`plan` (`pro`/`studio`) e `expires_at`. Útil para testes e primeiros clientes
do Studio.

---

## 7. Limites por plano (já implementados no site)

| Recurso | Free | Pro / Studio |
|---|---|---|
| Disco harmônico, progressões, timbres, braço | ✅ | ✅ |
| Análise de harmonia por áudio | 3 por sessão | ilimitada |
| Salvar progressões | até 3 | ilimitado |
| Exportar (cifra/PDF/JSON) | ❌ | ✅ |

> Ajuste os limites em `analyzeFile`, `savePreset` e `requirePro` no `index.html`,
> se quiser mudar a régua.
