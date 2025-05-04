"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Switch } from "@/components/ui/switch"
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

  const handleManualTask = () => {
    if (!selectedCamera || !taskName) return

    const taskId = addTask({
      name: taskName,
      description: taskDescription,
      cameraId: selectedCamera,
      targetObject,
      isManual: true,
    })

    // Add a record for this manual task
    addTaskRecord({
      taskId,
      cameraId: selectedCamera,
      taskName,
      details: `Manual task initiated: ${taskDescription}`,
      status: "pending",
    })

    // Reset form
    setTaskName("")
    setTaskDescription("")
    setSelectedCamera("")
  }

  return (
    <div className="flex items-center gap-4">
      <div className="flex items-center space-x-2">
        <Switch id="auto-mode" checked={isAutoMode} onCheckedChange={handleAutoModeToggle} />
        <Label htmlFor="auto-mode">{isAutoMode ? "Automatic Mode" : "Manual Mode"}</Label>
      </div>

      <Dialog>
        <DialogTrigger asChild>
          <Button>
            <PlayCircle className="mr-2 h-4 w-4" />
            Run Task
          </Button>
        </DialogTrigger>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Create Manual Task</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="camera" className="text-right">
                Camera
              </Label>
              <Select value={selectedCamera} onValueChange={setSelectedCamera}>
                <SelectTrigger className="col-span-3">
                  <SelectValue placeholder="Select camera" />
                </SelectTrigger>
                <SelectContent>
                  {cameras.map((camera) => (
                    <SelectItem key={camera.id} value={camera.id}>
                      {camera.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="name" className="text-right">
                Task Name
              </Label>
              <Input id="name" value={taskName} onChange={(e) => setTaskName(e.target.value)} className="col-span-3" />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="target" className="text-right">
                Target Object
              </Label>
              <Select value={targetObject} onValueChange={setTargetObject}>
                <SelectTrigger className="col-span-3">
                  <SelectValue placeholder="Select target" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Box">Box</SelectItem>
                  <SelectItem value="Person">Person</SelectItem>
                  <SelectItem value="Vehicle">Vehicle</SelectItem>
                  <SelectItem value="Animal">Animal</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="description" className="text-right">
                Description
              </Label>
              <Textarea
                id="description"
                value={taskDescription}
                onChange={(e) => setTaskDescription(e.target.value)}
                className="col-span-3"
              />
            </div>
          </div>
          <DialogFooter>
            <DialogClose asChild>
              <Button onClick={handleManualTask}>Run Task</Button>
            </DialogClose>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
