import { prisma } from "@/lib/db";

export async function getActivitiesForPublic() {
  const activities = await prisma.activity.findMany({
    orderBy: [{ order: "asc" }, { startsAt: "asc" }],
    include: { _count: { select: { participants: true } } },
  });

  return activities.map((activity) => ({
    ...activity,
    takenSpots: activity._count.participants,
    freeSpots: Math.max(activity.capacity - activity._count.participants, 0),
    isFull: activity._count.participants >= activity.capacity,
  }));
}

export async function getActivityForPublic(id: string) {
  const activity = await prisma.activity.findUnique({
    where: { id },
    include: { _count: { select: { participants: true } } },
  });

  if (!activity) return null;

  return {
    ...activity,
    takenSpots: activity._count.participants,
    freeSpots: Math.max(activity.capacity - activity._count.participants, 0),
    isFull: activity._count.participants >= activity.capacity,
  };
}

export function formatDate(date: Date): string {
  return new Intl.DateTimeFormat("de-DE", {
    weekday: "long",
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(date);
}

export function formatTime(date: Date): string {
  return new Intl.DateTimeFormat("de-DE", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

export function formatDateTimeRange(
  start: Date | null,
  end: Date | null,
  dateTbd: boolean = false
): string {
  if (dateTbd || !start) {
    return "Termin wird noch bekannt gegeben";
  }
  const datePart = formatDate(start);
  if (!end) {
    return `${datePart}, ${formatTime(start)} Uhr`;
  }
  return `${datePart}, ${formatTime(start)} – ${formatTime(end)} Uhr`;
}

export async function getSiteSettings() {
  return prisma.siteSettings.upsert({
    where: { id: "main" },
    update: {},
    create: { id: "main" },
  });
}
