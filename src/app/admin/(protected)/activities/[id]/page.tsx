import Link from "next/link";
import { notFound } from "next/navigation";
import { prisma } from "@/lib/db";
import { formatDate, formatTime } from "@/lib/activities";
import { updateActivityAction } from "../../actions";
import { ActivityForm } from "../../ActivityForm";
import { DeleteActivityButton } from "./DeleteActivityButton";
import { CopyEmailsButton } from "./CopyEmailsButton";
import { BroadcastForm } from "./BroadcastForm";

export const dynamic = "force-dynamic";

export default async function AdminActivityPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  const activity = await prisma.activity.findUnique({
    where: { id },
    include: { participants: { orderBy: { createdAt: "asc" } } },
  });

  if (!activity) {
    notFound();
  }

  const boundUpdateAction = updateActivityAction.bind(null, activity.id);
  const emails = activity.participants.map((p) => p.email);

  return (
    <div>
      <Link
        href="/admin"
        className="text-sm text-violet-600 hover:underline dark:text-violet-400"
      >
        ← Zurück zur Übersicht
      </Link>
      <h1 className="mt-4 mb-6 text-xl font-semibold text-zinc-900 dark:text-zinc-50">
        {activity.title}
      </h1>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <section className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
          <h2 className="mb-4 font-semibold text-zinc-900 dark:text-zinc-50">
            Details bearbeiten
          </h2>
          <ActivityForm
            action={boundUpdateAction}
            submitLabel="Speichern"
            initial={{
              title: activity.title,
              description: activity.description,
              location: activity.location,
              startsAt: activity.startsAt,
              endsAt: activity.endsAt,
              capacity: activity.capacity,
              order: activity.order,
            }}
          />
          <div className="mt-6 border-t border-zinc-200 pt-4 dark:border-zinc-800">
            <DeleteActivityButton activityId={activity.id} />
          </div>
        </section>

        <section className="flex flex-col gap-6">
          <div className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="font-semibold text-zinc-900 dark:text-zinc-50">
                Teilnehmende ({activity.participants.length} /{" "}
                {activity.capacity})
              </h2>
              <div className="flex items-center gap-2">
                <CopyEmailsButton emails={emails} />
                <a
                  href={`/admin/activities/${activity.id}/export`}
                  className="rounded-lg border border-zinc-300 px-3 py-1.5 text-sm font-medium text-zinc-700 hover:bg-zinc-50 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
                >
                  CSV
                </a>
              </div>
            </div>

            {activity.participants.length === 0 ? (
              <p className="text-sm text-zinc-500 dark:text-zinc-400">
                Noch keine Anmeldungen.
              </p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-zinc-200 text-zinc-500 dark:border-zinc-800 dark:text-zinc-400">
                      <th className="py-2 pr-4 font-medium">Name</th>
                      <th className="py-2 pr-4 font-medium">E-Mail</th>
                      <th className="py-2 font-medium">Angemeldet</th>
                    </tr>
                  </thead>
                  <tbody>
                    {activity.participants.map((participant) => (
                      <tr
                        key={participant.id}
                        className="border-b border-zinc-100 last:border-0 dark:border-zinc-800/60"
                      >
                        <td className="py-2 pr-4 text-zinc-900 dark:text-zinc-100">
                          {participant.name}
                        </td>
                        <td className="py-2 pr-4 text-zinc-600 dark:text-zinc-400">
                          {participant.email}
                        </td>
                        <td className="py-2 text-zinc-500 dark:text-zinc-500">
                          {formatDate(participant.createdAt)}{" "}
                          {formatTime(participant.createdAt)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          <div className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
            <h2 className="mb-3 font-semibold text-zinc-900 dark:text-zinc-50">
              E-Mail an diese Gruppe senden
            </h2>
            <BroadcastForm activityId={activity.id} />
          </div>
        </section>
      </div>
    </div>
  );
}
