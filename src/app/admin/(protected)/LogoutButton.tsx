import { logoutAction } from "./actions";

export function LogoutButton() {
  return (
    <form action={logoutAction}>
      <button
        type="submit"
        className="text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300"
      >
        Abmelden
      </button>
    </form>
  );
}
