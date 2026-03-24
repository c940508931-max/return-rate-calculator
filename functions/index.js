const { https } = require('firebase-functions');
const fetch = require('node-fetch');

const FEISHU_APP_ID = 'cli_a928e28f0ff6dbca';
const FEISHU_APP_SECRET = 'nc7WEIwxiLrB72ID0T4RygVp45CuNQcj';
const SPREADSHEET_TOKEN = 'XheSscvcBhMURPtzrxocDp3NnFg';
const SHEET_ID = '5c7d0c';

let cachedToken = null;
let tokenExpiry = 0;

async function getFeishuToken() {
  if (cachedToken && Date.now() < tokenExpiry) return cachedToken;
  const url = 'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal';
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ app_id: FEISHU_APP_ID, app_secret: FEISHU_APP_SECRET })
  });
  const data = await res.json();
  if (data.code !== 0) throw new Error('Feishu token error: ' + data.msg);
  cachedToken = data.tenant_access_token;
  tokenExpiry = Date.now() + (data.expire - 60) * 1000;
  return cachedToken;
}

async function getReturnRates(req, res) {
  res.set('Access-Control-Allow-Origin', '*');
  res.set('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.set('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(204).send('');
  }

  try {
    const token = await getFeishuToken();
    const range = `${SHEET_ID}!B2:M100`;
    const apiUrl = `https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/${SPREADSHEET_TOKEN}/values/${encodeURIComponent(range)}?valueRenderOption=FormattedValue`;

    const fres = await fetch(apiUrl, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const fdata = await fres.json();

    if (fdata.code !== 0) {
      return res.status(500).json({ error: 'Feishu API error: ' + fdata.msg });
    }

    const rows = fdata.data?.valueRange?.values || [];
    const result = {};
    for (const r of rows) {
      if (r && r.length > 11 && r[0] && r[11] && typeof r[11] === 'string' && r[11].includes('%')) {
        const code = String(r[0]).trim();
        const pct = parseFloat(r[11].replace('%', ''));
        if (code && !isNaN(pct)) result[code] = pct;
      }
    }

    return res.json(result);
  } catch (err) {
    console.error('Error:', err.message);
    return res.status(500).json({ error: err.message });
  }
}

exports.getFeishuReturnRates = https.onRequest(getReturnRates);
