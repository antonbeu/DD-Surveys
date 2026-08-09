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
- [Prisma](https://www.prisma.io) + PostgreSQL als Datenbank
- [Nodemailer](https://nodemailer.com) für den E-Mail-Versand
- Tailwind CSS fürs Styling

## Lokal starten

1. Abhängigkeiten installieren:

   ```bash
   npm install
   ```

2. Eine PostgreSQL-Datenbank bereitstellen (lokal z. B. per Docker):

   ```bash
   docker run --name lars-db -e POSTGRES_USER=larsapp -e POSTGRES_PASSWORD=larsapp \
     -e POSTGRES_DB=larsapp -p 5432:5432 -d postgres:16
   ```

3. `.env` anpassen (Datei existiert bereits mit sinnvollen Defaults):

   ```bash
   DATABASE_URL="postgresql://larsapp:larsapp@localhost:5432/larsapp"

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

4. Datenbank-Tabellen anlegen und mit Beispiel-Aktivitäten befüllen:

   ```bash
   npm run db:migrate
   npm run db:seed
   ```

5. Entwicklungsserver starten:

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

## Deployment (ohne Terminal, über Railway)

Diese App braucht eine PostgreSQL-Datenbank und einen Node-Server, der
dauerhaft läuft – kein reines Serverless-Hosting. Am einfachsten geht das
komplett über den Browser mit [Railway](https://railway.app):

1. Auf [railway.app](https://railway.app) gehen und mit **"Login with
   GitHub"** anmelden (kostenloser Account reicht zum Start).
2. **"New Project"** → **"Deploy from GitHub repo"** → das Repository
   `antonbeu/dd` auswählen. Falls Railway noch keinen Zugriff auf das Repo
   hat, wird das im selben Schritt eingerichtet.
3. Als Branch `claude/lars-birthday-event-signup-zalmw4` auswählen (oder
   den Branch, auf den die Änderungen zuletzt gepusht wurden).
4. Im selben Projekt über **"+ New"** → **"Database"** → **"Add
   PostgreSQL"** eine Datenbank hinzufügen. Railway verbindet sie
   automatisch mit der App und stellt die Variable `DATABASE_URL` bereit.
5. Bei der App (nicht der Datenbank) unter **"Variables"** folgende
   Umgebungsvariablen eintragen:

   | Variable | Wert |
   | --- | --- |
   | `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` (Railway schlägt das automatisch vor) |
   | `ADMIN_PASSWORD` | ein selbst gewähltes, geheimes Passwort für `/admin` |
   | `ADMIN_SESSION_SECRET` | eine lange zufällige Zeichenkette (z. B. über einen Passwort-Generator erzeugen) |
   | `MAIL_FROM` | z. B. `Lars Geburtstag <deine-adresse@beispiel.de>` |
   | `EVENT_NAME` | `Lars' 60. Geburtstag` |
   | `SMTP_HOST`, `SMTP_PORT`, `SMTP_SECURE`, `SMTP_USER`, `SMTP_PASS` | Zugangsdaten deines Mail-Anbieters (siehe oben) – ohne diese werden Mails nur geloggt, nicht wirklich verschickt |

6. Railway baut die App automatisch (dabei werden auch die
   Datenbank-Tabellen automatisch angelegt) und zeigt danach unter
   **"Settings" → "Networking" → "Generate Domain"** eine öffentliche
   URL wie `https://dein-projekt.up.railway.app` an – das ist der Link,
   den du an deine Gäste schickst.
7. Die Datenbank startet leer (die Beispiel-Aktivitäten aus der lokalen
   Entwicklung werden nicht automatisch übernommen). Im Admin-Bereich
   (`https://.../admin`, Login mit `ADMIN_PASSWORD`) einfach die echten
   Aktivitäten anlegen.

Setze unbedingt eigene, geheime Werte für `ADMIN_PASSWORD` und
`ADMIN_SESSION_SECRET` – nicht die Platzhalter aus `.env.example`
verwenden.

## Datenbank-Kommandos

```bash
npm run db:migrate   # Migrationen anwenden / neue Migration erstellen
npm run db:seed      # Beispiel-Aktivitäten anlegen (nur wenn DB leer ist)
npm run db:studio    # Prisma Studio – Datenbank im Browser ansehen/bearbeiten
```
