'use strict';

const express = require('express');
const fs = require('fs').promises;
const path = require('path');

const PORT = process.env.PORT || 3001;
const DIR = __dirname;
const COMMENTS_PATH = path.join(DIR, 'comments.json');
const LIKES_PATH = path.join(DIR, 'likes.json');

const app = express();

app.use((req, res, next) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,POST,OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') return res.sendStatus(204);
  next();
});

app.use(express.json({ limit: '64kb' }));

function safeSlug(s) {
  const t = String(s || '').trim();
  return /^[a-zA-Z0-9_-]{1,128}$/.test(t) ? t : null;
}

async function readJson(p, fallback) {
  try {
    return JSON.parse(await fs.readFile(p, 'utf8'));
  } catch {
    return fallback;
  }
}

async function writeJson(p, data) {
  await fs.writeFile(p, JSON.stringify(data, null, 2), 'utf8');
}

async function ensureStore() {
  for (const p of [COMMENTS_PATH, LIKES_PATH]) {
    try {
      await fs.access(p);
    } catch {
      await writeJson(p, {});
    }
  }
}

app.get('/api/comments/:slug', async (req, res) => {
  const slug = safeSlug(req.params.slug);
  if (!slug) return res.status(400).json({ error: 'Invalid slug' });
  await ensureStore();
  const all = await readJson(COMMENTS_PATH, {});
  const list = Array.isArray(all[slug]) ? all[slug] : [];
  res.json(list);
});

app.post('/api/comment/:slug', async (req, res) => {
  const slug = safeSlug(req.params.slug);
  if (!slug) return res.status(400).json({ error: 'Invalid slug' });
  const name = typeof req.body?.name === 'string' ? req.body.name.trim() : '';
  const message = typeof req.body?.message === 'string' ? req.body.message.trim() : '';
  if (!name || !message) return res.status(400).json({ error: 'Name and message required' });

  await ensureStore();
  const all = await readJson(COMMENTS_PATH, {});
  if (!Array.isArray(all[slug])) all[slug] = [];
  const entry = { name, message, timestamp: new Date().toISOString() };
  all[slug].push(entry);
  await writeJson(COMMENTS_PATH, all);
  res.status(201).json(entry);
});

app.get('/api/likes/:slug', async (req, res) => {
  const slug = safeSlug(req.params.slug);
  if (!slug) return res.status(400).json({ error: 'Invalid slug' });
  await ensureStore();
  const likes = await readJson(LIKES_PATH, {});
  const count = Number(likes[slug]) || 0;
  res.json({ slug, count });
});

app.post('/api/like/:slug', async (req, res) => {
  const slug = safeSlug(req.params.slug);
  if (!slug) return res.status(400).json({ error: 'Invalid slug' });
  await ensureStore();
  const likes = await readJson(LIKES_PATH, {});
  const next = (Number(likes[slug]) || 0) + 1;
  likes[slug] = next;
  await writeJson(LIKES_PATH, likes);
  res.json({ slug, count: next });
});

app.use((req, res) => res.status(404).json({ error: 'Not found' }));

ensureStore()
  .then(() => {
    app.listen(PORT, () => {
      console.log('listening on', PORT);
    });
  })
  .catch((e) => {
    console.error(e);
    process.exit(1);
  });
