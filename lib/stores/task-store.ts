import { create } from "zustand"
import { persist } from "zustand/middleware"
import type { Task, TaskRecord, TaskStatus } from "@/lib/types"

interface TaskState {
  tasks: Task[]
  taskRecords: TaskRecord[]
  isAutoMode: boolean
  addTask: (task: Omit<Task, "id" | "createdAt" | "status">) => string
  updateTaskStatus: (id: string, status: TaskStatus) => void
  removeTask: (id: string) => void
  addTaskRecord: (record: Omit<TaskRecord, "id" | "timestamp">) => void
  setAutoMode: (isAuto: boolean) => void
  getTasksByDate: (startDate: Date, endDate: Date) => TaskRecord[]
}

// Generate a sample timestamp for demo data
const getRandomPastDate = (daysAgo: number) => {
  const date = new Date()
  date.setDate(date.getDate() - Math.floor(Math.random() * daysAgo))
  date.setHours(Math.floor(Math.random() * 24))
  date.setMinutes(Math.floor(Math.random() * 60))
  date.setSeconds(Math.floor(Math.random() * 60))
  return date.toISOString()
}

// Format date as dd/mm/yy h:m:s
export const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return `${date.getDate().toString().padStart(2, "0")}/${(date.getMonth() + 1).toString().padStart(2, "0")}/${date.getFullYear().toString().slice(2)} ${date.getHours()}:${date.getMinutes().toString().padStart(2, "0")}:${date.getSeconds().toString().padStart(2, "0")}`
}

// Sample data for demonstration
const sampleTasks: Task[] = [
  {
    id: "1",
    name: "Detect Cargo Box",
    description: "Detect if cargo box is present in loading area",
    cameraId: "1",
    targetObject: "Box",
    createdAt: new Date().toISOString(),
    status: "completed",
    isManual: false,
  },
  {
    id: "2",
    name: "Monitor Entrance",
    description: "Check for unauthorized personnel",
    cameraId: "2",
    targetObject: "Person",
    createdAt: new Date().toISOString(),
    status: "pending",
    isManual: true,
  },
]

// Generate sample task records for the past 30 days
const generateSampleTaskRecords = () => {
  const records: TaskRecord[] = []
  const statuses: TaskStatus[] = ["completed", "failed", "completed", "completed"]

  // Generate records for the past 30 days
  for (let i = 0; i < 100; i++) {
    const daysAgo = Math.floor(Math.random() * 30)
    const timestamp = getRandomPastDate(daysAgo)
    const status = statuses[Math.floor(Math.random() * statuses.length)]

    records.push({
      id: `record-${i}`,
      taskId: Math.random() > 0.5 ? "1" : "2",
      timestamp,
      cameraId: Math.random() > 0.5 ? "1" : "2",
      taskName: Math.random() > 0.5 ? "Detect Cargo Box" : "Monitor Entrance",
      details:
        Math.random() > 0.5 ? "Successfully detected cargo box in position" : "Checked for unauthorized personnel",
      status,
      error: status === "failed" ? "Object not found in frame" : undefined,
    })
  }

  return records
}

const sampleTaskRecords = generateSampleTaskRecords()

export const useTaskStore = create<TaskState>()(
  persist(
    (set, get) => ({
      tasks: sampleTasks,
      taskRecords: sampleTaskRecords,
      isAutoMode: true,

      addTask: (taskData) => {
        const id = Date.now().toString()
        const task: Task = {
          ...taskData,
          id,
          createdAt: new Date().toISOString(),
          status: "pending",
        }

        set((state) => ({
          tasks: [...state.tasks, task],
        }))

        return id
      },

      updateTaskStatus: (id, status) => {
        set((state) => ({
          tasks: state.tasks.map((task) => (task.id === id ? { ...task, status } : task)),
        }))
      },

      removeTask: (id) => {
        set((state) => ({
          tasks: state.tasks.filter((task) => task.id !== id),
        }))
      },

      addTaskRecord: (recordData) => {
        const record: TaskRecord = {
          ...recordData,
          id: Date.now().toString(),
          timestamp: new Date().toISOString(),
        }

        set((state) => ({
          taskRecords: [...state.taskRecords, record],
        }))
      },

      setAutoMode: (isAuto) => {
        set({ isAutoMode: isAuto })
      },

      getTasksByDate: (startDate, endDate) => {
        const { taskRecords } = get()
        return taskRecords.filter((record) => {
          const recordDate = new Date(record.timestamp)
          return recordDate >= startDate && recordDate <= endDate
        })
      },
    }),
    {
      name: "task-storage",
    },
  ),
)
