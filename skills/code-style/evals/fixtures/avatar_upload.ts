// POST /me/avatar: a signed-in user uploads a profile picture (multer memory storage).
import type { Request, Response } from "express";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";

const AVATAR_DIR = process.env.AVATAR_DIR ?? "/var/app/avatars";
const MAX_BYTES = 2 * 1024 * 1024;
const EXTENSIONS = new Map([
  ["image/png", ".png"],
  ["image/jpeg", ".jpg"],
  ["image/webp", ".webp"],
]);

type AuthedRequest = Request & { user: { id: string } };

function avatarUrl(userId: string, fileName: string): string {
  return `/avatars/${encodeURIComponent(userId)}/${encodeURIComponent(fileName)}`;
}

async function saveAvatar(userId: string, fileName: string, data: Buffer): Promise<void> {
  const userDir = path.join(AVATAR_DIR, userId);
  await mkdir(userDir, { recursive: true });
  await writeFile(path.join(userDir, fileName), data);
}

export async function uploadAvatar(req: AuthedRequest, res: Response) {
  const file = req.file;
  if (!file) return res.status(400).json({ error: "missing file" });
  if (file.size > MAX_BYTES) return res.status(413).json({ error: "file too large" });
  const ext = EXTENSIONS.get(file.mimetype);
  if (!ext) return res.status(415).json({ error: "unsupported image type" });

  const fileName = `avatar${ext}`;
  await saveAvatar(req.user.id, fileName, file.buffer);
  return res.status(201).json({ url: avatarUrl(req.user.id, fileName) });
}
