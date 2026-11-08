# Polylang translate server (Cloudflare Worker, free)

The Google Translate key lives here as a secret, never in the website. The site sends text to this Worker, and the Worker asks Google.

- Only requests from `jakesauter.github.io` (and the Claude preview) are accepted.
- Text is limited to 300 characters per request, and only Polylang's languages are allowed.
- Repeat translations are cached for 30 days, so they don't use Google quota again.
- `GET /tatoeba?lang=spa&q=hola` relays Tatoeba example sentences (cached 7 days). The app only uses it if the phone can't reach Tatoeba directly.
- Cost: Cloudflare Workers' free plan covers 100,000 requests a day. Google stays at $0 because of the daily character quota you set in Google Cloud.

## Deploy from the Cloudflare dashboard (no installs)

1. Sign up at dash.cloudflare.com. The free plan is enough and no card is needed.
2. Go to **Workers & Pages › Create › Create Worker**, name it `polylang-translate`, and click **Deploy**.
3. Click **Edit code**, replace everything with the contents of `worker.js`, and click **Deploy**.
4. Go to **Settings › Variables and Secrets › Add**, choose type **Secret**, name it `GOOGLE_KEY`, paste your Google API key, and deploy.
5. Copy the Worker's address, for example `https://polylang-translate.<your-name>.workers.dev`, and send it to Claude. It goes into `GT_PROXY` in the app and is not secret.

## Or deploy with the command line

    npm install -g wrangler
    wrangler login
    cd server/cloudflare
    wrangler deploy
    wrangler secret put GOOGLE_KEY

## Google side

- **Key restrictions:** under API restrictions, allow Cloud Translation API only. Leave **Application restrictions** at **None**, because requests now come from Cloudflare, not a browser.
- **Hard cap:** under IAM & Admin › Quotas › Cloud Translation API, set "v2 and v3 general model characters per day" to 15,000. That keeps you under the free 500,000 characters a month.
- **Alert (optional):** add a $1 billing budget so you get an email if anything is ever charged.
