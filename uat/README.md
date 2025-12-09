# Concur Suite UAT Tests

Automated User Acceptance Tests for the InsightPulseAI Concur Suite on Odoo 18 CE/OCA.

## Overview

These tests validate end-to-end business flows for:
- Expense report submission and approval
- Cash advance request and liquidation
- Travel request management
- Corporate card reconciliation
- Navigation health checks

## Prerequisites

- Node.js 18+
- npm or yarn
- Odoo instance running (local or remote)

## Setup

1. Install dependencies:
```bash
npm install
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your Odoo URL and test credentials
```

3. Install Playwright browsers:
```bash
npx playwright install chromium
```

## Running Tests

### Run all tests
```bash
npm test
# or
npx playwright test
```

### Run with visible browser
```bash
npm run test:headed
# or
npx playwright test --headed
```

### Run specific test file
```bash
npx playwright test expense-flow
npx playwright test cash-advance-flow
npx playwright test navigation-health
```

### Run with UI mode
```bash
npm run test:ui
```

### View test report
```bash
npm run report
```

## Using Make Commands

From the repository root:

```bash
# Run all UAT tests
make uat

# Run with browser visible
make uat-headed

# View test report
make uat-report
```

## Test Structure

```
uat/
├── tests/
│   ├── fixtures.ts           # Shared test utilities
│   ├── expense-flow.spec.ts  # Expense report workflow
│   ├── cash-advance-flow.spec.ts  # Cash advance workflow
│   └── navigation-health.spec.ts  # Navigation checks
├── playwright.config.ts      # Playwright configuration
├── global-setup.ts           # Pre-test setup
├── global-teardown.ts        # Post-test cleanup
└── package.json
```

## Test Users

| Role | Login | Password | Purpose |
|------|-------|----------|---------|
| Employee | employee@test.com | demo123 | Standard user flows |
| Manager | manager@test.com | demo123 | Approval testing |
| Finance | finance@test.com | demo123 | Posting, reconciliation |
| Admin | admin | admin | System configuration |

## Writing New Tests

1. Create a new test file in `tests/`:
```typescript
import { test, expect, loginAsUser, waitForView } from './fixtures';

test.describe('My New Flow', () => {
  test('should do something', async ({ page }) => {
    await loginAsUser(page, 'employee');
    // Your test steps
  });
});
```

2. Use the shared fixtures for common operations:
- `loginAsUser(page, role)` - Login as a specific user
- `navigateToMenu(page, ...path)` - Navigate through menus
- `clickButton(page, text)` - Click a button
- `waitForView(page)` - Wait for Odoo view to load

## CI Integration

Tests run automatically via GitHub Actions on:
- Push to `main`
- Pull requests

See `.github/workflows/concur-suite.yml` for configuration.

## Troubleshooting

### Tests fail to find elements
- Odoo's DOM structure may vary by version
- Use `npx playwright codegen http://localhost:8069` to discover selectors
- Update selectors in `fixtures.ts`

### Connection timeouts
- Ensure Odoo is running: `make stack-up`
- Check `ODOO_URL` in `.env`
- Increase timeouts in `playwright.config.ts`

### Screenshots on failure
Failed test screenshots are saved to `test-results/`

## License

MIT - InsightPulseAI
