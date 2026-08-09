"use client";

import { useActionState } from "react";
import { sendBroadcastAction, type BroadcastState } from "../../actions";

const initialState: BroadcastState = { status: "idle" };

export function BroadcastForm({ activityId }: { activityId: string }) {
  const boundAction = sendBroadcastAction.bind(null, activityId);
  const [state, formAction, pending] = useActionState(
    boundAction,
    initialState
  );

  return (
    <form action={formAction} className="flex flex-col gap-3">
      <div>
        <label className="mb-1 block text-sm font-medium text-zinc-700 dark:text-zinc-300">
          Betreff
        </label>
        <input
          name="subject"
          type="text"
          required
          className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-zinc-900 focus:border-violet-500 focus:outline-none focus:ring-1 focus:ring-violet-500 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50"
        />
      </div>
      <div>
        <label className="mb-1 block text-sm font-medium text-zinc-700 dark:text-zinc-300">
          Nachricht
        </label>
        <textarea
          name="body"
          required
          rows={5}
          className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-zinc-900 focus:border-violet-500 focus:outline-none focus:ring-1 focus:ring-violet-500 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50"
        />
      </div>

      {state.status === "error" && (
        <p className="text-sm text-red-600 dark:text-red-400">
          {state.message}
        </p>
      )}
      {state.status === "success" && (
        <p className="text-sm text-green-700 dark:text-green-400">
          {state.message}
        </p>
      )}

      <button
        type="submit"
        disabled={pending}
        className="self-start rounded-lg bg-violet-600 px-4 py-2 font-medium text-white transition hover:bg-violet-700 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {pending ? "Wird gesendet…" : "An diese Gruppe senden"}
      </button>
    </form>
  );
}
