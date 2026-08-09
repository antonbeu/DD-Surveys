import Link from "next/link";
import { getActivitiesForPublic, formatDateTimeRange } from "@/lib/activities";

export const dynamic = "force-dynamic";

export default async function Home() {
  const activities = await getActivitiesForPublic();

  return (
    <div className="min-h-full bg-gradient-to-b from-violet-50 via-white to-white dark:from-violet-950 dark:via-black dark:to-black">
      <header className="bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white">
        <div className="mx-auto max-w-3xl px-6 py-16 text-center sm:py-20">
          <p className="text-sm font-semibold uppercase tracking-widest text-violet-100">
            Herzliche Einladung
          </p>
          <h1 className="mt-3 text-4xl font-bold sm:text-5xl">
            Lars wird 60! 🎉
          </h1>
          <p className="mt-5 text-lg text-violet-50">
            Ich freue mich riesig, meinen 60. Geburtstag mit euch zu feiern.
            Damit an allen Tagen alles gut organisiert ist, könnt ihr euch
            unten für die einzelnen Aktivitäten anmelden. Die Plätze sind
            begrenzt – meldet euch also am besten gleich an!
          </p>
        </div>
      </header>

      <main className="mx-auto max-w-3xl px-6 py-12">
        <h2 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-50">
          Aktivitäten
        </h2>
        <p className="mt-2 text-zinc-600 dark:text-zinc-400">
          Sucht euch eine oder mehrere Aktivitäten aus und tragt euch mit
          Namen und E-Mail-Adresse ein. Ihr bekommt danach eine
          Bestätigung mit allen Infos per Mail.
        </p>

        {activities.length === 0 ? (
          <p className="mt-8 rounded-lg border border-dashed border-zinc-300 p-6 text-center text-zinc-500 dark:border-zinc-700">
            Aktuell sind noch keine Aktivitäten eingetragen. Schaut bald
            wieder vorbei!
          </p>
        ) : (
          <ul className="mt-8 flex flex-col gap-4">
            {activities.map((activity) => (
              <li key={activity.id}>
                <Link
                  href={`/aktivitaet/${activity.id}`}
                  className="block rounded-xl border border-zinc-200 bg-white p-5 shadow-sm transition hover:border-violet-300 hover:shadow-md dark:border-zinc-800 dark:bg-zinc-900"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">
                        {activity.title}
                      </h3>
                      <p className="mt-1 line-clamp-2 text-sm text-zinc-600 dark:text-zinc-400">
                        {activity.description}
                      </p>
                      <p className="mt-3 text-sm text-zinc-500 dark:text-zinc-500">
                        📍 {activity.location}
                      </p>
                      <p className="text-sm text-zinc-500 dark:text-zinc-500">
                        🗓️{" "}
                        {formatDateTimeRange(
                          activity.startsAt,
                          activity.endsAt
                        )}
                      </p>
                    </div>
                    <div className="shrink-0 text-right">
                      {activity.isFull ? (
                        <span className="inline-block rounded-full bg-zinc-200 px-3 py-1 text-xs font-medium text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300">
                          Ausgebucht
                        </span>
                      ) : (
                        <span className="inline-block rounded-full bg-violet-100 px-3 py-1 text-xs font-medium text-violet-700 dark:bg-violet-900 dark:text-violet-200">
                          {activity.freeSpots} von {activity.capacity} frei
                        </span>
                      )}
                    </div>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </main>

      <footer className="mx-auto max-w-3xl px-6 pb-10 text-center text-xs text-zinc-400">
        <Link href="/admin" className="hover:text-zinc-500">
          Admin
        </Link>
      </footer>
    </div>
  );
}
