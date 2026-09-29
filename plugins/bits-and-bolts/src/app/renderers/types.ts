export type Point = [number, number, number];
export type Triangle = Point[];
export type PackedMesh = {
  origin: number[];
  step: number;
  positions: string;
  indices: string;
};
export type ModelSource = {
  format: string;
  bytes?: ArrayBuffer;
  mesh?: PackedMesh;
};
export type RenderState = {
  camera: string;
  mode: string;
  yaw: number;
  pitch: number;
  zoom: number;
  units: "mm" | "in";
  grid: boolean;
  host: { theme?: string };
  selection?: unknown;
};
export type RendererOptions = {
  container: HTMLElement;
  onChange: (change: Partial<RenderState>) => void;
  readWasm: () => Promise<Uint8Array>;
};
export type Renderer = {
  formats: string[];
  cameras: string[];
  modes: string[];
  load(source: ModelSource, isCurrent?: () => boolean): Promise<void>;
  draw(state: RenderState): void;
  bounds(): { size: number[] };
  triangleCount(): number;
  fit(): void;
  rotate(): void;
  exportStl(): string;
  context?(): unknown;
  capture(): { data: string; mimeType: string };
  clear(): void;
  clearSelection(): void;
  dispose(): void;
};
