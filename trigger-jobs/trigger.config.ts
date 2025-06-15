import { defineConfig } from "@trigger.dev/sdk/v3";

export default defineConfig({
  project: "proj_oszoiqgyzofujbljgxau", // Real project ID from Trigger.dev
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
  maxDuration: 300, // 5 minutes max duration for tasks
}); 