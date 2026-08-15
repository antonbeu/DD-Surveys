"use client";

import { deleteParticipantAction } from "../../actions";

export function DeleteParticipantButton({
  activityId,
  participantId,
  participantName,
}: {
  activityId: string;
  participantId: string;
  participantName: string;
}) {
  const boundAction = deleteParticipantAction.bind(
    null,
    activityId,
    participantId
  );

  return (
    <form
      action={boundAction}
      onSubmit={(event) => {
        if (
          !window.confirm(
            `${participantName} wirklich aus dieser Aktivität austragen?`
          )
        ) {
          event.preventDefault();
        }
      }}
    >
      <button
        type="submit"
        className="text-red-600 hover:underline dark:text-red-400"
      >
        Entfernen
      </button>
    </form>
  );
}
