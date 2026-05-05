/*
  Warnings:

  - A unique constraint covering the columns `[googleEventId]` on the table `tasks` will be added. If there are existing duplicate values, this will fail.

*/
-- AlterTable
ALTER TABLE "tasks" ADD COLUMN     "googleEventId" TEXT;

-- AlterTable
ALTER TABLE "users" ADD COLUMN     "googleAccessToken" TEXT,
ADD COLUMN     "googleRefreshToken" TEXT;

-- CreateIndex
CREATE UNIQUE INDEX "tasks_googleEventId_key" ON "tasks"("googleEventId");
