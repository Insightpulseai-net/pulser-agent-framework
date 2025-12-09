import { test, expect, loginAsUser, navigateToMenu, clickButton, waitForView } from './fixtures';

test.describe('Expense Report Flow', () => {
  test.describe.configure({ mode: 'serial' });

  let expenseName: string;

  test('Employee creates and submits expense', async ({ page }) => {
    await loginAsUser(page, 'employee');

    // Navigate to Expenses
    await navigateToMenu(page, 'Expenses');
    await waitForView(page);

    // Click Create
    await clickButton(page, 'Create');
    await page.waitForSelector('form.o_form_view', { timeout: 10000 });

    // Fill expense form
    expenseName = `Test Expense ${Date.now()}`;

    // Fill description
    const nameField = page.locator('input[name="name"]').first();
    await nameField.fill(expenseName);

    // Select expense category (product)
    const productField = page.locator('.o_field_many2one[name="product_id"] input').first();
    await productField.click();
    await page.waitForTimeout(500);
    // Select first available product
    const firstOption = page.locator('.o_m2o_dropdown_option, .ui-autocomplete li').first();
    if (await firstOption.isVisible()) {
      await firstOption.click();
    }

    // Fill amount
    const amountField = page.locator('input[name="unit_amount"]').first();
    await amountField.fill('1500');

    // Save
    await clickButton(page, 'Save');
    await page.waitForLoadState('networkidle');

    // Verify expense created
    await expect(page.locator(`.o_form_view:has-text("${expenseName}")`)).toBeVisible();

    console.log(`✅ Expense "${expenseName}" created`);
  });

  test('Employee submits expense for approval', async ({ page }) => {
    await loginAsUser(page, 'employee');

    // Navigate to My Expenses
    await navigateToMenu(page, 'Expenses', 'My Expenses');
    await waitForView(page);

    // Find and open our expense
    const expenseRow = page.locator(`tr:has-text("${expenseName}")`).first();
    if (await expenseRow.isVisible()) {
      await expenseRow.click();
      await waitForView(page);

      // Click Submit
      const submitButton = page.locator('button:has-text("Submit")').first();
      if (await submitButton.isVisible()) {
        await submitButton.click();
        await page.waitForLoadState('networkidle');
        console.log('✅ Expense submitted');
      }
    }
  });

  test('Manager approves expense', async ({ page }) => {
    await loginAsUser(page, 'manager');

    // Navigate to expenses to approve
    await navigateToMenu(page, 'Expenses');
    await waitForView(page);

    // Look for expense reports to approve or all expenses
    const toApproveMenu = page.locator('a:has-text("To Approve")').first();
    if (await toApproveMenu.isVisible()) {
      await toApproveMenu.click();
      await waitForView(page);
    }

    // Find and open expense
    const expenseRow = page.locator(`tr:has-text("${expenseName}")`).first();
    if (await expenseRow.isVisible()) {
      await expenseRow.click();
      await waitForView(page);

      // Click Approve
      const approveButton = page.locator('button:has-text("Approve")').first();
      if (await approveButton.isVisible()) {
        await approveButton.click();
        await page.waitForLoadState('networkidle');
        console.log('✅ Expense approved by manager');
      }
    }
  });

  test('Finance posts expense to journal', async ({ page }) => {
    await loginAsUser(page, 'finance');

    // Navigate to expenses
    await navigateToMenu(page, 'Expenses');
    await waitForView(page);

    // Find approved expense
    const expenseRow = page.locator(`tr:has-text("${expenseName}")`).first();
    if (await expenseRow.isVisible()) {
      await expenseRow.click();
      await waitForView(page);

      // Click Post (if available)
      const postButton = page.locator('button:has-text("Post")').first();
      if (await postButton.isVisible()) {
        await postButton.click();
        await page.waitForLoadState('networkidle');
        console.log('✅ Expense posted to journal');
      }
    }
  });
});
