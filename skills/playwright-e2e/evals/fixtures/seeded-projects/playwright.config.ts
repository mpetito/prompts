import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: '.',
  fullyParallel: true,
  globalSetup: './global-setup.ts',
  use: {
    baseURL: 'http://localhost:3000',
    storageState: '.auth/demo.json',
    trace: 'on-first-retry',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
  ],
  webServer: { command: 'npm run start:test', url: 'http://localhost:3000', reuseExistingServer: !process.env.CI },
});
