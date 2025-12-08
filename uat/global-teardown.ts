import { FullConfig } from '@playwright/test';

async function globalTeardown(config: FullConfig) {
  console.log('\n🧹 Global Teardown - Cleaning up test artifacts\n');

  // Add any cleanup logic here
  // - Reset database state if needed
  // - Clear test data
  // - Generate summary reports
}

export default globalTeardown;
