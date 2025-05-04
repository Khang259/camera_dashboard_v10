"use client"

import { useEffect, useRef } from "react"
import type { Camera, StreamInfo } from "@/lib/types"

interface AccuracyChartProps {
  cameras: Camera[]
  streamInfo: Record<string, StreamInfo | undefined>
}

export function AccuracyChart({ cameras, streamInfo }: AccuracyChartProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)

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
    const barWidth = chartWidth / (cameras.length * 4) // 4 categories per camera

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

    for (let i = 0; i <= 10; i++) {
      const y = canvas.height - padding - (i / 10) * chartHeight
      ctx.fillText(`${i * 10}%`, padding - 10, y)

      // Draw horizontal grid lines
      ctx.beginPath()
      ctx.moveTo(padding, y)
      ctx.lineTo(canvas.width - padding, y)
      ctx.strokeStyle = "#eee"
      ctx.stroke()
    }

    // Draw bars for each camera and category
    const categories = ["overall", "person", "car", "animal"]
    const colors = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444"]

    cameras.forEach((camera, cameraIndex) => {
      const info = streamInfo[camera.id]
      if (!info || !info.accuracy) return

      // Draw camera label
      ctx.textAlign = "center"
      ctx.textBaseline = "top"
      ctx.fillStyle = "#666"
      const cameraX = padding + (cameraIndex * 4 + 2) * barWidth
      ctx.fillText(camera.name, cameraX, canvas.height - padding + 10)

      // Draw bars for each category
      categories.forEach((category, categoryIndex) => {
        const value = info.accuracy[category as keyof typeof info.accuracy] || 0
        const barHeight = chartHeight * value
        const x = padding + (cameraIndex * 4 + categoryIndex) * barWidth
        const y = canvas.height - padding - barHeight

        // Draw bar
        ctx.fillStyle = colors[categoryIndex]
        ctx.fillRect(x, y, barWidth * 0.8, barHeight)

        // Draw value on top of bar if it's tall enough
        if (barHeight > 20) {
          ctx.textAlign = "center"
          ctx.textBaseline = "bottom"
          ctx.fillStyle = "white"
          ctx.font = "10px sans-serif"
          ctx.fillText(`${Math.round(value * 100)}%`, x + barWidth * 0.4, y - 2)
        }
      })
    })

    // Draw legend
    const legendX = padding
    const legendY = padding
    categories.forEach((category, index) => {
      ctx.fillStyle = colors[index]
      ctx.fillRect(legendX + index * 100, legendY, 15, 15)

      ctx.textAlign = "left"
      ctx.textBaseline = "middle"
      ctx.fillStyle = "#666"
      ctx.font = "12px sans-serif"
      ctx.fillText(category.charAt(0).toUpperCase() + category.slice(1), legendX + index * 100 + 20, legendY + 7.5)
    })
  }, [cameras, streamInfo])

  return (
    <div className="w-full h-80">
      <canvas ref={canvasRef} className="w-full h-full" />
    </div>
  )
}
