"use client";

import { useActionState } from "react";
import { signupAction, type SignupState } from "./actions";

const initialState: SignupState = { status: "idle" };

export function SignupForm({
  activityId,
  isFull,
}: {
  activityId: string;
  isFull: boolean;
}) {
  const boundAction = signupAction.bind(null, activityId);
  const [state, formAction, pending] = useActionState(
    boundAction,
    initialState
  );

  if (isFull && state.status !== "success") {
    return (
      <div className="rounded-lg bg-zinc-100 p-4 text-center text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300">
        Diese Aktivität ist leider ausgebucht.
      </div>
    );
  }

  if (state.status === "success") {
    return (
      <div className="rounded-lg bg-green-50 p-4 text-green-800 dark:bg-green-950 dark:text-green-200">
        {state.message}
      </div>
    );
  }

  return (
    <form action={formAction} className="flex flex-col gap-4">
      <div>
        <label
          htmlFor="name"
          className="mb-1 block text-sm font-medium text-zinc-700 dark:text-zinc-300"
        >
          Name
        </label>
        <input
          id="name"
          name="name"
          type="text"
          required
          minLength={2}
          className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-zinc-900 focus:border-violet-500 focus:outline-none focus:ring-1 focus:ring-violet-500 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50"
          placeholder="Dein Name"
        />
      </div>
      <div>
        <label
          htmlFor="email"
          className="mb-1 block text-sm font-medium text-zinc-700 dark:text-zinc-300"
        >
          E-Mail-Adresse
        </label>
        <input
          id="email"
          name="email"
          type="email"
          required
          className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-zinc-900 focus:border-violet-500 focus:outline-none focus:ring-1 focus:ring-violet-500 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50"
          placeholder="du@beispiel.de"
        />
      </div>

      {state.status === "error" && (
        <p className="text-sm text-red-600 dark:text-red-400" aria-live="polite">
          {state.message}
        </p>
      )}

      <button
        type="submit"
        disabled={pending}
        className="rounded-lg bg-violet-600 px-4 py-2 font-medium text-white transition hover:bg-violet-700 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {pending ? "Wird angemeldet…" : "Jetzt anmelden"}
      </button>
    </form>
  );
}
