import Link from "next/link";
import { prisma } from "@/lib/db";
import { formatDateTimeRange } from "@/lib/activities";

export const dynamic = "force-dynamic";

export default async function AdminDashboardPage() {
  const activities = await prisma.activity.findMany({
    orderBy: [{ order: "asc" }, { startsAt: "asc" }],
    include: { _count: { select: { participants: true } } },
  });

  return (
    <div>
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-zinc-900 dark:text-zinc-50">
          Aktivitäten
        </h1>
        <Link
          href="/admin/activities/new"
          className="rounded-lg bg-violet-600 px-4 py-2 text-sm font-medium text-white hover:bg-violet-700"
        >
          + Neue Aktivität
        </Link>
      </div>

      {activities.length === 0 ? (
        <p className="mt-8 rounded-lg border border-dashed border-zinc-300 p-6 text-center text-zinc-500 dark:border-zinc-700">
          Noch keine Aktivitäten angelegt.
        </p>
      ) : (
        <ul className="mt-6 flex flex-col gap-3">
          {activities.map((activity) => (
            <li key={activity.id}>
              <Link
                href={`/admin/activities/${activity.id}`}
                className="block rounded-xl border border-zinc-200 bg-white p-4 shadow-sm transition hover:border-violet-300 dark:border-zinc-800 dark:bg-zinc-900"
              >
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className="font-medium text-zinc-900 dark:text-zinc-50">
                      {activity.title}
                    </p>
                    <p className="text-sm text-zinc-500 dark:text-zinc-400">
                      {formatDateTimeRange(activity.startsAt, activity.endsAt)}{" "}
                      · {activity.location}
                    </p>
                  </div>
                  <span className="shrink-0 rounded-full bg-violet-100 px-3 py-1 text-xs font-medium text-violet-700 dark:bg-violet-900 dark:text-violet-200">
                    {activity._count.participants} / {activity.capacity}
                  </span>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
