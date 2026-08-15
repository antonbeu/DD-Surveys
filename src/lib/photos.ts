import fs from "fs";
import path from "path";

const GALLERY_DIR = path.join(process.cwd(), "public", "fotos");
const HERO_PHOTO_CANDIDATES = ["lars-hero.jpg", "lars-hero.jpeg", "lars-hero.png"];
const IMAGE_EXTENSIONS = new Set([".jpg", ".jpeg", ".png", ".webp"]);

export function getGalleryPhotos(): string[] {
  if (!fs.existsSync(GALLERY_DIR)) return [];

  return fs
    .readdirSync(GALLERY_DIR)
    .filter((file) => IMAGE_EXTENSIONS.has(path.extname(file).toLowerCase()))
    .sort()
    .map((file) => `/fotos/${file}`);
}

export function getHeroPhoto(): string | null {
  for (const candidate of HERO_PHOTO_CANDIDATES) {
    if (fs.existsSync(path.join(process.cwd(), "public", candidate))) {
      return `/${candidate}`;
    }
  }
  return null;
}
