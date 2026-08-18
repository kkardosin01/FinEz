import crypto from "node:crypto";

const DJANGO_WEBHOOK_URL = process.env.DJANGO_WEBHOOK_URL || "http://api:8000/webhooks/whatsapp";
const WEBHOOK_SECRET = process.env.WHATSAPP_WEBHOOK_SECRET || "";

export async function forwardMessageToDjango({ phone, text, messageId }) {
  const body = JSON.stringify({ phone, text, messageId });
  const headers = { "Content-Type": "application/json" };

  if (WEBHOOK_SECRET) {
    headers["X-Finez-Signature"] = crypto
      .createHmac("sha256", WEBHOOK_SECRET)
      .update(body)
      .digest("hex");
  }

  try {
    const response = await fetch(DJANGO_WEBHOOK_URL, { method: "POST", headers, body });
    if (!response.ok) {
      console.error(`Webhook Django respondeu ${response.status}`);
    }
  } catch (err) {
    console.error("Falha ao encaminhar mensagem pro Django:", err.message);
  }
}
