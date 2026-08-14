/**
 * OpenCode Plugin: Tester Agent
 * Command: /test
 * Description: Runs lint, unit tests, and e2e tests before review
 */

export default {
  name: "tester-agent",
  description: "Run tester agent (lint + test + e2e) before review",
  
  // Register custom command
  commands: {
    "test": {
      description: "Run tester agent: lint, test, e2e",
      handler: async (context) => {
        const { exec } = await import("node:child_process");
        const { promisify } = await import("node:util");
        const execAsync = promisify(exec);
        
        try {
          console.log("🚀 Starting Tester Agent...");
          const { stdout, stderr } = await execAsync("npm run tester:agent", {
            cwd: context.projectRoot || process.cwd(),
            env: { ...process.env, FORCE_COLOR: "1" }
          });
          
          console.log(stdout);
          if (stderr) console.error(stderr);
          
          return {
            success: true,
            message: "✅ All tests passed, ready for review!"
          };
        } catch (err) {
          return {
            success: false,
            message: "❌ Tests failed. Please fix errors before review.",
            error: err.message
          };
        }
      }
    }
  },
  
  // Hook: Run tester before review (if available)
  hooks: {
    "pre-review": async (context) => {
      console.log("🔍 Running tester agent before review...");
      // This would automatically run tests before review
      // Implementation depends on OpenCode plugin API
    }
  }
};
