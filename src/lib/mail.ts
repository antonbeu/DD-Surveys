import nodemailer from "nodemailer";
import type { Activity, Participant } from "@prisma/client";

const EVENT_NAME =
  process.env.EVENT_NAME ?? "Lars' 60. Geburtstag";

function getTransporter() {
  const host = process.env.SMTP_HOST;
  const port = process.env.SMTP_PORT;
  const user = process.env.SMTP_USER;
  const pass = process.env.SMTP_PASS;

  if (!host || !port || !user || !pass) {
    return null;
  }

  return nodemailer.createTransport({
    host,
    port: Number(port),
    secure: process.env.SMTP_SECURE === "true",
    auth: { user, pass },
  });
}

async function send(options: {
  to: string | string[];
  bcc?: string | string[];
  subject: string;
  text: string;
  html: string;
}) {
  const transporter = getTransporter();
  const from = process.env.MAIL_FROM ?? "no-reply@example.com";

  if (!transporter) {
    console.warn(
      "[mail] SMTP ist nicht konfiguriert – E-Mail wird nur geloggt statt versendet."
    );
    console.warn("[mail]", { ...options, from });
    return;
  }

  await transporter.sendMail({ from, ...options });
}

function formatDateTime(date: Date): string {
  return new Intl.DateTimeFormat("de-DE", {
    weekday: "long",
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

export async function sendSignupConfirmation(
  participant: Participant,
  activity: Activity
) {
  const zeitraum = activity.endsAt
    ? `${formatDateTime(activity.startsAt)} bis ${new Intl.DateTimeFormat(
        "de-DE",
        { hour: "2-digit", minute: "2-digit" }
      ).format(activity.endsAt)} Uhr`
    : `${formatDateTime(activity.startsAt)} Uhr`;

  const subject = `Anmeldebestätigung: ${activity.title} – ${EVENT_NAME}`;

  const text = `Hallo ${participant.name},

du bist erfolgreich für folgende Aktivität bei ${EVENT_NAME} angemeldet:

${activity.title}
${activity.description}

Ort: ${activity.location}
Zeit: ${zeitraum}

Wir freuen uns auf dich!
`;

  const html = `
    <div style="font-family: sans-serif; max-width: 480px; margin: 0 auto;">
      <h2 style="color:#7c3aed;">Anmeldebestätigung</h2>
      <p>Hallo ${escapeHtml(participant.name)},</p>
      <p>du bist erfolgreich für folgende Aktivität bei <strong>${escapeHtml(
        EVENT_NAME
      )}</strong> angemeldet:</p>
      <div style="background:#f5f3ff; border-radius:8px; padding:16px; margin:16px 0;">
        <h3 style="margin:0 0 8px 0;">${escapeHtml(activity.title)}</h3>
        <p style="margin:0 0 12px 0;">${escapeHtml(activity.description)}</p>
        <p style="margin:0;"><strong>Ort:</strong> ${escapeHtml(
          activity.location
        )}</p>
        <p style="margin:0;"><strong>Zeit:</strong> ${escapeHtml(zeitraum)}</p>
      </div>
      <p>Wir freuen uns auf dich!</p>
    </div>
  `;

  await send({ to: participant.email, subject, text, html });
}

export async function sendBroadcast(
  activity: Activity,
  participantEmails: string[],
  subject: string,
  body: string
) {
  if (participantEmails.length === 0) return;

  const fullSubject = `${subject} – ${activity.title}`;
  const html = `<div style="font-family: sans-serif; max-width: 480px; margin: 0 auto; white-space: pre-wrap;">${escapeHtml(
    body
  )}</div>`;

  await send({
    to: process.env.MAIL_FROM ?? "no-reply@example.com",
    bcc: participantEmails,
    subject: fullSubject,
    text: body,
    html,
  });
}

function escapeHtml(input: string): string {
  return input
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;")
    .replace(/\n/g, "<br/>");
}
