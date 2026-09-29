import type { CadPreferences, PublicCadPart } from "../shared/contracts.js";
import type { PackedMesh } from "../app/renderers/types.js";
export interface CatalogStore {
  list(): Promise<PublicCadPart[]>;
  get(id: string): Promise<PublicCadPart | null>;
  read(
    id: string,
    representation: "source" | "display",
  ): Promise<{
    part: PublicCadPart;
    format: string;
    blob?: string;
    mesh?: PackedMesh;
  }>;
  import(input: {
    blob: string;
    fileName: string;
    name?: string;
    description?: string;
    tags?: string[];
  }): Promise<PublicCadPart>;
  savePreviews(
    id: string,
    previews: PublicCadPart["previews"],
  ): Promise<PublicCadPart>;
  readSettings(): Promise<CadPreferences>;
  updateSettings(set: Partial<CadPreferences>): Promise<CadPreferences>;
  settingsLifetime: string;
  localPath?(id: string): Promise<string>;
  importPath?(path: string, fileName: string): Promise<PublicCadPart>;
}
