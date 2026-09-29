declare module "occt-import-js" {
  type OcctOptions = {
    locateFile?: (path: string, prefix: string) => string;
    wasmBinary?: Uint8Array;
  };
  type OcctMesh = {
    attributes: {
      normal?: { array: ArrayLike<number> };
      position: { array: ArrayLike<number> };
    };
    color?: ArrayLike<number>;
    index?: { array: ArrayLike<number> };
    name?: string;
  };
  type OcctResult = {
    meshes: Array<OcctMesh>;
    success: boolean;
  };
  type OcctApi = {
    ReadStepFile: (buffer: Uint8Array, options: unknown) => OcctResult;
  };
  export default function occtImportJs(options?: OcctOptions): Promise<OcctApi>;
}
