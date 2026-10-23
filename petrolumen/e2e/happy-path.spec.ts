import { test, expect } from '@playwright/test';
import path from 'path';

test.describe('Desktop Core User Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Mock Auth API responses
    await page.route('**/api/v1/auth/token', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'mock-jwt-token',
          token_type: 'bearer',
        }),
      });
    });

    await page.route('**/api/v1/users/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 1,
          username: 'admin',
          email: 'admin@example.com',
          full_name: 'Admin User',
          role: 'admin',
          is_active: true,
        }),
      });
    });

    await page.route('**/api/v1/wells', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          wells: ['TestWell'],
        }),
      });
    });

    await page.route('**/api/v1/wells/*/preview**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          well_name: 'TestWell',
          preview: [{ Date: '2023-01-01', Time: 1, Rate: 1000 }],
        }),
      });
    });

    await page.route('**/api/v1/wells/*/statistics**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          well_name: 'TestWell',
          statistics: { rows: 5, columns: ['Date', 'Time', 'Rate'] },
        }),
      });
    });

    // Mock API calls for well upload and DCA analysis
    await page.route('**/api/v1/wells/*/data', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          message: 'Upload successful!',
          well_name: 'TestWell',
          files_processed: ['test-data.csv'],
          data_preview_first_5_rows: [
            { Date: '2023-01-01', Time: 1, Rate: 1000 },
          ],
        }),
      });
    });

    await page.route('**/api/v1/gaia/dca/duong', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          parameters: {
            a: 1.2345,
            m: 0.6789,
          },
        }),
      });
    });
  });

  test('Upload well data file, run DCA analysis, and export PDF report', async ({ page }) => {
    // 1. Navigate to the app
    await page.goto('/');

    // 2. Ensure Data Management tab is active
    await page.getByRole('tab', { name: /Data Management/i }).click();

    // 3. Perform login if login form is present
    const usernameInput = page.locator('#username');
    if (await usernameInput.isVisible()) {
      await usernameInput.fill('admin');
      const passwordInput = page.locator('#password');
      await passwordInput.fill('password123');
      await page.getByRole('button', { name: 'Login' }).click();
    }

    // 4. Upload sample CSV file
    const wellNameInput = page.locator('#wellNameUpload');
    await expect(wellNameInput).toBeVisible();
    await wellNameInput.fill('TestWell');

    const fileInput = page.locator('#fileUpload');
    const csvFilePath = path.join(__dirname, 'test-data.csv');
    await fileInput.setInputFiles(csvFilePath);

    // 5. Click Upload button and wait for success state
    await page.getByRole('button', { name: /Upload Data/i }).click();
    await expect(page.getByText('Upload successful!')).toBeVisible();

    // 6. Navigate to DCA page
    await page.goto('/dca');

    // 7. Trigger DCA analysis
    await page.getByRole('button', { name: /Run Analysis/i }).click();

    // 8. Verify analysis results are rendered
    await expect(page.getByText('Duong Param a')).toBeVisible();
    await expect(page.getByText('1.2345')).toBeVisible();

    // 9. Click Export PDF button and assert download event
    const downloadPromise = page.waitForEvent('download');
    await page.getByRole('button', { name: /Export PDF Report/i }).click();
    const download = await downloadPromise;

    expect(download.suggestedFilename()).toBe('dca-report.pdf');
  });
});
