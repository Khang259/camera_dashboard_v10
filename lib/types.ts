export interface Camera {
  id: string
  name: string
  ipAddress?: string
  streamUrl: string
}

export interface BoundingBox {
  x: number
  y: number
  width: number
  height: number
  label: string
  confidence: number
}

export interface AccuracyMetrics {
  overall: number
  person: number
  car: number
  animal: number
}

export interface StreamInfo {
  boundingBoxes: BoundingBox[]
  fps: number
  resolution: string
  bitrate: number
  latency: number
  isOnline: boolean
  accuracy: AccuracyMetrics
}

export type TaskStatus = "pending" | "in-progress" | "completed" | "failed"

export interface Task {
  id: string
  name: string
  description: string
  cameraId: string
  targetObject: string
  createdAt: string
  status: TaskStatus
  isManual: boolean
}

export interface TaskRecord {
  id: string
  taskId: string
  timestamp: string
  cameraId: string
  taskName: string
  details: string
  status: TaskStatus
  error?: string
}
