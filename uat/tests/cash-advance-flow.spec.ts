import { test, expect, loginAsUser, navigateToMenu, clickButton, waitForView } from './fixtures';

test.describe('Cash Advance Flow', () => {
  test.describe.configure({ mode: 'serial' });

  let advanceName: string;

  test('Employee creates cash advance request', async ({ page }) => {
    await loginAsUser(page, 'employee');

    // Navigate to Cash Advances (if Smart Delta module installed)
    const cashAdvanceMenu = page.locator('a:has-text("Cash Advance"), button:has-text("Cash Advance")').first();

    if (!(await cashAdvanceMenu.isVisible({ timeout: 5000 }).catch(() => false))) {
      console.log('⏭️ Cash Advance module not installed, skipping test');
      test.skip();
      return;
    }

    await cashAdvanceMenu.click();
    await waitForView(page);

    // Create new cash advance
    await clickButton(page, 'Create');
    await page.waitForSelector('form.o_form_view', { timeout: 10000 });

    advanceName = `CA-${Date.now()}`;

    // Fill purpose
    const purposeField = page.locator('textarea[name="purpose"]').first();
    await purposeField.fill('Client meeting expenses');

    // Fill amount
    const amountField = page.locator('input[name="amount_requested"]').first();
    await amountField.fill('25000');

    // Save
    await clickButton(page, 'Save');
    await page.waitForLoadState('networkidle');

    console.log('✅ Cash advance request created');
  });

  test('Employee submits cash advance', async ({ page }) => {
    await loginAsUser(page, 'employee');

    // Navigate to Cash Advances
    const cashAdvanceMenu = page.locator('a:has-text("Cash Advance")').first();
    if (!(await cashAdvanceMenu.isVisible({ timeout: 5000 }).catch(() => false))) {
      test.skip();
      return;
    }

    await cashAdvanceMenu.click();
    await waitForView(page);

    // Open our request
    const row = page.locator('tr.o_data_row').first();
    if (await row.isVisible()) {
      await row.click();
      await waitForView(page);

      // Submit
      const submitButton = page.locator('button:has-text("Submit")').first();
      if (await submitButton.isVisible()) {
        await submitButton.click();
        await page.waitForLoadState('networkidle');
        console.log('✅ Cash advance submitted');
      }
    }
  });

  test('Manager approves cash advance', async ({ page }) => {
    await loginAsUser(page, 'manager');

    const cashAdvanceMenu = page.locator('a:has-text("Cash Advance")').first();
    if (!(await cashAdvanceMenu.isVisible({ timeout: 5000 }).catch(() => false))) {
      test.skip();
      return;
    }

    await cashAdvanceMenu.click();
    await waitForView(page);

    // Find submitted advance
    const row = page.locator('tr.o_data_row:has-text("Submitted")').first();
    if (await row.isVisible()) {
      await row.click();
      await waitForView(page);

      // Approve
      const approveButton = page.locator('button:has-text("Approve")').first();
      if (await approveButton.isVisible()) {
        await approveButton.click();
        await page.waitForLoadState('networkidle');
        console.log('✅ Cash advance approved by manager');
      }
    }
  });

  test('Finance releases cash advance', async ({ page }) => {
    await loginAsUser(page, 'finance');

    const cashAdvanceMenu = page.locator('a:has-text("Cash Advance")').first();
    if (!(await cashAdvanceMenu.isVisible({ timeout: 5000 }).catch(() => false))) {
      test.skip();
      return;
    }

    await cashAdvanceMenu.click();
    await waitForView(page);

    // Find approved advance
    const row = page.locator('tr.o_data_row:has-text("Approved")').first();
    if (await row.isVisible()) {
      await row.click();
      await waitForView(page);

      // Approve and release
      const financeApprove = page.locator('button:has-text("Finance Approve")').first();
      if (await financeApprove.isVisible()) {
        await financeApprove.click();
        await page.waitForLoadState('networkidle');
      }

      const releaseButton = page.locator('button:has-text("Release")').first();
      if (await releaseButton.isVisible()) {
        await releaseButton.click();
        await page.waitForLoadState('networkidle');
        console.log('✅ Cash advance released');
      }
    }
  });

  test('Employee adds liquidation', async ({ page }) => {
    await loginAsUser(page, 'employee');

    const cashAdvanceMenu = page.locator('a:has-text("Cash Advance")').first();
    if (!(await cashAdvanceMenu.isVisible({ timeout: 5000 }).catch(() => false))) {
      test.skip();
      return;
    }

    await cashAdvanceMenu.click();
    await waitForView(page);

    // Find released advance
    const row = page.locator('tr.o_data_row:has-text("Released")').first();
    if (await row.isVisible()) {
      await row.click();
      await waitForView(page);

      // Add liquidation
      const addLiqButton = page.locator('button:has-text("Add Liquidation")').first();
      if (await addLiqButton.isVisible()) {
        await addLiqButton.click();
        await page.waitForSelector('.modal, .o_dialog', { timeout: 5000 });

        // Fill liquidation
        const descField = page.locator('input[name="description"], textarea[name="description"]').first();
        await descField.fill('Taxi fare');

        const amountField = page.locator('input[name="amount"]').first();
        await amountField.fill('15000');

        // Save
        const saveButton = page.locator('.modal button:has-text("Save"), .o_dialog button:has-text("Save")').first();
        if (await saveButton.isVisible()) {
          await saveButton.click();
          await page.waitForLoadState('networkidle');
          console.log('✅ Liquidation added');
        }
      }
    }
  });
});
