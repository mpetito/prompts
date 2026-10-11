// Consent review for creator profiles: a creator submits consent documents, a moderator
// approves or rejects them, and every step is appended to the profile's event log.
import { randomUUID } from "node:crypto";

export type ConsentStatus = "none" | "pending" | "approved" | "rejected";

export type Profile = {
  id: string;
  displayName: string;
  email: string;
  consentStatus: ConsentStatus;
  updatedAt: string;
};

export type ProfileEventType = "consent_submitted" | "consent_approved" | "consent_rejected";

export type ProfileEvent = {
  id: string;
  profileId: string;
  type: ProfileEventType;
  at: string;
  actorId: string;
  reason?: string;
};

export interface ProfileStore {
  getProfile(id: string): Promise<Profile>;
  updateProfile(id: string, patch: Partial<Omit<Profile, "id">>): Promise<Profile>;
  appendEvent(event: ProfileEvent): Promise<void>;
  listEvents(profileId: string, type?: ProfileEventType): Promise<ProfileEvent[]>;
}

export class ConsentStateError extends Error {
  constructor(profileId: string, expected: ConsentStatus, actual: ConsentStatus) {
    super(`profile ${profileId}: expected consent ${expected}, found ${actual}`);
    this.name = "ConsentStateError";
  }
}

async function record(
  store: ProfileStore,
  profileId: string,
  type: ProfileEventType,
  actorId: string,
  reason?: string,
): Promise<string> {
  const at = new Date().toISOString();
  await store.appendEvent({ id: randomUUID(), profileId, type, at, actorId, reason });
  return at;
}

async function requireStatus(store: ProfileStore, profileId: string, expected: ConsentStatus) {
  const profile = await store.getProfile(profileId);
  if (profile.consentStatus !== expected) {
    throw new ConsentStateError(profileId, expected, profile.consentStatus);
  }
  return profile;
}

export async function submitConsent(store: ProfileStore, profileId: string): Promise<Profile> {
  const profile = await store.getProfile(profileId);
  if (profile.consentStatus === "pending" || profile.consentStatus === "approved") {
    throw new ConsentStateError(profileId, "none", profile.consentStatus);
  }
  const at = await record(store, profileId, "consent_submitted", profileId);
  return store.updateProfile(profileId, { consentStatus: "pending", updatedAt: at });
}

export async function approveConsent(
  store: ProfileStore,
  profileId: string,
  moderatorId: string,
): Promise<Profile> {
  await requireStatus(store, profileId, "pending");
  const at = await record(store, profileId, "consent_approved", moderatorId);
  return store.updateProfile(profileId, { consentStatus: "approved", updatedAt: at });
}

export async function rejectConsent(
  store: ProfileStore,
  profileId: string,
  moderatorId: string,
  reason: string,
): Promise<Profile> {
  await requireStatus(store, profileId, "pending");
  const at = await record(store, profileId, "consent_rejected", moderatorId, reason);
  return store.updateProfile(profileId, { consentStatus: "rejected", updatedAt: at });
}
