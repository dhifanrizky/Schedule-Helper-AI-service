import { test, expect } from "@playwright/test";

test("loads dashboard start state", async ({ page }) => {
  await page.goto("/dashboard");
  await expect(page.getByText("Schedule Helper")).toBeVisible();
});
