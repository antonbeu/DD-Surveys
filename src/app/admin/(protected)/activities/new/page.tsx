import Link from "next/link";
import { createActivityAction } from "../../actions";
import { ActivityForm } from "../../ActivityForm";

export default function NewActivityPage() {
  return (
    <div>
      <Link
        href="/admin"
        className="text-sm text-violet-600 hover:underline dark:text-violet-400"
      >
        ← Zurück zur Übersicht
      </Link>
      <h1 className="mt-4 mb-6 text-xl font-semibold text-zinc-900 dark:text-zinc-50">
        Neue Aktivität
      </h1>
      <div className="max-w-xl rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
        <ActivityForm action={createActivityAction} submitLabel="Anlegen" />
      </div>
    </div>
  );
}
