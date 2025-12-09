# Concur Suite UAT Scenarios

**Version:** 1.0.0
**Last Updated:** 2024-12-08
**Owner:** InsightPulseAI QA Team

This document describes the User Acceptance Test (UAT) scenarios for the SAP Concur-style T&E Suite.
Each scenario is mapped to automated tests in the `uat/` directory.

---

## Overview

### Test Environment
- **URL:** https://staging-erp.insightpulseai.net
- **Test Framework:** Playwright
- **Test Runner:** `make uat` or `npx playwright test`

### Test Users
| Role | Username | Password | Purpose |
|------|----------|----------|---------|
| Employee | `employee@test.com` | `demo123` | Standard expense submission |
| Manager | `manager@test.com` | `demo123` | Approval testing |
| Finance | `finance@test.com` | `demo123` | Posting and reconciliation |
| Admin | `admin@test.com` | (secure) | System configuration |

---

## Scenario 1: Employee Expense Report Flow

**Test File:** `uat/tests/expense-flow.spec.ts`
**Priority:** CRITICAL
**Estimated Duration:** 5 minutes

### Description
Employee submits an expense report with receipts, manager approves, finance posts journal entry.

### Preconditions
- Employee user exists with department assignment
- Manager is assigned as approver
- Expense policy is active

### Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Login as employee | Dashboard loads successfully |
| 2 | Navigate to Expenses > My Expenses | Expense list view displayed |
| 3 | Click "Create" | New expense form opens |
| 4 | Fill expense details (Category: Transportation, Amount: 1500 PHP) | Form accepts input |
| 5 | Upload receipt image | Receipt attached successfully |
| 6 | Save expense | Expense saved in Draft status |
| 7 | Click "Submit" | Expense moves to Submitted status |
| 8 | Logout | Session ended |
| 9 | Login as manager | Dashboard loads |
| 10 | Navigate to Expenses > To Approve | Pending expense visible |
| 11 | Open expense and click "Approve" | Expense moves to Approved status |
| 12 | Logout | Session ended |
| 13 | Login as finance | Dashboard loads |
| 14 | Navigate to Expenses > To Post | Approved expense visible |
| 15 | Click "Post" | Journal entry created |

### Acceptance Criteria
- [ ] Expense created successfully
- [ ] Receipt upload works
- [ ] Approval workflow triggers correctly
- [ ] Manager receives notification
- [ ] Journal entry posted with correct accounts

---

## Scenario 2: Cash Advance + Liquidation Flow

**Test File:** `uat/tests/cash-advance-flow.spec.ts`
**Priority:** CRITICAL
**Estimated Duration:** 7 minutes

### Description
Employee requests cash advance, gets approval, receives funds, and completes liquidation.

### Preconditions
- Employee user exists
- Cash advance rules configured
- Finance approval chain defined

### Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Login as employee | Dashboard loads |
| 2 | Navigate to Cash Advances | Cash advance list displayed |
| 3 | Click "New Request" | Request form opens |
| 4 | Fill details (Amount: 25000 PHP, Purpose: Client meeting) | Form accepts input |
| 5 | Submit request | Request in Submitted status |
| 6 | Login as manager | Manager dashboard |
| 7 | Approve cash advance | Status: Manager Approved |
| 8 | Login as finance | Finance dashboard |
| 9 | Approve and release funds | Status: Released |
| 10 | Login as employee | Employee dashboard |
| 11 | Navigate to Cash Advance > Add Liquidation | Liquidation form opens |
| 12 | Add liquidation (Amount: 15000 PHP) | Partial liquidation recorded |
| 13 | Add second liquidation (Amount: 10000 PHP) | Full liquidation complete |
| 14 | Verify status | Status: Fully Liquidated |

### Acceptance Criteria
- [ ] Cash advance request created
- [ ] Multi-level approval works
- [ ] Outstanding balance calculated correctly
- [ ] Partial liquidation recorded
- [ ] Full liquidation closes request

---

## Scenario 3: Travel Request + Per Diem

**Test File:** `uat/tests/travel-request-flow.spec.ts`
**Priority:** HIGH
**Estimated Duration:** 5 minutes

### Description
Employee submits travel request with per diem calculation.

### Preconditions
- Per diem rates configured for destinations
- Travel approval policy active

### Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Login as employee | Dashboard loads |
| 2 | Navigate to Travel Requests | Travel request list |
| 3 | Create new travel request | Form opens |
| 4 | Select destination: Cebu City | Per diem rate auto-populated |
| 5 | Set dates (3 days) | Duration calculated |
| 6 | Verify per diem total | 3 x 1800 = 5400 PHP |
| 7 | Add itinerary items | Itinerary saved |
| 8 | Submit request | Status: Submitted |
| 9 | Login as manager and approve | Status: Approved |
| 10 | Request advance from travel | Cash advance created |

### Acceptance Criteria
- [ ] Per diem rates auto-populated
- [ ] Duration calculation correct
- [ ] Total per diem computed correctly
- [ ] Itinerary tracking works
- [ ] Integration with cash advance

---

## Scenario 4: Corporate Card Import + Reconciliation

**Test File:** `uat/tests/card-reconciliation-flow.spec.ts`
**Priority:** MEDIUM
**Estimated Duration:** 6 minutes

### Description
Finance imports card statement, auto-matches transactions, handles exceptions.

### Preconditions
- Card statement module installed
- Sample CSV file available
- Employee has submitted matching expenses

### Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Login as finance | Dashboard loads |
| 2 | Navigate to Card Reconciliation | Statement list |
| 3 | Create new statement | Form opens |
| 4 | Select card holder | Employee selected |
| 5 | Import CSV file | Import wizard opens |
| 6 | Configure column mapping | Columns mapped |
| 7 | Execute import | Transactions imported |
| 8 | Click "Auto Match" | Matching executed |
| 9 | Review matched transactions | Green status indicators |
| 10 | Review exceptions | Exception queue populated |
| 11 | Manually resolve exception | Exception cleared |
| 12 | Click "Reconcile" | Statement reconciled |

### Acceptance Criteria
- [ ] CSV import works
- [ ] Auto-matching finds correct expenses
- [ ] Unmatched transactions flagged
- [ ] Exception resolution workflow
- [ ] Reconciliation completes

---

## Scenario 5: Policy Violation Warning

**Test File:** `uat/tests/policy-validation.spec.ts`
**Priority:** HIGH
**Estimated Duration:** 3 minutes

### Description
System prevents expense submission when policy is violated.

### Preconditions
- Expense policy with limits configured
- Per-transaction limit: 10000 PHP
- Receipt required above: 500 PHP

### Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Login as employee | Dashboard loads |
| 2 | Create expense with amount 15000 PHP | Form accepts input |
| 3 | Do not attach receipt | No receipt attached |
| 4 | Attempt to submit | Error: Policy violation |
| 5 | View policy violations | Shows limit exceeded + receipt required |
| 6 | Reduce amount to 8000 PHP | Amount updated |
| 7 | Attach receipt | Receipt attached |
| 8 | Submit again | Submission successful |

### Acceptance Criteria
- [ ] Policy violation detected
- [ ] Clear error message displayed
- [ ] Multiple violations listed
- [ ] Correction allows submission

---

## Scenario 6: Analytics Dashboard Load

**Test File:** `uat/tests/analytics-dashboard.spec.ts`
**Priority:** MEDIUM
**Estimated Duration:** 2 minutes

### Description
Finance dashboard loads with populated charts and KPIs.

### Preconditions
- Demo data seeded
- Dashboard widgets configured

### Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Login as finance | Dashboard loads |
| 2 | Navigate to Analytics Dashboard | Dashboard view |
| 3 | Verify expense by category chart | Chart rendered with data |
| 4 | Verify spend by employee widget | Widget populated |
| 5 | Verify pending approvals KPI | KPI shows count |
| 6 | Apply date filter | Charts update |

### Acceptance Criteria
- [ ] All charts render without error
- [ ] Charts contain demo data
- [ ] Filters work correctly
- [ ] No JavaScript console errors

---

## Running UAT Tests

### Local Execution
```bash
# Install dependencies
cd uat && npm install

# Run all tests
make uat

# Run specific test
npx playwright test expense-flow

# Run with UI
make uat-headed

# View report
make uat-report
```

### CI Execution
Tests run automatically on PR and push to main via GitHub Actions.

### Test Results
| Scenario | Status | Last Run | Duration |
|----------|--------|----------|----------|
| Expense Flow | PENDING | - | - |
| Cash Advance Flow | PENDING | - | - |
| Travel Request Flow | PENDING | - | - |
| Card Reconciliation | PENDING | - | - |
| Policy Validation | PENDING | - | - |
| Analytics Dashboard | PENDING | - | - |

---

## Sign-Off

**UAT Completed By:**

| Scenario | Tester | Date | Status |
|----------|--------|------|--------|
| Expense Flow | | | |
| Cash Advance Flow | | | |
| Travel Request Flow | | | |
| Card Reconciliation | | | |
| Policy Validation | | | |
| Analytics Dashboard | | | |

**UAT Approved:** [ ] Yes / [ ] No

**QA Lead Signature:** _______________

**Date:** _______________
