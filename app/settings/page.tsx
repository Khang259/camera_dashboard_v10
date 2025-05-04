import { CameraEditorForm } from "@/components/camera-editor-form"

export default function SettingsPage() {
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Camera Settings</h1>
      <CameraEditorForm />
    </div>
  )
}
