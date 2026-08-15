"use client";

import { useActionState } from "react";
import {
  updateSiteSettingsAction,
  type SettingsFormState,
} from "../actions";

const initialState: SettingsFormState = { status: "idle" };

export function SettingsForm({
  initial,
}: {
  initial: { heroEyebrow: string; heroTitle: string; heroText: string };
}) {
  const [state, formAction, pending] = useActionState(
    updateSiteSettingsAction,
    initialState
  );

  return (
    <form action={formAction} className="flex flex-col gap-4">
      <div>
        <label className="mb-1 block text-sm font-medium text-zinc-700 dark:text-zinc-300">
          Kicker-Zeile (klein, über der Überschrift)
        </label>
        <input
          name="heroEyebrow"
          type="text"
          required
          defaultValue={initial.heroEyebrow}
          className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-zinc-900 focus:border-violet-500 focus:outline-none focus:ring-1 focus:ring-violet-500 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50"
        />
      </div>

      <div>
        <label className="mb-1 block text-sm font-medium text-zinc-700 dark:text-zinc-300">
          Überschrift
        </label>
        <input
          name="heroTitle"
          type="text"
          required
          defaultValue={initial.heroTitle}
          className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-zinc-900 focus:border-violet-500 focus:outline-none focus:ring-1 focus:ring-violet-500 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50"
        />
      </div>

      <div>
        <label className="mb-1 block text-sm font-medium text-zinc-700 dark:text-zinc-300">
          Begrüßungstext
        </label>
        <textarea
          name="heroText"
          required
          rows={6}
          defaultValue={initial.heroText}
          className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-zinc-900 focus:border-violet-500 focus:outline-none focus:ring-1 focus:ring-violet-500 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50"
        />
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
        {pending ? "Speichern…" : "Speichern"}
      </button>
    </form>
  );
}
