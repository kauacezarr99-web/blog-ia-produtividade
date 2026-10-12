# Produtividade IA — Blog de Afiliados

Blog de conteúdo sobre **ferramentas de IA para produtividade**, gerado estático (stdlib, sem dependências) e publicado no **GitHub Pages** (hospedagem 100% gratuita).

Motor: skill `automated-content-site`. Um cron do Hermes publica 1 artigo a cada 4 horas.

## Estrutura

```
blog-ia-produtividade/
├─ build.py       # gerador estático (stdlib only)
├─ config.json    # nome, niches, amazon_tag, shareasale_id
├─ content/       # artigos em .md
├─ autorun.sh     # rebuild + git push (crash-proof)
└─ public/        # saída (HTML, sitemap.xml, feed.xml, disclosure.html)
```

## ID de afiliado

`amazon_tag` em `config.json` → **`kauaiaproduti-20`**
Toda ocorrência de `{{AMAZON:palavra-chave}}` nos artigos vira:

`https://www.amazon.com/s?k=...&tag=kauaiaproduti-20`

## As 3 coisas que SÓ o dono do repositório consegue fazer

1. **Publicar no GitHub Pages (grátis):**
   - criar repo público no GitHub;
   - `git remote add origin https://github.com/<SEU_USUARIO>/blog-ia-produtividade.git`
   - `git push -u origin main`
   - ativar Pages (Settings → Pages → branch main) e atualizar `site_url` em `config.json`.

2. **Amazon Associates:** o ID `kauaiaproduti-20` já está no config. Confirme na sua conta Amazon que o tag está ativo.

3. **Tráfego:** sem tráfego não há comissão. Publique os links dos artigos no Reddit, X, Quora e Pinterest.
