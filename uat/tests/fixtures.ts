import { test as base, expect, Page } from '@playwright/test';

// Test user credentials
export const USERS = {
  employee: {
    login: process.env.TEST_EMPLOYEE_LOGIN || 'employee@test.com',
    password: process.env.TEST_EMPLOYEE_PASSWORD || 'demo123',
  },
  manager: {
    login: process.env.TEST_MANAGER_LOGIN || 'manager@test.com',
    password: process.env.TEST_MANAGER_PASSWORD || 'demo123',
  },
  finance: {
    login: process.env.TEST_FINANCE_LOGIN || 'finance@test.com',
    password: process.env.TEST_FINANCE_PASSWORD || 'demo123',
  },
  admin: {
    login: process.env.TEST_ADMIN_LOGIN || 'admin',
    password: process.env.TEST_ADMIN_PASSWORD || 'admin',
  },
};

// Helper to login to Odoo
export async function loginAsUser(page: Page, role: keyof typeof USERS) {
  const user = USERS[role];
  const db = process.env.ODOO_DB || 'odoo';

  await page.goto('/web/login');

  // Fill login form
  await page.fill('input[name="login"]', user.login);
  await page.fill('input[name="password"]', user.password);

  // Select database if dropdown exists
  const dbSelect = page.locator('select[name="db"]');
  if (await dbSelect.isVisible()) {
    await dbSelect.selectOption(db);
  }

  // Submit form
  await page.click('button[type="submit"]');

  // Wait for navigation
  await page.waitForURL('**/web**', { timeout: 30000 });

  // Verify logged in
  const userMenu = page.locator('.o_user_menu, .oe_user_menu_placeholder');
  await expect(userMenu).toBeVisible({ timeout: 10000 });

  console.log(`✅ Logged in as ${role}`);
}

// Helper to navigate to a menu
export async function navigateToMenu(page: Page, ...menuPath: string[]) {
  for (const menuItem of menuPath) {
    const menu = page.locator(`a:has-text("${menuItem}"), button:has-text("${menuItem}")`).first();
    await menu.click();
    await page.waitForLoadState('networkidle');
  }
}

// Helper to wait for view to load
export async function waitForView(page: Page) {
  await page.waitForLoadState('networkidle');
  await page.waitForSelector('.o_view_controller, .o_content', { timeout: 30000 });
}

// Helper to click a button by text
export async function clickButton(page: Page, text: string) {
  const button = page.locator(`button:has-text("${text}"), a.btn:has-text("${text}")`).first();
  await button.click();
  await page.waitForLoadState('networkidle');
}

// Helper to fill a form field
export async function fillField(page: Page, fieldName: string, value: string) {
  const field = page.locator(`input[name="${fieldName}"], textarea[name="${fieldName}"]`).first();
  await field.fill(value);
}

// Helper to select from dropdown
export async function selectOption(page: Page, fieldName: string, optionText: string) {
  const select = page.locator(`select[name="${fieldName}"]`).first();
  if (await select.isVisible()) {
    await select.selectOption({ label: optionText });
  } else {
    // Many2one field with autocomplete
    const input = page.locator(`input[name="${fieldName}"]`).first();
    await input.fill(optionText);
    await page.waitForTimeout(500);
    const option = page.locator(`.ui-autocomplete li:has-text("${optionText}")`).first();
    await option.click();
  }
}

// Extended test with helpers
export const test = base.extend<{
  loginAs: (role: keyof typeof USERS) => Promise<void>;
}>({
  loginAs: async ({ page }, use) => {
    await use(async (role) => {
      await loginAsUser(page, role);
    });
  },
});

export { expect } from '@playwright/test';
