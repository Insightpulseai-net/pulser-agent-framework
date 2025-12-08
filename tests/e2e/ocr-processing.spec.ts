// OCR Processing E2E Tests - Playwright
// Tests for OCR operations and confidence metrics

import { test, expect } from '@playwright/test'

test.describe('OCR Confidence Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000/dashboard/ocr-confidence')
  })

  test('should display OCR confidence stats', async ({ page }) => {
    // Wait for page to load
    await page.waitForSelector('h1:has-text("OCR Confidence Metrics")')

    // Check for stat cards
    await expect(page.locator('text=Average Confidence')).toBeVisible()
    await expect(page.locator('text=Total Scans')).toBeVisible()
    await expect(page.locator('text=High Confidence')).toBeVisible()
    await expect(page.locator('text=Medium Confidence')).toBeVisible()
    await expect(page.locator('text=Low Confidence')).toBeVisible()
  })

  test('should display confidence distribution chart', async ({ page }) => {
    // Wait for chart to render
    await page.waitForSelector('.recharts-wrapper')

    // Check for chart elements
    const bars = await page.locator('.recharts-bar-rectangle').count()
    expect(bars).toBeGreaterThan(0)

    // Check for axis labels
    await expect(page.locator('text=0.0-0.2,0.2-0.4,0.4-0.6,0.6-0.8,0.8-1.0')).toBeVisible()
  })

  test('should show recent OCR scans table', async ({ page }) => {
    // Wait for table
    await page.waitForSelector('table')

    // Check for table headers
    await expect(page.locator('th:has-text("Vendor")')).toBeVisible()
    await expect(page.locator('th:has-text("Amount")')).toBeVisible()
    await expect(page.locator('th:has-text("Confidence")')).toBeVisible()
    await expect(page.locator('th:has-text("Date")')).toBeVisible()

    // Check for at least one scan row
    const rows = await page.locator('tbody tr').count()
    expect(rows).toBeGreaterThan(0)
  })

  test('should filter scans by confidence range', async ({ page }) => {
    // Select confidence filter (e.g., "High Confidence >= 0.80")
    await page.selectOption('select#confidence-range', 'high')

    // Wait for filtered results
    await page.waitForTimeout(500)

    // All visible confidence values should be >= 0.80
    const confidenceValues = await page.locator('td.confidence-value').allTextContents()
    confidenceValues.forEach(value => {
      const confidence = parseFloat(value.replace('%', '')) / 100
      expect(confidence).toBeGreaterThanOrEqual(0.80)
    })
  })

  test('should show confidence badge colors', async ({ page }) => {
    // High confidence should be green
    const highConfidence = page.locator('.status-badge:has-text("95%")')
    if (await highConfidence.count() > 0) {
      await expect(highConfidence.first()).toHaveClass(/status-success/)
    }

    // Medium confidence should be yellow
    const mediumConfidence = page.locator('.status-badge:has-text("72%")')
    if (await mediumConfidence.count() > 0) {
      await expect(mediumConfidence.first()).toHaveClass(/status-warning/)
    }

    // Low confidence should be red
    const lowConfidence = page.locator('.status-badge:has-text("48%")')
    if (await lowConfidence.count() > 0) {
      await expect(lowConfidence.first()).toHaveClass(/status-error/)
    }
  })
})

test.describe('OCR Processing API', () => {
  test('should process receipt with OCR', async ({ request }) => {
    const response = await request.post('/api/ocr', {
      data: {
        expense_id: '123e4567-e89b-12d3-a456-426614174000',
        receipt_url: 'https://example.com/receipt.jpg',
        use_llm_postprocessing: false,
        tenant_id: 'test-tenant',
        workspace_id: 'test-workspace',
      },
    })

    expect(response.ok()).toBeTruthy()
    const body = await response.json()
    expect(body.result).toBeDefined()
    expect(body.result.confidence).toBeGreaterThan(0)
    expect(body.result.vendor_name).toBeDefined()
    expect(body.result.amount).toBeGreaterThan(0)
  })

  test('should process receipt with LLM post-processing', async ({ request }) => {
    const response = await request.post('/api/ocr', {
      data: {
        expense_id: '123e4567-e89b-12d3-a456-426614174001',
        receipt_url: 'https://example.com/receipt2.jpg',
        use_llm_postprocessing: true,
        tenant_id: 'test-tenant',
        workspace_id: 'test-workspace',
      },
    })

    expect(response.ok()).toBeTruthy()
    const body = await response.json()
    expect(body.result).toBeDefined()
    expect(body.result.extracted_fields).toBeDefined()
    expect(body.result.extracted_fields.vendor_confidence).toBeDefined()
  })

  test('should get OCR results with filters', async ({ request }) => {
    const response = await request.get('/api/ocr?min_confidence=0.80&limit=10')

    expect(response.ok()).toBeTruthy()
    const body = await response.json()
    expect(body.results).toBeDefined()
    expect(body.stats).toBeDefined()
    expect(body.stats.avg_confidence).toBeGreaterThan(0)
  })

  test('should calculate OCR statistics', async ({ request }) => {
    const response = await request.get('/api/ocr?limit=100')

    expect(response.ok()).toBeTruthy()
    const body = await response.json()
    expect(body.stats).toBeDefined()
    expect(body.stats.total_scans).toBeGreaterThan(0)
    expect(body.stats.high_confidence).toBeGreaterThanOrEqual(0)
    expect(body.stats.medium_confidence).toBeGreaterThanOrEqual(0)
    expect(body.stats.low_confidence).toBeGreaterThanOrEqual(0)

    // Total should equal sum of confidence categories
    const total = body.stats.high_confidence + body.stats.medium_confidence + body.stats.low_confidence
    expect(total).toBe(body.stats.total_scans)
  })

  test('should reject missing required fields', async ({ request }) => {
    const response = await request.post('/api/ocr', {
      data: {
        expense_id: '123e4567-e89b-12d3-a456-426614174002',
        // Missing receipt_url, tenant_id, workspace_id
      },
    })

    expect(response.status()).toBe(400)
    const body = await response.json()
    expect(body.error).toContain('Missing required fields')
  })

  test('should handle OCR validation errors', async ({ request }) => {
    const response = await request.post('/api/ocr', {
      data: {
        expense_id: 'invalid-uuid',
        receipt_url: 'not-a-valid-url',
        tenant_id: 'test-tenant',
        workspace_id: 'test-workspace',
      },
    })

    // May return 400 or 500 depending on validation
    expect([400, 500]).toContain(response.status())
  })
})

test.describe('OCR Confidence Thresholds', () => {
  test('should meet minimum confidence threshold', async ({ request }) => {
    const response = await request.get('/api/ocr?min_confidence=0.60')

    expect(response.ok()).toBeTruthy()
    const body = await response.json()

    // All results should meet minimum threshold
    body.results.forEach((result: any) => {
      expect(result.confidence).toBeGreaterThanOrEqual(0.60)
    })
  })

  test('should flag low confidence results', async ({ request }) => {
    const response = await request.get('/api/ocr?max_confidence=0.60')

    expect(response.ok()).toBeTruthy()
    const body = await response.json()

    // All results should be below threshold (flagged for review)
    body.results.forEach((result: any) => {
      expect(result.confidence).toBeLessThan(0.60)
    })
  })
})
