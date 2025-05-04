import { TaskList } from "@/components/task-list"

export default function TasksPage() {
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Task Records</h1>
      <p className="text-muted-foreground">Track tasks and errors from camera object detection</p>
      <TaskList />
    </div>
  )
}
