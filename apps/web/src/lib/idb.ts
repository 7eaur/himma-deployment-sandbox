import { openDB, DBSchema } from 'idb';

interface HimmaDB extends DBSchema {
  audio_outbox: {
    key: string;
    value: {
      idempotency_key: string;
      recording_id: string; // the server generated UUID
      blob: Blob;
      timestamp: number;
    };
  };
}

const DB_NAME = 'himma-db';
const STORE_NAME = 'audio_outbox';

async function initDB() {
  return openDB<HimmaDB>(DB_NAME, 1, {
    upgrade(db) {
      db.createObjectStore(STORE_NAME, { keyPath: 'idempotency_key' });
    },
  });
}

export async function saveAudioToOutbox(idempotency_key: string, recording_id: string, blob: Blob) {
  const db = await initDB();
  await db.put(STORE_NAME, {
    idempotency_key,
    recording_id,
    blob,
    timestamp: Date.now(),
  });
}

export async function getAudioFromOutbox(idempotency_key: string) {
  const db = await initDB();
  return db.get(STORE_NAME, idempotency_key);
}

export async function removeAudioFromOutbox(idempotency_key: string) {
  const db = await initDB();
  await db.delete(STORE_NAME, idempotency_key);
}

export async function clearOutbox() {
  const db = await initDB();
  await db.clear(STORE_NAME);
}
