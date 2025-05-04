"use client"

import { useEffect, useState } from "react"
import { useStreamStore } from "@/lib/stores/stream-store"

// This is a mock WebSocket hook for demonstration
// In a real application, you would use a real WebSocket connection
export function useWebSocket(cameraId: string) {
  const [lastMessage, setLastMessage] = useState<{ data: string } | null>(null)
  const { updateStreamInfo } = useStreamStore()

  useEffect(() => {
    // Simulate WebSocket messages with random data
    const interval = setInterval(() => {
      const boundingBoxes = Array.from({ length: Math.floor(Math.random() * 3) + 1 }, () => ({
        x: Math.random() * 70,
        y: Math.random() * 70,
        width: 20,
        height: 20,
        label: Math.random() > 0.5 ? "Person" : "Car",
        confidence: Math.random(),
      }))

      // Generate random accuracy metrics
      const accuracy = {
        overall: Math.random() * 0.3 + 0.7, // 70-100%
        person: Math.random() * 0.4 + 0.6, // 60-100%
        car: Math.random() * 0.5 + 0.5, // 50-100%
        animal: Math.random() * 0.6 + 0.4, // 40-100%
      }

      const message = {
        cameraId,
        boundingBoxes,
        fps: Math.floor(Math.random() * 30) + 10,
        resolution: Math.random() > 0.5 ? "1080p" : "720p",
        bitrate: Math.floor(Math.random() * 5000) + 1000,
        latency: Math.floor(Math.random() * 200) + 50,
        isOnline: Math.random() > 0.2,
        accuracy,
      }

      setLastMessage({ data: JSON.stringify(message) })
    }, 2000)

    return () => clearInterval(interval)
  }, [cameraId, updateStreamInfo])

  return { lastMessage }
}
