import { test, expect } from '@playwright/test';
import { projectCopy } from './project-copy';

// Signed in as the seeded user through storageState (see playwright.config.ts).

test('the sidebar lists the seeded projects', async ({ page }) => {
  await page.goto('/projects');
  const sidebar = page.getByRole('navigation', { name: projectCopy.sidebarLabel });
  await expect(sidebar.getByRole('link')).toHaveText(['Acme Launch', 'Beta Site']);
});

test('opening a project shows its board', async ({ page }) => {
  await page.goto('/projects');
  await page.getByRole('link', { name: 'Acme Launch' }).click();
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Acme Launch');
  await expect(page.getByTestId('board')).toBeVisible();
});
