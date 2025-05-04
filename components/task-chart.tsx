"use client"

import { useEffect, useRef } from "react"
import { useTaskStore } from "@/lib/stores/task-store"

interface TaskChartProps {
  period: "today" | "week" | "month"
}

export function TaskChart({ period }: TaskChartProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const { taskRecords } = useTaskStore()

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext("2d")
    if (!ctx) return

    // Set canvas dimensions
    canvas.width = canvas.offsetWidth
    canvas.height = canvas.offsetHeight

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    // Chart dimensions
    const padding = 40
    const chartWidth = canvas.width - padding * 2
    const chartHeight = canvas.height - padding * 2

    // Get date range based on period
    const endDate = new Date()
    endDate.setHours(23, 59, 59, 999)

    const startDate = new Date()
    let labels: string[] = []
    let interval = 1

    if (period === "today") {
      startDate.setHours(0, 0, 0, 0)
      // Create hourly labels
      labels = Array.from({ length: 24 }, (_, i) => `${i}:00`)
      interval = 1
    } else if (period === "week") {
      startDate.setDate(startDate.getDate() - 6)
      startDate.setHours(0, 0, 0, 0)
      // Create daily labels for the past week
      labels = Array.from({ length: 7 }, (_, i) => {
        const date = new Date(startDate)
        date.setDate(date.getDate() + i)
        return date.toLocaleDateString("en-US", { weekday: "short" })
      })
      interval = 24
    } else if (period === "month") {
      startDate.setDate(startDate.getDate() - 29)
      startDate.setHours(0, 0, 0, 0)
      // Create labels for each 3 days
      labels = Array.from({ length: 10 }, (_, i) => {
        const date = new Date(startDate)
        date.setDate(date.getDate() + i * 3)
        return date.toLocaleDateString("en-US", { month: "short", day: "numeric" })
      })
      interval = 24 * 3
    }

    // Filter records for the selected period
    const filteredRecords = taskRecords.filter((record) => {
      const recordDate = new Date(record.timestamp)
      return recordDate >= startDate && recordDate <= endDate
    })

    // Group records by time interval
    const completedData: number[] = []
    const failedData: number[] = []

    if (period === "today") {
      // Group by hour
      for (let hour = 0; hour < 24; hour++) {
        const hourStart = new Date(startDate)
        hourStart.setHours(hour, 0, 0, 0)

        const hourEnd = new Date(startDate)
        hourEnd.setHours(hour, 59, 59, 999)

        const hourRecords = filteredRecords.filter((record) => {
          const recordDate = new Date(record.timestamp)
          return recordDate >= hourStart && recordDate <= hourEnd
        })

        completedData.push(hourRecords.filter((r) => r.status === "completed").length)
        failedData.push(hourRecords.filter((r) => r.status === "failed").length)
      }
    } else if (period === "week") {
      // Group by day
      for (let day = 0; day < 7; day++) {
        const dayStart = new Date(startDate)
        dayStart.setDate(dayStart.getDate() + day)

        const dayEnd = new Date(dayStart)
        dayEnd.setHours(23, 59, 59, 999)

        const dayRecords = filteredRecords.filter((record) => {
          const recordDate = new Date(record.timestamp)
          return recordDate >= dayStart && recordDate <= dayEnd
        })

        completedData.push(dayRecords.filter((r) => r.status === "completed").length)
        failedData.push(dayRecords.filter((r) => r.status === "failed").length)
      }
    } else if (period === "month") {
      // Group by 3 days
      for (let i = 0; i < 10; i++) {
        const periodStart = new Date(startDate)
        periodStart.setDate(periodStart.getDate() + i * 3)

        const periodEnd = new Date(periodStart)
        periodEnd.setDate(periodEnd.getDate() + 2)
        periodEnd.setHours(23, 59, 59, 999)

        const periodRecords = filteredRecords.filter((record) => {
          const recordDate = new Date(record.timestamp)
          return recordDate >= periodStart && recordDate <= periodEnd
        })

        completedData.push(periodRecords.filter((r) => r.status === "completed").length)
        failedData.push(periodRecords.filter((r) => r.status === "failed").length)
      }
    }

    // Find max value for scaling
    const maxValue = Math.max(
      ...completedData,
      ...failedData,
      1, // Ensure we have at least a scale of 1
    )

    // Draw axes
    ctx.beginPath()
    ctx.moveTo(padding, padding)
    ctx.lineTo(padding, canvas.height - padding)
    ctx.lineTo(canvas.width - padding, canvas.height - padding)
    ctx.strokeStyle = "#ccc"
    ctx.stroke()

    // Draw y-axis labels
    ctx.textAlign = "right"
    ctx.textBaseline = "middle"
    ctx.fillStyle = "#666"
    ctx.font = "12px sans-serif"

    const yAxisSteps = 5
    for (let i = 0; i <= yAxisSteps; i++) {
      const y = canvas.height - padding - (i / yAxisSteps) * chartHeight
      const value = Math.round((i / yAxisSteps) * maxValue)
      ctx.fillText(value.toString(), padding - 10, y)

      // Draw horizontal grid lines
      ctx.beginPath()
      ctx.moveTo(padding, y)
      ctx.lineTo(canvas.width - padding, y)
      ctx.strokeStyle = "#eee"
      ctx.stroke()
    }

    // Draw x-axis labels
    ctx.textAlign = "center"
    ctx.textBaseline = "top"

    const barWidth = chartWidth / labels.length / 3

    labels.forEach((label, i) => {
      const x = padding + (i + 0.5) * (chartWidth / labels.length)
      ctx.fillText(label, x, canvas.height - padding + 10)
    })

    // Draw bars
    completedData.forEach((value, i) => {
      const barHeight = (value / maxValue) * chartHeight
      const x = padding + (i + 0.3) * (chartWidth / completedData.length)
      const y = canvas.height - padding - barHeight

      ctx.fillStyle = "#10b981" // Green for completed
      ctx.fillRect(x, y, barWidth, barHeight)
    })

    failedData.forEach((value, i) => {
      const barHeight = (value / maxValue) * chartHeight
      const x = padding + (i + 0.6) * (chartWidth / failedData.length)
      const y = canvas.height - padding - barHeight

      ctx.fillStyle = "#ef4444" // Red for failed
      ctx.fillRect(x, y, barWidth, barHeight)
    })

    // Draw legend
    ctx.fillStyle = "#10b981"
    ctx.fillRect(padding, padding - 20, 15, 15)

    ctx.fillStyle = "#ef4444"
    ctx.fillRect(padding + 100, padding - 20, 15, 15)

    ctx.textAlign = "left"
    ctx.textBaseline = "middle"
    ctx.fillStyle = "#666"
    ctx.font = "12px sans-serif"
    ctx.fillText("Completed", padding + 20, padding - 12.5)
    ctx.fillText("Failed", padding + 120, padding - 12.5)
  }, [taskRecords, period])

  return (
    <div className="w-full h-80">
      <canvas ref={canvasRef} className="w-full h-full" />
    </div>
  )
}
