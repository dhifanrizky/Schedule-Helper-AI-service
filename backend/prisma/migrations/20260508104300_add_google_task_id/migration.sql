-- AlterTable
ALTER TABLE "tasks" ADD COLUMN "googleTaskId" TEXT;

-- CreateIndex
CREATE UNIQUE INDEX "tasks_googleTaskId_key" ON "tasks"("googleTaskId");