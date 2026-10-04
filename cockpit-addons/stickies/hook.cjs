// 付箋（スティッキーノート）アドオン — サーバー側フック
//
// server.js の先頭で require するだけで動く。Next.js のビルド成果物には手を入れず、
// http.createServer をラップして次の3つを追加する。
//   GET/PUT /api/stickies      … data/stickies.json の読み書き
//   GET     /stickies/*.js|css … このフォルダの静的ファイル
//   HTML 応答の末尾に <script src="/stickies/stickies.js"> を差し込む
const http = require("http");
const fs = require("fs");
const path = require("path");

const ADDON_DIR = __dirname;
const DATA_DIR = path.join(process.cwd(), "data");
const DATA_FILE = path.join(DATA_DIR, "stickies.json");
const MAX_BODY = 1024 * 1024;
const STATIC = {
  "/stickies/stickies.js": ["stickies.js", "text/javascript; charset=utf-8"],
  "/stickies/stickies.css": ["stickies.css", "text/css; charset=utf-8"],
};
const INJECT = '<link rel="stylesheet" href="/stickies/stickies.css"><script src="/stickies/stickies.js" defer></script>';

function readNotes() {
  try {
    const data = JSON.parse(fs.readFileSync(DATA_FILE, "utf8"));
    return Array.isArray(data.notes) ? data : { notes: [] };
  } catch {
    return { notes: [] };
  }
}

function writeNotes(data) {
  if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR, { recursive: true });
  const tmp = DATA_FILE + ".tmp";
  fs.writeFileSync(tmp, JSON.stringify(data, null, 2), "utf8");
  fs.renameSync(tmp, DATA_FILE);
}

function sanitize(input) {
  const notes = Array.isArray(input && input.notes) ? input.notes : [];
  const num = (v, d) => (Number.isFinite(v) ? Math.round(v) : d);
  return {
    notes: notes.slice(0, 200).map((n) => ({
      id: String(n.id || "").slice(0, 64),
      text: String(n.text || "").slice(0, 10000),
      color: ["yellow", "pink", "blue", "green", "purple"].includes(n.color) ? n.color : "yellow",
      x: num(n.x, 80),
      y: num(n.y, 120),
      w: Math.max(160, Math.min(800, num(n.w, 220))),
      h: Math.max(120, Math.min(800, num(n.h, 180))),
      z: num(n.z, 1),
      updatedAt: String(n.updatedAt || new Date().toISOString()).slice(0, 40),
    })).filter((n) => n.id),
    hidden: Boolean(input && input.hidden),
  };
}

function sendJson(res, status, body) {
  const text = JSON.stringify(body);
  res.writeHead(status, {
    "Content-Type": "application/json; charset=utf-8",
    "Cache-Control": "no-store",
    "Content-Length": Buffer.byteLength(text),
  });
  res.end(text);
}

function handleApi(req, res) {
  if (req.method === "GET") return sendJson(res, 200, readNotes());
  if (req.method !== "PUT") return sendJson(res, 405, { error: "method not allowed" });
  let size = 0;
  const chunks = [];
  req.on("data", (c) => {
    size += c.length;
    if (size > MAX_BODY) req.destroy();
    else chunks.push(c);
  });
  req.on("end", () => {
    try {
      const data = sanitize(JSON.parse(Buffer.concat(chunks).toString("utf8")));
      writeNotes(data);
      sendJson(res, 200, data);
    } catch (e) {
      sendJson(res, 400, { error: String(e && e.message) });
    }
  });
}

function handleStatic(req, res, [file, type]) {
  fs.readFile(path.join(ADDON_DIR, file), (err, buf) => {
    if (err) return sendJson(res, 404, { error: "not found" });
    res.writeHead(200, { "Content-Type": type, "Cache-Control": "no-cache", "Content-Length": buf.length });
    res.end(buf);
  });
}

// ページ本体の HTML 応答にだけタグを差し込む。圧縮されると末尾に足せないので
// その要求だけ Accept-Encoding を外し、Content-Length も付けさせない。
function wantsHtml(req) {
  return req.method === "GET" && !req.headers["rsc"] && /text\/html/.test(req.headers["accept"] || "");
}

function injectHtml(req, res) {
  delete req.headers["accept-encoding"];
  const isHtml = () => /text\/html/.test(String(res.getHeader("content-type") || ""));
  const origSetHeader = res.setHeader.bind(res);
  res.setHeader = (name, value) => {
    if (String(name).toLowerCase() === "content-length" && isHtml()) return res;
    return origSetHeader(name, value);
  };
  const origWriteHead = res.writeHead.bind(res);
  res.writeHead = (status, ...rest) => {
    const headers = rest.find((r) => r && typeof r === "object" && !Array.isArray(r));
    if (headers) {
      const ct = Object.keys(headers).find((k) => k.toLowerCase() === "content-type");
      if (ct && /text\/html/.test(String(headers[ct]))) {
        for (const k of Object.keys(headers)) if (k.toLowerCase() === "content-length") delete headers[k];
      }
    }
    if (isHtml()) res.removeHeader("content-length");
    return origWriteHead(status, ...rest);
  };
  const origEnd = res.end.bind(res);
  res.end = (chunk, encoding, cb) => {
    if (typeof chunk === "function") [cb, chunk] = [chunk, undefined];
    if (typeof encoding === "function") [cb, encoding] = [encoding, undefined];
    if (isHtml() && res.statusCode < 400 && req.method !== "HEAD") {
      if (chunk != null) res.write(chunk, encoding);
      return origEnd(INJECT, "utf8", cb);
    }
    return origEnd(chunk, encoding, cb);
  };
}

function wrap(listener) {
  return function stickiesListener(req, res) {
    const url = (req.url || "").split("?")[0];
    if (url === "/api/stickies") return handleApi(req, res);
    if (STATIC[url]) return handleStatic(req, res, STATIC[url]);
    if (wantsHtml(req)) injectHtml(req, res);
    return listener.call(this, req, res);
  };
}

const origCreateServer = http.createServer;
http.createServer = function (...args) {
  const i = args.findIndex((a) => typeof a === "function");
  if (i >= 0) args[i] = wrap(args[i]);
  return origCreateServer.apply(this, args);
};
