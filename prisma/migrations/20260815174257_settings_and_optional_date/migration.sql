-- AlterTable
ALTER TABLE "Activity" ADD COLUMN     "dateTbd" BOOLEAN NOT NULL DEFAULT false,
ALTER COLUMN "startsAt" DROP NOT NULL;

-- CreateTable
CREATE TABLE "SiteSettings" (
    "id" TEXT NOT NULL DEFAULT 'main',
    "heroEyebrow" TEXT NOT NULL DEFAULT 'Herzliche Einladung',
    "heroTitle" TEXT NOT NULL DEFAULT 'Lars wird 60! 🎉',
    "heroText" TEXT NOT NULL DEFAULT 'Ich freue mich riesig, meinen 60. Geburtstag mit euch zu feiern. Damit an allen Tagen alles gut organisiert ist, könnt ihr euch unten für die einzelnen Aktivitäten anmelden. Die Plätze sind begrenzt – meldet euch also am besten gleich an!',
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "SiteSettings_pkey" PRIMARY KEY ("id")
);
