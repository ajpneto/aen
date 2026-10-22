# AENTECH — Assistência Técnica de Celulares e Tablets

Aplicação web estática em **HTML5**, **CSS3** e **JavaScript**, totalmente otimizada para o **GitHub Pages**, vinculada ao domínio próprio **fazhoje.com** (Squarespace), com **SEO avançado para motores de busca** e **Open Graph completo para compartilhamento em redes sociais e WhatsApp**.

---

## 🚀 Tecnologias & Características

- **100% Estático:** Apenas HTML5, CSS3 e JavaScript puro (sem necessidade de backend, Python ou hospedagem paga).
- **Hospedagem Gratuita:** GitHub Pages com alta disponibilidade, CDN mundial e certificado SSL/HTTPS automático.
- **SEO & Busca Local (Ourinhos - SP):**
  - Meta tags completas (`description`, `keywords`, `robots`, `canonical`).
  - Geotagging para Ourinhos - SP (`geo.region`, `geo.placename`, `geo.position`, `ICBM`).
  - Schema.org (JSON-LD) com dados estruturados de `LocalBusiness` e `FAQPage` para indexação rica no Google.
  - Arquivos `robots.txt` e `sitemap.xml` prontos para o Google Search Console e Bing Webmaster.
- **Open Graph (WhatsApp, Facebook, LinkedIn, Twitter/X):**
  - URLs absolutas em HTTPS com imagem (`static/og-brand.png`) dimensionada em 1200x630 (abaixo de 300KB, formato ideal para WhatsApp).
  - Twitter Card configurado com `summary_large_image`.
- **PWA & Ícones:**
  - `site.webmanifest` integrado com ícones para Android e iOS (`apple-touch-icon`).
  - Favicon em múltiplos tamanhos (16x16, 32x32, 192x192, 512x512).
- **Página de Erro 404:**
  - `404.html` personalizada para links quebrados com redirecionamento para o início e WhatsApp.

---

## 🌐 Configuração do Domínio do Squarespace no GitHub Pages

Para conectar o domínio **fazhoje.com** ao GitHub Pages:

### 1. No painel do Squarespace (DNS)

Acesse: **Squarespace** > **Domínios** > **fazhoje.com** > **Configurações de DNS** (ou DNS Settings).

Adicione os seguintes registros:

#### A) Registros `A` (para o domínio raiz `fazhoje.com`):
Crie 4 registros do tipo **A**:
| Tipo | Host / Nome | Aponta para (IP) |
| :--- | :--- | :--- |
| **A** | `@` | `185.199.108.153` |
| **A** | `@` | `185.199.109.153` |
| **A** | `@` | `185.199.110.153` |
| **A** | `@` | `185.199.111.153` |

#### B) Registro `CNAME` (para o subdomínio `www`):
| Tipo | Host / Nome | Aponta para |
| :--- | :--- | :--- |
| **CNAME** | `www` | `ajpneto.github.io.` |

---

### 2. No repositório GitHub

1. Acesse o repositório no GitHub: [https://github.com/ajpneto/aen](https://github.com/ajpneto/aen)
2. Clique em **Settings** (Configurações) > **Pages** (no menu lateral).
3. Na seção **Build and deployment**:
   - **Source:** Escolha `Deploy from a branch`.
   - **Branch:** `main` | pasta: `/ (root)` > clique em **Save**.
   *(O repositório também inclui `.github/workflows/pages.yml` se preferir a opção GitHub Actions).*
4. Em **Custom domain**:
   - Confirme `fazhoje.com` e clique em **Save** (o arquivo `CNAME` na raiz do projeto já define essa configuração).
5. Após o DNS propagar, marque a opção **Enforce HTTPS** para ativar o certificado SSL gratuito.

---

## 📱 Dica para Prévia no WhatsApp

O WhatsApp armazena em cache o link ao ser enviado pela primeira vez. Se você testar e não carregar a imagem imediatamente:

1. Acesse o [Facebook Sharing Debugger](https://developers.facebook.com/tools/debug/) (ferramenta oficial do mesmo motor do WhatsApp).
2. Insira `https://fazhoje.com` e clique em **Scrape Again** para limpar o cache.
3. No WhatsApp, você também pode compartilhar com um parâmetro para forçar atualização instantânea: `https://fazhoje.com/?v=1`.

---

## 💻 Teste Local Simples

Para testar no seu computador com qualquer servidor local:

```bash
# Com Python (já nativo no sistema):
python3 -m http.server 8000

# Ou usando Node.js (npx serve):
npx serve
```

Abra no navegador em: `http://localhost:8000`

---

## 📁 Estrutura de Arquivos

```text
├── .github/
│   └── workflows/
│       └── pages.yml       # Deploy automatizado no GitHub Pages
├── static/
│   ├── css/
│   │   └── style.css       # Estilos CSS
│   ├── js/
│   │   └── main.js        # Scripts JS (scroll, animações)
│   ├── favicon.ico
│   ├── favicon-16x16.png
│   ├── favicon-32x32.png
│   ├── apple-touch-icon.png
│   ├── android-chrome-192x192.png
│   ├── android-chrome-512x512.png
│   └── og-brand.png        # Imagem para OpenGraph / WhatsApp (1200x630)
├── .gitignore
├── .nojekyll               # Desativa processamento Jekyll no GitHub Pages
├── 404.html                # Página de erro 404 estilizada
├── CNAME                   # Domínio próprio (fazhoje.com)
├── index.html              # Página principal (HTML5 + Schema.org + OpenGraph)
├── README.md               # Documentação do projeto
├── robots.txt              # Regras para bots e indexadores
├── site.webmanifest        # PWA e ícones mobile
└── sitemap.xml             # Sitemap XML para motores de busca
```
