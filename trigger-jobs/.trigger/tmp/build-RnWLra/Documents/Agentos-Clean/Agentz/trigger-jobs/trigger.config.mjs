import {
  defineConfig
} from "../../../../chunk-DY4YI7G3.mjs";
import {
  init_esm
} from "../../../../chunk-XVMCOVNG.mjs";

// trigger.config.ts
init_esm();
var trigger_config_default = defineConfig({
  // Real project ID from Trigger.dev
  project: "proj_oszoiqgyzofujbljgxau",
  dirs: ["./src/trigger"],
  retries: {
    enabledInDev: false,
    default: {
      maxAttempts: 3,
      minTimeoutInMs: 1e3,
      maxTimeoutInMs: 1e4,
      factor: 2,
      randomize: true
    }
  },
  // 5 minutes max duration for tasks
  maxDuration: 300,
  build: {}
});
var resolveEnvVars = void 0;
export {
  trigger_config_default as default,
  resolveEnvVars
};
//# sourceMappingURL=trigger.config.mjs.map
