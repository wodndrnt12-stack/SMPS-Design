const { defineConfig } = require('@playwright/test');
const path = require('path');

module.exports = defineConfig({
  testDir: './tests',
  timeout: 30000,
  retries: 0,
  use: {
    browserName: 'chromium',
    headless: true,
    baseURL: `file:///${path.resolve(__dirname, 'index.html').replace(/\\/g, '/')}`,
  },
  reporter: [['list']],
});
