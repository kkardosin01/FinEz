/**
 * Auth state do Baileys persistido criptografado (AES-256-GCM) em um único
 * arquivo — evita re-parear a cada deploy sem guardar a sessão em texto
 * plano no disco (seção 6: "sessão persistida criptografada").
 *
 * Chave vem de WHATSAPP_SESSION_KEY (32 bytes em hex/base64), nunca no código.
 */
import fs from "node:fs";
import crypto from "node:crypto";
import { initAuthCreds, BufferJSON, proto } from "@whiskeysockets/baileys";

const ALGO = "aes-256-gcm";

function getKey() {
  const raw = process.env.WHATSAPP_SESSION_KEY;
  if (!raw || raw.length < 32) {
    throw new Error(
      "WHATSAPP_SESSION_KEY ausente ou curta demais — gere 32 bytes aleatórios (ex.: openssl rand -hex 32)"
    );
  }
  return crypto.createHash("sha256").update(raw).digest();
}

function encrypt(json) {
  const key = getKey();
  const iv = crypto.randomBytes(12);
  const cipher = crypto.createCipheriv(ALGO, key, iv);
  const ciphertext = Buffer.concat([cipher.update(json, "utf8"), cipher.final()]);
  const authTag = cipher.getAuthTag();
  return Buffer.concat([iv, authTag, ciphertext]).toString("base64");
}

function decrypt(payload) {
  const key = getKey();
  const raw = Buffer.from(payload, "base64");
  const iv = raw.subarray(0, 12);
  const authTag = raw.subarray(12, 28);
  const ciphertext = raw.subarray(28);
  const decipher = crypto.createDecipheriv(ALGO, key, iv);
  decipher.setAuthTag(authTag);
  return Buffer.concat([decipher.update(ciphertext), decipher.final()]).toString("utf8");
}

export async function useEncryptedAuthState(filePath) {
  let data = { creds: initAuthCreds(), keys: {} };

  if (fs.existsSync(filePath)) {
    try {
      const decrypted = decrypt(fs.readFileSync(filePath, "utf8"));
      data = JSON.parse(decrypted, BufferJSON.reviver);
    } catch (err) {
      console.error("Falha ao decifrar a sessão salva — iniciando pareamento do zero.", err.message);
    }
  }

  const write = () => {
    const json = JSON.stringify(data, BufferJSON.replacer);
    fs.writeFileSync(filePath, encrypt(json), "utf8");
  };

  return {
    state: {
      creds: data.creds,
      keys: {
        get: async (type, ids) => {
          const result = {};
          for (const id of ids) {
            let value = data.keys[type]?.[id];
            if (value && type === "app-state-sync-key") {
              value = proto.Message.AppStateSyncKeyData.fromObject(value);
            }
            if (value) result[id] = value;
          }
          return result;
        },
        set: async (updates) => {
          for (const type of Object.keys(updates)) {
            data.keys[type] = data.keys[type] || {};
            Object.assign(data.keys[type], updates[type]);
          }
          write();
        },
      },
    },
    saveCreds: async () => write(),
  };
}
