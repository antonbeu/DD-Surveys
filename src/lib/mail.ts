import type { Activity, Participant } from "@prisma/client";

const EVENT_NAME =
  process.env.EVENT_NAME ?? "Lars' 60. Geburtstag";

/**
 * Holt nur die E-Mail-Adresse aus MAIL_FROM.
 * Funktioniert sowohl mit:
 * lars.beulke@me.com
 * als auch mit:
 * Lars Geburtstag <lars.beulke@me.com>
 */
function extractEmail(value: string): string {
  const match = value.match(/<([^>]+)>/);
  return match ? match[1].trim() : value.trim();
}

/**
 * Holt den Anzeigenamen aus MAIL_FROM.
 */
function extractName(value: string): string {
  const match = value.match(/^(.+?)\s*</);
  return match ? match[1].trim().replace(/^["']|["']$/g, "") : "Lars Geburtstag";
}

/**
 * Verschickt eine E-Mail über die Mailjet API.
 *
 * Gibt true zurück, wenn Mailjet die E-Mail angenommen hat.
 * Gibt false zurück, wenn etwas schiefgeht.
 */
async function send(options: {
  to: string | string[];
  bcc?: string | string[];
  subject: string;
  text: string;
  html: string;
}): Promise<boolean> {
  const apiKey = process.env.MAILJET_API_KEY;
  const secretKey = process.env.MAILJET_SECRET_KEY;

  const mailFrom =
    process.env.MAIL_FROM ?? "lars.beulke@me.com";

  if (!apiKey || !secretKey) {
    console.error(
      "[mail] MAILJET_API_KEY oder MAILJET_SECRET_KEY fehlt."
    );
    return false;
  }

  const recipients = Array.isArray(options.to)
    ? options.to
    : [options.to];

  const bccRecipients = options.bcc
    ? Array.isArray(options.bcc)
      ? options.bcc
      : [options.bcc]
    : [];

  const message: {
    From: {
      Email: string;
      Name: string;
    };
    To: { Email: string }[];
    Bcc?: { Email: string }[];
    Subject: string;
    TextPart: string;
    HTMLPart: string;
  } = {
    From: {
      Email: extractEmail(mailFrom),
      Name: extractName(mailFrom),
    },
    To: recipients.map((email) => ({
      Email: extractEmail(email),
    })),
    Subject: options.subject,
    TextPart: options.text,
    HTMLPart: options.html,
  };

  if (bccRecipients.length > 0) {
    message.Bcc = bccRecipients.map((email) => ({
      Email: extractEmail(email),
    }));
  }

  try {
    const auth = Buffer.from(
      `${apiKey}:${secretKey}`
    ).toString("base64");

    const response = await fetch(
      "https://api.mailjet.com/v3.1/send",
      {
        method: "POST",
        headers: {
          Authorization: `Basic ${auth}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          Messages: [message],
        }),
        signal: AbortSignal.timeout(10000),
      }
    );

    if (!response.ok) {
      const errorText = await response.text();

      console.error(
        "[mail] Mailjet Fehler:",
        response.status,
        errorText
      );

      return false;
    }

    console.log("[mail] E-Mail erfolgreich über Mailjet versendet.");

    return true;
  } catch (error) {
    console.error(
      "[mail] Mailjet konnte nicht erreicht werden:",
      error
    );

    return false;
  }
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
        <h3 style="margin:0 0 8px 0;">
          ${escapeHtml(activity.title)}
        </h3>

        <p style="margin:0 0 12px 0;">
          ${escapeHtml(activity.description)}
        </p>

        <p style="margin:0;">
          <strong>Ort:</strong>
          ${escapeHtml(activity.location)}
        </p>

        <p style="margin:0;">
          <strong>Zeit:</strong>
          ${escapeHtml(zeitraum)}
        </p>
      </div>

      <p>Wir freuen uns auf dich!</p>
    </div>
  `;

  /*
   * Wichtig:
   * Auch wenn die E-Mail einmal nicht funktioniert,
   * bleibt die Anmeldung trotzdem erfolgreich.
   */
  const emailSent = await send({
    to: participant.email,
    subject,
    text,
    html,
  });

  if (!emailSent) {
    console.error(
      `[mail] Bestätigung für ${participant.email} konnte nicht versendet werden.`
    );
  }
}

export async function sendBroadcast(
  activity: Activity,
  participantEmails: string[],
  subject: string,
  body: string
) {
  if (participantEmails.length === 0) return;

  const fullSubject = `${subject} – ${activity.title}`;

  const html = `
    <div style="font-family: sans-serif; max-width: 480px; margin: 0 auto; white-space: pre-wrap;">
      ${escapeHtml(body)}
    </div>
  `;

  for (const email of participantEmails) {
    const emailSent = await send({
      to: email,
      subject: fullSubject,
      text: body,
      html,
    });

    if (!emailSent) {
      throw new Error(
        `Die E-Mail an ${email} konnte nicht über Mailjet versendet werden.`
      );
    }
  }
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
