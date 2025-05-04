import { create } from "zustand"
import type { StreamInfo } from "@/lib/types"

interface StreamState {
  streamInfo: Record<string, StreamInfo>
  updateStreamInfo: (cameraId: string, info: StreamInfo) => void
}

// Generate random stream info for demo purposes
const generateRandomStreamInfo = (): StreamInfo => ({
  boundingBoxes: [
    {
      x: Math.random() * 70,
      y: Math.random() * 70,
      width: 20,
      height: 20,
      label: Math.random() > 0.5 ? "Person" : "Car",
      confidence: Math.random(),
    },
  ],
  fps: Math.floor(Math.random() * 30) + 10,
  resolution: Math.random() > 0.5 ? "1080p" : "720p",
  bitrate: Math.floor(Math.random() * 5000) + 1000,
  latency: Math.floor(Math.random() * 200) + 50,
  isOnline: Math.random() > 0.2,
  accuracy: {
    overall: Math.random() * 0.3 + 0.7, // 70-100%
    person: Math.random() * 0.4 + 0.6, // 60-100%
    car: Math.random() * 0.5 + 0.5, // 50-100%
    animal: Math.random() * 0.6 + 0.4, // 40-100%
  },
})

// Initialize with sample data for the demo
const initialStreamInfo: Record<string, StreamInfo> = {
  "1": generateRandomStreamInfo(),
  "2": generateRandomStreamInfo(),
  "3": generateRandomStreamInfo(),
}

export const useStreamStore = create<StreamState>((set) => ({
  streamInfo: initialStreamInfo,
  updateStreamInfo: (cameraId, info) =>
    set((state) => ({
      streamInfo: {
        ...state.streamInfo,
        [cameraId]: info,
      },
    })),
}))
