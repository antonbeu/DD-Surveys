import { prisma } from "@/lib/db";
import { isAdminAuthenticated } from "@/lib/auth";

function csvEscape(value: string): string {
  if (/[",\n]/.test(value)) {
    return `"${value.replace(/"/g, '""')}"`;
  }
  return value;
}

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  if (!(await isAdminAuthenticated())) {
    return new Response("Nicht autorisiert", { status: 401 });
  }

  const { id } = await params;

  const activity = await prisma.activity.findUnique({
    where: { id },
    include: { participants: { orderBy: { createdAt: "asc" } } },
  });

  if (!activity) {
    return new Response("Nicht gefunden", { status: 404 });
  }

  const rows = [
    ["Name", "E-Mail", "Angemeldet am"],
    ...activity.participants.map((p) => [
      p.name,
      p.email,
      p.createdAt.toISOString(),
    ]),
  ];

  const csv = rows.map((row) => row.map(csvEscape).join(",")).join("\n");
  const filename = `teilnehmende-${activity.title
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")}.csv`;

  return new Response(csv, {
    headers: {
      "Content-Type": "text/csv; charset=utf-8",
      "Content-Disposition": `attachment; filename="${filename}"`,
    },
  });
}
