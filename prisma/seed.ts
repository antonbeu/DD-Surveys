import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

async function main() {
  const existing = await prisma.activity.count();
  if (existing > 0) {
    console.log("Es gibt bereits Aktivitäten, überspringe Seed.");
    return;
  }

  await prisma.activity.createMany({
    data: [
      {
        title: "Grillen im Garten",
        description:
          "Gemütliches Grillen mit guter Musik und noch besserer Gesellschaft. Für Getränke und Grillgut ist gesorgt – Beilagen dürfen gerne mitgebracht werden.",
        location: "Gartenlaube Musterstraße 1, 12345 Musterstadt",
        startsAt: new Date("2026-09-12T16:00:00"),
        endsAt: new Date("2026-09-12T22:00:00"),
        capacity: 25,
        order: 1,
      },
      {
        title: "Wanderung zur Alten Mühle",
        description:
          "Eine leichte Wanderung (ca. 8 km) mit Einkehr und Kaffee & Kuchen zur Belohnung. Festes Schuhwerk empfohlen.",
        location: "Treffpunkt: Wanderparkplatz Waldrand",
        startsAt: new Date("2026-09-13T10:00:00"),
        endsAt: new Date("2026-09-13T13:00:00"),
        capacity: 15,
        order: 2,
      },
      {
        title: "Kegelabend",
        description:
          "Wer traut sich an die Kegelbahn? Ein lustiger Abend mit Wettkampf um die goldene Kegelkugel.",
        location: "Kegelcenter Musterstadt, Bahnhofstraße 4",
        startsAt: new Date("2026-09-12T19:00:00"),
        endsAt: new Date("2026-09-12T22:00:00"),
        capacity: 12,
        order: 3,
      },
    ],
  });

  console.log("Seed-Daten wurden angelegt.");
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
