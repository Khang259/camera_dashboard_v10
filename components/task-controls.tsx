"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
  DialogClose,
} from "@/components/ui/dialog"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { useTaskStore } from "@/lib/stores/task-store"
import { useCameraStore } from "@/lib/stores/camera-store"
import { PlayCircle } from "lucide-react"
import { HoloSwitch } from "@/components/ui/holo-switch"

export function TaskControls() {
  const { isAutoMode, setAutoMode, addTask, addTaskRecord } = useTaskStore()
  const { cameras } = useCameraStore()
  const [selectedCamera, setSelectedCamera] = useState("")
  const [taskName, setTaskName] = useState("")
  const [taskDescription, setTaskDescription] = useState("")
  const [targetObject, setTargetObject] = useState("Box")

  const handleAutoModeToggle = (checked: boolean) => {
    setAutoMode(checked)
  }

  return (
    <div className="flex items-center gap-4">
      <div className="flex items-center space-x-2">
        <HoloSwitch id="auto-mode" checked={isAutoMode} onCheckedChange={handleAutoModeToggle} />
        <Label htmlFor="auto-mode">{isAutoMode ? "Automatic Mode" : "Manual Mode"}</Label>
      </div>
    </div>
  )
}
