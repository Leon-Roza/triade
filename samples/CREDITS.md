# Créditos dos samples

Samples usados no **Modo Compositor** (`samples/`). Todos livres para uso pessoal e comercial.

## Bateria — `samples/drums/`
- **Virtuosity Drums** (Versilian Studios & Karoryfer Samples) — **CC0 1.0 (domínio público)**.
- https://github.com/sfzinstruments/virtuosity_drums
- Convertido de FLAC→WAV mono, com camadas de intensidade.

## Baixo — `samples/bass/`
- **dsmolken — Rubner double bass (pizzicato)** — **CC0 1.0 (domínio público)**.
- https://github.com/sfzinstruments/dsmolken_rubner_bass (compilado em `danigb/samples`)
- 11 notas (C1–A3) mapeadas por afinação.

## Piano — `samples/piano/`
- **VCSL — Grand Piano, Kawai** (Versilian Community Sample Library) — **CC0 1.0**.
- https://github.com/sgossner/VCSL (compilado em `danigb/samples`)
- 36 notas (camada média) mapeadas por afinação.

> Guitarras/violão e o pad "Synth" são **sintetizados** (Karplus-Strong / osciladores) — sem samples.

### Como foram feitos
Os arquivos `.ogg`/`.flac` originais foram baixados, convertidos para **WAV mono** (Python `soundfile`),
recortados (sem silêncio excedente) e com a dinâmica preservada.
