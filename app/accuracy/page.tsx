import { AccuracyDashboard } from "@/components/accuracy-dashboard"

export default function AccuracyPage() {
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Detection Accuracy</h1>
      <p className="text-muted-foreground">Track the accuracy of object detection for each camera</p>
      <AccuracyDashboard />
    </div>
  )
}
