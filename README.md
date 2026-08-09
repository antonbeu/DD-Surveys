# Lars' 60. Geburtstag – Anmeldeseite

Eine kleine Webseite, auf der sich Gäste für einzelne Aktivitäten rund um
Lars' 60. Geburtstag anmelden können. Jede Aktivität hat einen Ort, eine
Zeit, eine Beschreibung und eine begrenzte Teilnehmendenzahl. Nach der
Anmeldung (Name + E-Mail) bekommen Gäste eine Bestätigung per Mail. Als
Admin kannst du Aktivitäten anlegen/bearbeiten, alle Teilnehmendenlisten
inkl. E-Mail-Adressen einsehen, als CSV exportieren und direkt eine E-Mail
an alle Teilnehmenden einer Aktivität schicken (wie ein Verteiler).

## Tech-Stack

- [Next.js](https://nextjs.org) (App Router, Server Actions)
- [Prisma](https://www.prisma.io) + SQLite als Datenbank
- [Nodemailer](https://nodemailer.com) für den E-Mail-Versand
- Tailwind CSS fürs Styling

## Lokal starten

1. Abhängigkeiten installieren:

   ```bash
   npm install
   ```

2. `.env` anpassen (Datei existiert bereits mit sinnvollen Defaults):

   ```bash
   ADMIN_PASSWORD="dein-admin-passwort"
   ADMIN_SESSION_SECRET="ein-langer-zufälliger-string"
   MAIL_FROM="Lars Geburtstag <no-reply@example.com>"
   EVENT_NAME="Lars' 60. Geburtstag"

   # SMTP-Zugangsdaten für den echten Mailversand (siehe unten)
   SMTP_HOST=""
   SMTP_PORT="587"
   SMTP_SECURE="false"
   SMTP_USER=""
   SMTP_PASS=""
   ```

   Solange `SMTP_HOST` leer ist, werden E-Mails nicht wirklich verschickt,
   sondern nur in die Server-Konsole geloggt – praktisch zum Testen.

3. Datenbank anlegen und mit Beispiel-Aktivitäten befüllen:

   ```bash
   npm run db:migrate
   npm run db:seed
   ```

4. Entwicklungsserver starten:

   ```bash
   npm run dev
   ```

   Öffne [http://localhost:3000](http://localhost:3000) für die
   öffentliche Seite und [http://localhost:3000/admin](http://localhost:3000/admin)
   für den Admin-Bereich (Login mit `ADMIN_PASSWORD`).

## Aktivitäten verwalten (Admin)

Unter `/admin` kannst du:

- neue Aktivitäten anlegen (Titel, Beschreibung, Ort, Beginn/Ende,
  maximale Teilnehmendenzahl, Reihenfolge auf der Startseite),
- bestehende Aktivitäten bearbeiten oder löschen,
- pro Aktivität die Liste aller Teilnehmenden mit Name, E-Mail und
  Anmeldezeitpunkt einsehen,
- alle E-Mail-Adressen einer Aktivität mit einem Klick kopieren oder als
  CSV herunterladen,
- eine E-Mail (Betreff + Text) direkt an alle Teilnehmenden einer
  Aktivität senden.

## E-Mail-Versand einrichten (SMTP)

Für echten Mailversand brauchst du Zugangsdaten zu einem SMTP-Server, z. B.
von deinem E-Mail-Anbieter oder einem Dienst wie
[Resend](https://resend.com), [Brevo](https://www.brevo.com) oder
[Mailgun](https://www.mailgun.com). Trage die Zugangsdaten in `.env` ein:

```bash
SMTP_HOST="smtp.beispiel.de"
SMTP_PORT="587"
SMTP_SECURE="false"
SMTP_USER="dein-benutzername"
SMTP_PASS="dein-passwort"
MAIL_FROM="Lars Geburtstag <deine-adresse@beispiel.de>"
```

## Deployment

Diese App braucht neben dem Next.js-Server eine **dauerhaft beschreibbare**
SQLite-Datei. Das funktioniert nicht auf rein serverlosen Plattformen mit
read-only Dateisystem (z. B. Vercel im Standardbetrieb). Für den echten
Einsatz eignet sich z. B.:

- ein kleiner VPS oder Server mit `npm run build && npm run start`,
- eine Plattform mit persistentem Volume (z. B. Railway, Render, Fly.io),
- oder eine Umstellung von SQLite auf eine gehostete Postgres-Datenbank
  (z. B. Neon oder Supabase) – dafür müsste `DATABASE_URL` und der
  `provider` in `prisma/schema.prisma` angepasst werden.

Setze in der Produktionsumgebung unbedingt eigene, geheime Werte für
`ADMIN_PASSWORD` und `ADMIN_SESSION_SECRET`.

## Datenbank-Kommandos

```bash
npm run db:migrate   # Migrationen anwenden / neue Migration erstellen
npm run db:seed      # Beispiel-Aktivitäten anlegen (nur wenn DB leer ist)
npm run db:studio    # Prisma Studio – Datenbank im Browser ansehen/bearbeiten
```
