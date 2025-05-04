import { TaskStatistics } from "@/components/task-statistics"

export default function StatisticsPage() {
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Task Statistics</h1>
      <p className="text-muted-foreground">View task completion statistics and trends</p>
      <TaskStatistics />
    </div>
  )
}
