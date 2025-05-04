import { CameraGrid } from "@/components/camera-grid"
import { TaskControls } from "@/components/task-controls"

export default function DashboardPage() {
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Camera Dashboard</h1>
        <TaskControls />
      </div>
      <CameraGrid />
    </div>
  )
}
