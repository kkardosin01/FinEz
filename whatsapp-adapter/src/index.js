/**
 * Adaptador mínimo Baileys <-> Django (seção 6).
 *
 * Decisão consciente: biblioteca não-oficial, contra os termos do WhatsApp,
 * risco de bloqueio do número. Mitigado com número dedicado, volume baixo e
 * plano B (o app funciona 100% via web se o número for bloqueado).
 */
import express from "express";
import pino from "pino";
import qrcode from "qrcode-terminal";
import makeWASocket, { DisconnectReason } from "@whiskeysockets/baileys";
import { Boom } from "@hapi/boom";

import { useEncryptedAuthState } from "./encryptedAuthState.js";
import { forwardMessageToDjango } from "./webhook.js";

const PORT = process.env.PORT || 3333;
const ADAPTER_TOKEN = process.env.WHATSAPP_ADAPTER_TOKEN || "";
const SESSION_PATH = process.env.WHATSAPP_SESSION_PATH || "/data/session.enc";

const logger = pino({ level: process.env.LOG_LEVEL || "info" });

let sock;

async function connect() {
  const { state, saveCreds } = await useEncryptedAuthState(SESSION_PATH);

  sock = makeWASocket({
    auth: state,
    logger: pino({ level: "warn" }),
    printQRInTerminal: false,
  });

  sock.ev.on("creds.update", saveCreds);

  sock.ev.on("connection.update", (update) => {
    const { connection, lastDisconnect, qr } = update;

    if (qr) {
      console.log("Escaneie o QR code com o número dedicado do FinEz:");
      qrcode.generate(qr, { small: true });
    }

    if (connection === "close") {
      const statusCode = new Boom(lastDisconnect?.error)?.output?.statusCode;
      const shouldReconnect = statusCode !== DisconnectReason.loggedOut;
      logger.warn({ statusCode, shouldReconnect }, "conexão encerrada");
      if (shouldReconnect) connect();
    } else if (connection === "open") {
      logger.info("conectado ao WhatsApp");
    }
  });

  sock.ev.on("messages.upsert", async ({ messages, type }) => {
    if (type !== "notify") return;

    for (const msg of messages) {
      if (msg.key.fromMe || !msg.message) continue;

      const phone = msg.key.remoteJid?.split("@")[0];
      const text =
        msg.message.conversation || msg.message.extendedTextMessage?.text || "";

      if (!phone || !text) continue;

      logger.info({ phone }, "mensagem recebida");
      await forwardMessageToDjango({ phone, text, messageId: msg.key.id });
    }
  });
}

function requireAuth(req, res, next) {
  const header = req.headers.authorization || "";
  const token = header.replace("Bearer ", "");
  if (!ADAPTER_TOKEN || token !== ADAPTER_TOKEN) {
    return res.status(401).json({ error: "unauthorized" });
  }
  next();
}

const app = express();
app.use(express.json());

app.get("/health", (_req, res) => {
  res.json({ status: sock?.user ? "connected" : "disconnected" });
});

// Chamado pelo Django (whatsapp.sender) pra enviar confirmações, alertas e resumos.
app.post("/send", requireAuth, async (req, res) => {
  const { phone, body } = req.body || {};
  if (!phone || !body) {
    return res.status(400).json({ error: "phone e body são obrigatórios" });
  }
  if (!sock?.user) {
    return res.status(503).json({ error: "whatsapp não conectado" });
  }

  try {
    await sock.sendMessage(`${phone}@s.whatsapp.net`, { text: body });
    res.status(202).json({ status: "sent" });
  } catch (err) {
    logger.error({ err: err.message }, "falha ao enviar mensagem");
    res.status(500).json({ error: "send_failed" });
  }
});

app.listen(PORT, () => logger.info(`adaptador WhatsApp ouvindo na porta ${PORT}`));

connect().catch((err) => {
  logger.error({ err }, "falha ao conectar ao WhatsApp");
  process.exit(1);
});
