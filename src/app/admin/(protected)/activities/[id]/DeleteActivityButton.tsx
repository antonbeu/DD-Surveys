"use client";

import { deleteActivityAction } from "../../actions";

export function DeleteActivityButton({ activityId }: { activityId: string }) {
  const boundAction = deleteActivityAction.bind(null, activityId);

  return (
    <form
      action={boundAction}
      onSubmit={(event) => {
        if (
          !window.confirm(
            "Aktivität wirklich löschen? Alle Anmeldungen dazu werden ebenfalls gelöscht."
          )
        ) {
          event.preventDefault();
        }
      }}
    >
      <button
        type="submit"
        className="rounded-lg border border-red-300 px-4 py-2 text-sm font-medium text-red-700 hover:bg-red-50 dark:border-red-800 dark:text-red-400 dark:hover:bg-red-950"
      >
        Aktivität löschen
      </button>
    </form>
  );
}
