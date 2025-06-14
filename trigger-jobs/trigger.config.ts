import { defineConfig } from "@trigger.dev/sdk/v3";

export default defineConfig({
  project: "agentos-automation", // We'll update this with actual project ref
  dirs: ["./src/trigger"],
  retries: {
    enabledInDev: false,
    default: {
      maxAttempts: 3,
      minTimeoutInMs: 1000,
      maxTimeoutInMs: 10000,
      factor: 2,
      randomize: true,
    },
  },
}); 