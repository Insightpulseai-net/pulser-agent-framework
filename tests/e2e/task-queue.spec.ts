// Task Queue E2E Tests - Playwright
// Tests for task queue operations and UI

import { test, expect } from '@playwright/test'

test.describe('Task Queue Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000/dashboard/task-queue')
  })

  test('should display task queue stats', async ({ page }) => {
    // Wait for page to load
    await page.waitForSelector('h1:has-text("Task Queue Monitor")')

    // Check for stat cards
    const totalTasks = await page.locator('text=Total Tasks').count()
    expect(totalTasks).toBeGreaterThan(0)

    const processing = await page.locator('text=Processing').count()
    expect(processing).toBeGreaterThan(0)

    const completed = await page.locator('text=Completed').count()
    expect(completed).toBeGreaterThan(0)

    const failed = await page.locator('text=Failed').count()
    expect(failed).toBeGreaterThan(0)
  })

  test('should display task list', async ({ page }) => {
    // Wait for task table
    await page.waitForSelector('table')

    // Check for table headers
    await expect(page.locator('th:has-text("Kind")')).toBeVisible()
    await expect(page.locator('th:has-text("Status")')).toBeVisible()
    await expect(page.locator('th:has-text("Priority")')).toBeVisible()
    await expect(page.locator('th:has-text("Attempts")')).toBeVisible()

    // Check for at least one task row
    const rows = await page.locator('tbody tr').count()
    expect(rows).toBeGreaterThan(0)
  })

  test('should filter tasks by status', async ({ page }) => {
    // Click on "Completed" stat card
    await page.click('text=Completed')

    // Wait for filtered results
    await page.waitForTimeout(500)

    // All visible tasks should have "Completed" status
    const statusBadges = await page.locator('.status-badge').allTextContents()
    statusBadges.forEach(badge => {
      expect(badge).toContain('Completed')
    })
  })

  test('should show real-time updates', async ({ page }) => {
    // Get initial task count
    const initialCount = await page.locator('tbody tr').count()

    // Trigger new task creation (via API)
    await page.evaluate(async () => {
      await fetch('/api/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          kind: 'TEST_TASK',
          payload: { test: true },
          priority: 5,
        }),
      })
    })

    // Wait for real-time update
    await page.waitForTimeout(1000)

    // Task count should increase
    const newCount = await page.locator('tbody tr').count()
    expect(newCount).toBeGreaterThan(initialCount)
  })
})

test.describe('Task Queue API', () => {
  test('should create new task', async ({ request }) => {
    const response = await request.post('/api/tasks', {
      data: {
        kind: 'BIR_FORM_FILING',
        payload: {
          bir_form_id: '123e4567-e89b-12d3-a456-426614174000',
          form_type: '1601-C',
        },
        priority: 8,
      },
    })

    expect(response.ok()).toBeTruthy()
    const body = await response.json()
    expect(body.task).toBeDefined()
    expect(body.task.kind).toBe('BIR_FORM_FILING')
    expect(body.task.status).toBe('pending')
  })

  test('should get tasks with filters', async ({ request }) => {
    const response = await request.get('/api/tasks?status=pending&limit=10')

    expect(response.ok()).toBeTruthy()
    const body = await response.json()
    expect(body.tasks).toBeDefined()
    expect(Array.isArray(body.tasks)).toBeTruthy()
  })

  test('should update task status', async ({ request }) => {
    // First create a task
    const createResponse = await request.post('/api/tasks', {
      data: {
        kind: 'TEST_TASK',
        payload: { test: true },
        priority: 5,
      },
    })

    const { task } = await createResponse.json()

    // Update task status
    const updateResponse = await request.patch('/api/tasks', {
      data: {
        id: task.id,
        status: 'completed',
        result: { success: true },
      },
    })

    expect(updateResponse.ok()).toBeTruthy()
    const body = await updateResponse.json()
    expect(body.task.status).toBe('completed')
  })
})
