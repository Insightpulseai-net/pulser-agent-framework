import { chromium, FullConfig } from '@playwright/test';

async function globalSetup(config: FullConfig) {
  const baseURL = config.projects[0].use.baseURL || 'http://localhost:8069';

  console.log(`\n🔧 Global Setup - Checking Odoo at ${baseURL}\n`);

  // Wait for Odoo to be available
  const browser = await chromium.launch();
  const page = await browser.newPage();

  let retries = 10;
  while (retries > 0) {
    try {
      await page.goto(baseURL + '/web/login', { timeout: 10000 });
      console.log('✅ Odoo is available');
      break;
    } catch (error) {
      retries--;
      if (retries === 0) {
        console.error('❌ Odoo not available after 10 retries');
        throw new Error('Odoo service not available');
      }
      console.log(`⏳ Waiting for Odoo... (${retries} retries left)`);
      await new Promise((resolve) => setTimeout(resolve, 5000));
    }
  }

  await browser.close();
}

export default globalSetup;
