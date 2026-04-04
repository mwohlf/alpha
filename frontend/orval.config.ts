import { defineConfig, NamingConvention } from "orval";

export default defineConfig({
  alpha: {
    input: "../etc/alpha-service.yaml",

    output: {
      target: "./src/generated/endpoints.ts",
      schemas: "./src/generated/models",
      client: "axios",
      mode: "split",
      clean: true,
      namingConvention: NamingConvention.PASCAL_CASE,
    },
  },
});
