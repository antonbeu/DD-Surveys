"use server";

import { redirect } from "next/navigation";
import { checkAdminPassword, setAdminSessionCookie } from "@/lib/auth";

export type LoginState = {
  status: "idle" | "error";
  message?: string;
};

export async function loginAction(
  _prevState: LoginState,
  formData: FormData
): Promise<LoginState> {
  const password = String(formData.get("password") ?? "");

  let valid: boolean;
  try {
    valid = checkAdminPassword(password);
  } catch (error) {
    console.error("[loginAction]", error);
    return {
      status: "error",
      message: "Admin-Zugang ist serverseitig nicht konfiguriert.",
    };
  }

  if (!valid) {
    return { status: "error", message: "Falsches Passwort." };
  }

  await setAdminSessionCookie();
  redirect("/admin");
}
