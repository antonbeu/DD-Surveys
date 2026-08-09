"use server";

import { revalidatePath } from "next/cache";
import { Prisma } from "@prisma/client";
import { prisma } from "@/lib/db";
import { sendSignupConfirmation } from "@/lib/mail";

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export type SignupState = {
  status: "idle" | "success" | "error";
  message?: string;
};

export async function signupAction(
  activityId: string,
  _prevState: SignupState,
  formData: FormData
): Promise<SignupState> {
  const name = String(formData.get("name") ?? "").trim();
  const email = String(formData.get("email") ?? "")
    .trim()
    .toLowerCase();

  if (name.length < 2) {
    return { status: "error", message: "Bitte gib deinen Namen an." };
  }
  if (!EMAIL_REGEX.test(email)) {
    return { status: "error", message: "Bitte gib eine gültige E-Mail-Adresse an." };
  }

  const activity = await prisma.activity.findUnique({
    where: { id: activityId },
  });
  if (!activity) {
    return { status: "error", message: "Diese Aktivität wurde nicht gefunden." };
  }

  try {
    const participant = await prisma.$transaction(async (tx) => {
      const takenSpots = await tx.participant.count({
        where: { activityId },
      });
      if (takenSpots >= activity.capacity) {
        throw new Error("FULL");
      }
      return tx.participant.create({
        data: { name, email, activityId },
      });
    });

    await sendSignupConfirmation(participant, activity);
    revalidatePath("/");
    revalidatePath(`/aktivitaet/${activityId}`);

    return {
      status: "success",
      message:
        "Du bist angemeldet! Wir haben dir eine Bestätigung mit allen Infos per E-Mail geschickt.",
    };
  } catch (error) {
    if (error instanceof Error && error.message === "FULL") {
      revalidatePath("/");
      revalidatePath(`/aktivitaet/${activityId}`);
      return {
        status: "error",
        message: "Diese Aktivität ist leider schon ausgebucht.",
      };
    }
    if (
      error instanceof Prisma.PrismaClientKnownRequestError &&
      error.code === "P2002"
    ) {
      return {
        status: "error",
        message: "Diese E-Mail-Adresse ist für diese Aktivität bereits angemeldet.",
      };
    }
    console.error("[signupAction] Fehler bei der Anmeldung", error);
    return {
      status: "error",
      message: "Es ist ein Fehler aufgetreten. Bitte versuche es erneut.",
    };
  }
}
