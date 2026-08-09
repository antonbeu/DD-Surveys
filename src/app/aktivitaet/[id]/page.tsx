import Link from "next/link";
import { notFound } from "next/navigation";
import { getActivityForPublic, formatDateTimeRange } from "@/lib/activities";
import { SignupForm } from "./SignupForm";

export const dynamic = "force-dynamic";

export default async function ActivityPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const activity = await getActivityForPublic(id);

  if (!activity) {
    notFound();
  }

  return (
    <div className="min-h-full bg-gradient-to-b from-violet-50 via-white to-white dark:from-violet-950 dark:via-black dark:to-black">
      <div className="mx-auto max-w-xl px-6 py-12">
        <Link
          href="/"
          className="text-sm text-violet-600 hover:underline dark:text-violet-400"
        >
          ← Zurück zur Übersicht
        </Link>

        <div className="mt-4 rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
          <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-50">
            {activity.title}
          </h1>
          <p className="mt-3 whitespace-pre-wrap text-zinc-600 dark:text-zinc-400">
            {activity.description}
          </p>

          <dl className="mt-5 space-y-1 text-sm text-zinc-600 dark:text-zinc-400">
            <div className="flex gap-2">
              <dt className="font-medium text-zinc-900 dark:text-zinc-200">
                📍 Ort:
              </dt>
              <dd>{activity.location}</dd>
            </div>
            <div className="flex gap-2">
              <dt className="font-medium text-zinc-900 dark:text-zinc-200">
                🗓️ Zeit:
              </dt>
              <dd>{formatDateTimeRange(activity.startsAt, activity.endsAt)}</dd>
            </div>
            <div className="flex gap-2">
              <dt className="font-medium text-zinc-900 dark:text-zinc-200">
                👥 Plätze:
              </dt>
              <dd>
                {activity.takenSpots} / {activity.capacity} belegt
                {activity.isFull ? " – ausgebucht" : ""}
              </dd>
            </div>
          </dl>
        </div>

        <div className="mt-6 rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
          <h2 className="mb-4 text-lg font-semibold text-zinc-900 dark:text-zinc-50">
            Anmeldung
          </h2>
          <SignupForm activityId={activity.id} isFull={activity.isFull} />
        </div>
      </div>
    </div>
  );
}
