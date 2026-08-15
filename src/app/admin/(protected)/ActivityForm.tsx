"use client";

import { useActionState, useState } from "react";
import type { ActivityFormState } from "./actions";

function toDatetimeLocalValue(date: Date | null): string {
  if (!date) return "";
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(
    date.getDate()
  )}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

type Initial = {
  title: string;
  description: string;
  location: string;
  startsAt: Date | null;
  endsAt: Date | null;
  dateTbd: boolean;
  capacity: number;
  order: number;
};

const emptyInitial: Initial = {
  title: "",
  description: "",
  location: "",
  startsAt: new Date(),
  endsAt: null,
  dateTbd: false,
  capacity: 10,
  order: 0,
};

const initialState: ActivityFormState = { status: "idle" };

export function ActivityForm({
  action,
  initial,
  submitLabel,
}: {
  action: (
    prevState: ActivityFormState,
    formData: FormData
  ) => Promise<ActivityFormState>;
  initial?: Initial;
  submitLabel: string;
}) {
  const values = initial ?? emptyInitial;
  const [state, formAction, pending] = useActionState(action, initialState);
  const [dateTbd, setDateTbd] = useState(values.dateTbd);

  return (
    <form action={formAction} className="flex flex-col gap-4">
      <div>
        <label className="mb-1 block text-sm font-medium text-zinc-700 dark:text-zinc-300">
          Titel
        </label>
        <input
          name="title"
          type="text"
          required
          defaultValue={values.title}
          className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-zinc-900 focus:border-violet-500 focus:outline-none focus:ring-1 focus:ring-violet-500 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50"
        />
      </div>

      <div>
        <label className="mb-1 block text-sm font-medium text-zinc-700 dark:text-zinc-300">
          Beschreibung
        </label>
        <textarea
          name="description"
          required
          rows={4}
          defaultValue={values.description}
          className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-zinc-900 focus:border-violet-500 focus:outline-none focus:ring-1 focus:ring-violet-500 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50"
        />
      </div>

      <div>
        <label className="mb-1 block text-sm font-medium text-zinc-700 dark:text-zinc-300">
          Ort
        </label>
        <input
          name="location"
          type="text"
          required
          defaultValue={values.location}
          className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-zinc-900 focus:border-violet-500 focus:outline-none focus:ring-1 focus:ring-violet-500 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50"
        />
      </div>

      <label className="flex items-center gap-2 text-sm text-zinc-700 dark:text-zinc-300">
        <input
          name="dateTbd"
          type="checkbox"
          checked={dateTbd}
          onChange={(event) => setDateTbd(event.target.checked)}
          className="h-4 w-4 rounded border-zinc-300 text-violet-600 focus:ring-violet-500 dark:border-zinc-700"
        />
        Termin steht noch nicht fest
      </label>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div>
          <label className="mb-1 block text-sm font-medium text-zinc-700 dark:text-zinc-300">
            Beginn
          </label>
          <input
            name="startsAt"
            type="datetime-local"
            required={!dateTbd}
            disabled={dateTbd}
            defaultValue={toDatetimeLocalValue(values.startsAt)}
            className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-zinc-900 focus:border-violet-500 focus:outline-none focus:ring-1 focus:ring-violet-500 disabled:bg-zinc-100 disabled:text-zinc-400 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50 dark:disabled:bg-zinc-800"
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-zinc-700 dark:text-zinc-300">
            Ende (optional)
          </label>
          <input
            name="endsAt"
            type="datetime-local"
            disabled={dateTbd}
            defaultValue={toDatetimeLocalValue(values.endsAt)}
            className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-zinc-900 focus:border-violet-500 focus:outline-none focus:ring-1 focus:ring-violet-500 disabled:bg-zinc-100 disabled:text-zinc-400 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50 dark:disabled:bg-zinc-800"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div>
          <label className="mb-1 block text-sm font-medium text-zinc-700 dark:text-zinc-300">
            Max. Teilnehmende
          </label>
          <input
            name="capacity"
            type="number"
            min={1}
            required
            defaultValue={values.capacity}
            className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-zinc-900 focus:border-violet-500 focus:outline-none focus:ring-1 focus:ring-violet-500 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50"
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-zinc-700 dark:text-zinc-300">
            Reihenfolge auf der Webseite
          </label>
          <input
            name="order"
            type="number"
            defaultValue={values.order}
            className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-zinc-900 focus:border-violet-500 focus:outline-none focus:ring-1 focus:ring-violet-500 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50"
          />
        </div>
      </div>

      {state.status === "error" && (
        <p className="text-sm text-red-600 dark:text-red-400">
          {state.message}
        </p>
      )}
      {state.status === "idle" && state.message && (
        <p className="text-sm text-green-700 dark:text-green-400">
          {state.message}
        </p>
      )}

      <button
        type="submit"
        disabled={pending}
        className="self-start rounded-lg bg-violet-600 px-4 py-2 font-medium text-white transition hover:bg-violet-700 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {pending ? "Speichern…" : submitLabel}
      </button>
    </form>
  );
}
