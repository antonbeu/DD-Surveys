import { getSiteSettings } from "@/lib/activities";
import { SettingsForm } from "./SettingsForm";

export const dynamic = "force-dynamic";

export default async function AdminSettingsPage() {
  const settings = await getSiteSettings();

  return (
    <div>
      <h1 className="mb-2 text-xl font-semibold text-zinc-900 dark:text-zinc-50">
        Startseite bearbeiten
      </h1>
      <p className="mb-6 text-sm text-zinc-600 dark:text-zinc-400">
        Dieser Text erscheint ganz oben auf der öffentlichen Startseite,
        bevor die Aktivitäten aufgelistet werden.
      </p>
      <div className="max-w-xl rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
        <SettingsForm
          initial={{
            heroEyebrow: settings.heroEyebrow,
            heroTitle: settings.heroTitle,
            heroText: settings.heroText,
          }}
        />
      </div>
    </div>
  );
}
