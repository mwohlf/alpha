import { defineConfig } from "orval";

export default defineConfig({
  myApi: {
    // 1. Where is your Swagger/OpenAPI file? (Can be a local path or a live URL)
    input: "../etc/alpha-service.yaml",

    output: {
      // 2. Where should Orval put the generated code?
      target: "./src/api/generated/endpoints.ts",
      schemas: "./src/api/generated/models",

      // 3. Generate TanStack Query hooks instead of plain fetch calls
      client: "react-query",

      // 4. (Optional) Splits files cleanly based on your API tags
      mode: "tags-split",
    },
  },
});
