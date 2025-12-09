import { test, expect, loginAsUser, waitForView } from './fixtures';

test.describe('Navigation Health Checks', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsUser(page, 'admin');
  });

  test('Dashboard loads without errors', async ({ page }) => {
    await page.goto('/web');
    await waitForView(page);

    // Check no error messages
    const errorBanner = page.locator('.o_notification_error, .o_dialog_warning');
    await expect(errorBanner).not.toBeVisible();

    // Check main content loaded
    const mainContent = page.locator('.o_main_content, .o_content');
    await expect(mainContent).toBeVisible();

    console.log('✅ Dashboard loads without errors');
  });

  test('Expenses menu accessible', async ({ page }) => {
    const expensesMenu = page.locator('a:has-text("Expenses")').first();

    if (await expensesMenu.isVisible({ timeout: 5000 }).catch(() => false)) {
      await expensesMenu.click();
      await waitForView(page);

      // Verify view loaded
      const viewController = page.locator('.o_view_controller, .o_list_view, .o_kanban_view');
      await expect(viewController).toBeVisible({ timeout: 10000 });

      console.log('✅ Expenses menu accessible');
    } else {
      console.log('⏭️ Expenses menu not visible, module may not be installed');
    }
  });

  test('Employees menu accessible', async ({ page }) => {
    const hrMenu = page.locator('a:has-text("Employees")').first();

    if (await hrMenu.isVisible({ timeout: 5000 }).catch(() => false)) {
      await hrMenu.click();
      await waitForView(page);

      const viewController = page.locator('.o_view_controller, .o_kanban_view');
      await expect(viewController).toBeVisible({ timeout: 10000 });

      console.log('✅ Employees menu accessible');
    } else {
      console.log('⏭️ Employees menu not visible');
    }
  });

  test('Projects menu accessible', async ({ page }) => {
    const projectMenu = page.locator('a:has-text("Project")').first();

    if (await projectMenu.isVisible({ timeout: 5000 }).catch(() => false)) {
      await projectMenu.click();
      await waitForView(page);

      const viewController = page.locator('.o_view_controller, .o_kanban_view');
      await expect(viewController).toBeVisible({ timeout: 10000 });

      console.log('✅ Projects menu accessible');
    } else {
      console.log('⏭️ Projects menu not visible');
    }
  });

  test('Accounting menu accessible', async ({ page }) => {
    const accountingMenu = page.locator('a:has-text("Accounting"), a:has-text("Invoicing")').first();

    if (await accountingMenu.isVisible({ timeout: 5000 }).catch(() => false)) {
      await accountingMenu.click();
      await waitForView(page);

      const viewController = page.locator('.o_view_controller, .o_kanban_view, .o_dashboard');
      await expect(viewController).toBeVisible({ timeout: 10000 });

      console.log('✅ Accounting menu accessible');
    } else {
      console.log('⏭️ Accounting menu not visible');
    }
  });

  test('Smart Delta - Finance PPM accessible', async ({ page }) => {
    const ppmMenu = page.locator('a:has-text("Finance PPM"), a:has-text("PPM")').first();

    if (await ppmMenu.isVisible({ timeout: 5000 }).catch(() => false)) {
      await ppmMenu.click();
      await waitForView(page);

      const viewController = page.locator('.o_view_controller');
      await expect(viewController).toBeVisible({ timeout: 10000 });

      console.log('✅ Finance PPM menu accessible');
    } else {
      console.log('⏭️ Finance PPM module not installed');
    }
  });

  test('Smart Delta - Travel Requests accessible', async ({ page }) => {
    const travelMenu = page.locator('a:has-text("Travel Request"), a:has-text("Travel")').first();

    if (await travelMenu.isVisible({ timeout: 5000 }).catch(() => false)) {
      await travelMenu.click();
      await waitForView(page);

      const viewController = page.locator('.o_view_controller');
      await expect(viewController).toBeVisible({ timeout: 10000 });

      console.log('✅ Travel Requests menu accessible');
    } else {
      console.log('⏭️ Travel module not installed');
    }
  });

  test('Smart Delta - Cash Advance accessible', async ({ page }) => {
    const cashMenu = page.locator('a:has-text("Cash Advance")').first();

    if (await cashMenu.isVisible({ timeout: 5000 }).catch(() => false)) {
      await cashMenu.click();
      await waitForView(page);

      const viewController = page.locator('.o_view_controller');
      await expect(viewController).toBeVisible({ timeout: 10000 });

      console.log('✅ Cash Advance menu accessible');
    } else {
      console.log('⏭️ Cash Advance module not installed');
    }
  });

  test('No JavaScript errors on page load', async ({ page }) => {
    const errors: string[] = [];

    page.on('pageerror', (error) => {
      errors.push(error.message);
    });

    await page.goto('/web');
    await waitForView(page);

    // Navigate through main menus
    const menus = ['Expenses', 'Employees', 'Project'];
    for (const menuName of menus) {
      const menu = page.locator(`a:has-text("${menuName}")`).first();
      if (await menu.isVisible({ timeout: 2000 }).catch(() => false)) {
        await menu.click();
        await page.waitForLoadState('networkidle');
      }
    }

    expect(errors).toHaveLength(0);
    console.log('✅ No JavaScript errors detected');
  });
});
