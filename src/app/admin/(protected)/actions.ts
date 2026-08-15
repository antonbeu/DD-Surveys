"use server";

import { redirect } from "next/navigation";
import { revalidatePath } from "next/cache";
import { prisma } from "@/lib/db";
import { isAdminAuthenticated, clearAdminSessionCookie } from "@/lib/auth";
import { sendBroadcast } from "@/lib/mail";

async function requireAdmin() {
  if (!(await isAdminAuthenticated())) {
    redirect("/admin/login");
  }
}

export async function logoutAction() {
  await clearAdminSessionCookie();
  redirect("/admin/login");
}

export type ActivityFormState = {
  status: "idle" | "error";
  message?: string;
};

function parseActivityForm(formData: FormData) {
  const title = String(formData.get("title") ?? "").trim();
  const description = String(formData.get("description") ?? "").trim();
  const location = String(formData.get("location") ?? "").trim();
  const dateTbd = formData.get("dateTbd") === "on";
  const startsAtRaw = String(formData.get("startsAt") ?? "");
  const endsAtRaw = String(formData.get("endsAt") ?? "");
  const capacityRaw = String(formData.get("capacity") ?? "");
  const orderRaw = String(formData.get("order") ?? "0");

  if (!title || !description || !location) {
    throw new Error("Bitte fülle alle Pflichtfelder aus.");
  }
  if (!dateTbd && !startsAtRaw) {
    throw new Error(
      "Bitte einen Beginn angeben oder \"Termin steht noch nicht fest\" auswählen."
    );
  }

  let startsAt: Date | null = null;
  let endsAt: Date | null = null;

  if (!dateTbd) {
    startsAt = new Date(startsAtRaw);
    if (Number.isNaN(startsAt.getTime())) {
      throw new Error("Ungültiges Startdatum.");
    }

    if (endsAtRaw) {
      endsAt = new Date(endsAtRaw);
      if (Number.isNaN(endsAt.getTime())) {
        throw new Error("Ungültiges Enddatum.");
      }
    }
  }

  const capacity = Number(capacityRaw);
  if (!Number.isInteger(capacity) || capacity < 1) {
    throw new Error("Die Teilnehmendenanzahl muss eine positive Zahl sein.");
  }

  const order = Number.isInteger(Number(orderRaw)) ? Number(orderRaw) : 0;

  return {
    title,
    description,
    location,
    dateTbd,
    startsAt,
    endsAt,
    capacity,
    order,
  };
}

export async function createActivityAction(
  _prevState: ActivityFormState,
  formData: FormData
): Promise<ActivityFormState> {
  await requireAdmin();

  let data;
  try {
    data = parseActivityForm(formData);
  } catch (error) {
    return {
      status: "error",
      message: error instanceof Error ? error.message : "Ungültige Eingabe.",
    };
  }

  const activity = await prisma.activity.create({ data });

  revalidatePath("/");
  revalidatePath("/admin");
  redirect(`/admin/activities/${activity.id}`);
}

export async function updateActivityAction(
  activityId: string,
  _prevState: ActivityFormState,
  formData: FormData
): Promise<ActivityFormState> {
  await requireAdmin();

  let data;
  try {
    data = parseActivityForm(formData);
  } catch (error) {
    return {
      status: "error",
      message: error instanceof Error ? error.message : "Ungültige Eingabe.",
    };
  }

  await prisma.activity.update({ where: { id: activityId }, data });

  revalidatePath("/");
  revalidatePath(`/aktivitaet/${activityId}`);
  revalidatePath("/admin");
  revalidatePath(`/admin/activities/${activityId}`);

  return { status: "idle", message: "Änderungen gespeichert." };
}

export async function deleteActivityAction(activityId: string) {
  await requireAdmin();

  await prisma.activity.delete({ where: { id: activityId } });

  revalidatePath("/");
  revalidatePath("/admin");
  redirect("/admin");
}

export async function deleteParticipantAction(
  activityId: string,
  participantId: string
) {
  await requireAdmin();

  await prisma.participant.delete({ where: { id: participantId } });

  revalidatePath("/");
  revalidatePath(`/aktivitaet/${activityId}`);
  revalidatePath("/admin");
  revalidatePath(`/admin/activities/${activityId}`);
}

export type SettingsFormState = {
  status: "idle" | "error";
  message?: string;
};

export async function updateSiteSettingsAction(
  _prevState: SettingsFormState,
  formData: FormData
): Promise<SettingsFormState> {
  await requireAdmin();

  const heroEyebrow = String(formData.get("heroEyebrow") ?? "").trim();
  const heroTitle = String(formData.get("heroTitle") ?? "").trim();
  const heroText = String(formData.get("heroText") ?? "").trim();

  if (!heroEyebrow || !heroTitle || !heroText) {
    return { status: "error", message: "Bitte fülle alle Felder aus." };
  }

  await prisma.siteSettings.upsert({
    where: { id: "main" },
    update: { heroEyebrow, heroTitle, heroText },
    create: { id: "main", heroEyebrow, heroTitle, heroText },
  });

  revalidatePath("/");
  revalidatePath("/admin/einstellungen");

  return { status: "idle", message: "Änderungen gespeichert." };
}

export type BroadcastState = {
  status: "idle" | "success" | "error";
  message?: string;
};

export async function sendBroadcastAction(
  activityId: string,
  _prevState: BroadcastState,
  formData: FormData
): Promise<BroadcastState> {
  await requireAdmin();

  const subject = String(formData.get("subject") ?? "").trim();
  const body = String(formData.get("body") ?? "").trim();

  if (!subject || !body) {
    return {
      status: "error",
      message: "Bitte Betreff und Nachricht ausfüllen.",
    };
  }

  const activity = await prisma.activity.findUnique({
    where: { id: activityId },
  });
  if (!activity) {
    return { status: "error", message: "Aktivität nicht gefunden." };
  }

  const participants = await prisma.participant.findMany({
    where: { activityId },
    select: { email: true },
  });

  if (participants.length === 0) {
    return {
      status: "error",
      message: "Für diese Aktivität gibt es noch keine Teilnehmenden.",
    };
  }

  try {
    await sendBroadcast(
      activity,
      participants.map((p) => p.email),
      subject,
      body
    );
  } catch (error) {
    console.error("[sendBroadcastAction]", error);
    return {
      status: "error",
      message: "E-Mail konnte nicht versendet werden.",
    };
  }

  return {
    status: "success",
    message: `E-Mail an ${participants.length} Teilnehmende gesendet.`,
  };
}
