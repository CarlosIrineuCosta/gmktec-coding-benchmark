/// <reference types="vite/client" />

declare module "virtual:gallery-manifest" {
  export interface RawManifestImage {
    id: string;
    creator: string;
    height: number;
    width: number;
    license: string;
    local_filename: string;
    sha256: string;
    source_page: string;
  }
  const manifest: RawManifestImage[];
  export default manifest;
}
