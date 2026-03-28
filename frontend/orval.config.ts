import { defineConfig } from "orval";

export default defineConfig({
  myApi: {
    input: "../etc/alpha-service.yaml",

    output: {
      // 2. Where should Orval put the generated code?
      target: "./src/generated/endpoints.ts",
      schemas: "./src/generated/models",

      // 3. Generate TanStack Query hooks instead of plain fetch calls
      client: "react-query",

      // 4. (Optional) Splits files cleanly based on your API tags
      mode: "split",

      clean: true,
    },
  },
});
