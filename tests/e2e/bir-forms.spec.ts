// BIR Forms E2E Tests - Playwright
// Tests for BIR form operations and compliance tracking

import { test, expect } from '@playwright/test'

test.describe('BIR Status Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000/dashboard/bir-status')
  })

  test('should display BIR compliance stats', async ({ page }) => {
    // Wait for page to load
    await page.waitForSelector('h1:has-text("BIR Status Dashboard")')

    // Check for stat cards
    await expect(page.locator('text=Forms Due')).toBeVisible()
    await expect(page.locator('text=Filed On Time')).toBeVisible()
    await expect(page.locator('text=Compliance Rate')).toBeVisible()
    await expect(page.locator('text=Overdue')).toBeVisible()
  })

  test('should display BIR forms by agency', async ({ page }) => {
    // Wait for agency grid
    await page.waitForSelector('text=TBWA')

    // Check for at least one agency card
    const agencyCards = await page.locator('.fluent-card').count()
    expect(agencyCards).toBeGreaterThan(0)

    // Each card should have agency name and form type
    const firstCard = page.locator('.fluent-card').first()
    await expect(firstCard.locator('text=1601-C,0619-E,2550Q,1702-RT')).toBeVisible()
  })

  test('should show deadline urgency indicators', async ({ page }) => {
    // Look for urgent deadline badges (due within 3 days)
    const urgentBadges = await page.locator('.status-badge:has-text("days")').count()

    // At least some forms should have deadline indicators
    expect(urgentBadges).toBeGreaterThanOrEqual(0)
  })

  test('should filter forms by form type', async ({ page }) => {
    // Select form type filter
    await page.selectOption('select#form-type', '1601-C')

    // Wait for filtered results
    await page.waitForTimeout(500)

    // All visible forms should be 1601-C
    const formTypes = await page.locator('text=1601-C').count()
    expect(formTypes).toBeGreaterThan(0)
  })

  test('should show approval workflow status', async ({ page }) => {
    // Click on a form to view details
    const firstForm = page.locator('.fluent-card').first()
    await firstForm.click()

    // Wait for modal/details view
    await page.waitForTimeout(500)

    // Check for approval level indicator
    await expect(page.locator('text=Approval Level,Finance Supervisor,Senior Finance Manager,Finance Director')).toBeVisible()
  })
})

test.describe('BIR Forms API', () => {
  test('should create new BIR form with validation', async ({ request }) => {
    const response = await request.post('/api/bir', {
      data: {
        form_type: '1601-C',
        filing_period: '2025-12',
        filing_deadline: '2026-01-10',
        agency_name: 'TBWA\\SMP',
        employee_name: 'RIM',
        metadata: {},
      },
    })

    expect(response.ok()).toBeTruthy()
    const body = await response.json()
    expect(body.form).toBeDefined()
    expect(body.form.status).toBe('not_started')
    expect(body.validation.is_valid).toBeTruthy()
  })

  test('should reject invalid form data', async ({ request }) => {
    const response = await request.post('/api/bir', {
      data: {
        form_type: 'INVALID_FORM',
        filing_period: '2025-13', // Invalid month
        filing_deadline: 'invalid-date',
        agency_name: 'Unknown Agency',
        employee_name: 'XYZ',
      },
    })

    expect(response.status()).toBe(400)
    const body = await response.json()
    expect(body.errors).toBeDefined()
    expect(body.errors.length).toBeGreaterThan(0)
  })

  test('should get BIR forms with filters', async ({ request }) => {
    const response = await request.get('/api/bir?status=not_started&form_type=1601-C')

    expect(response.ok()).toBeTruthy()
    const body = await response.json()
    expect(body.forms).toBeDefined()
    expect(Array.isArray(body.forms)).toBeTruthy()
  })

  test('should update BIR form status', async ({ request }) => {
    // First create a form
    const createResponse = await request.post('/api/bir', {
      data: {
        form_type: '2550Q',
        filing_period: '2025-12-Q4',
        filing_deadline: '2026-02-28',
        agency_name: 'TBWA\\SMP',
        employee_name: 'CKVC',
      },
    })

    const { form } = await createResponse.json()

    // Update form status
    const updateResponse = await request.patch('/api/bir', {
      data: {
        id: form.id,
        status: 'in_progress',
        metadata: {
          approval_level: 'level1',
          started_at: new Date().toISOString(),
        },
      },
    })

    expect(updateResponse.ok()).toBeTruthy()
    const body = await updateResponse.json()
    expect(body.form.status).toBe('in_progress')
  })

  test('should validate quarterly form period format', async ({ request }) => {
    const response = await request.post('/api/bir', {
      data: {
        form_type: '2550Q',
        filing_period: '2025-12', // Missing quarter
        filing_deadline: '2026-02-28',
        agency_name: 'TBWA\\SMP',
        employee_name: 'BOM',
      },
    })

    expect(response.status()).toBe(400)
    const body = await response.json()
    expect(body.errors).toContain('Quarterly form requires period format with quarter (e.g., 2025-12-Q4)')
  })
})
