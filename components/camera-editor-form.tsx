"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useCameraStore } from "@/lib/stores/camera-store";
import type { Camera } from "@/lib/types";

// Zod schema
const formSchema = z.object({
  name: z.string().min(2, { message: "Camera name must be at least 2 characters." }),
  ipAddress: z
    .string()
    .min(7, { message: "Please enter a valid IP address." })
    .regex(/^(\d{1,3}\.){3}\d{1,3}(:\d+)?$/, {
      message: "Please enter a valid IP address format (e.g., 192.168.1.100 or 192.168.1.100:8080).",
    }),
  streamUrl: z.string().url({ message: "Please enter a valid URL." }),
});

export function CameraEditorForm() {
  const { cameras, addCamera, updateCamera, removeCamera } = useCameraStore();
  const [editingCamera, setEditingCamera] = useState<Camera | null>(null);

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: { name: "", ipAddress: "", streamUrl: "" },
  });

  // Xử lý submit form (Update hoặc Add)
  async function onSubmit(values: z.infer<typeof formSchema>) {
    try {
      const cameraData = {
        id: editingCamera ? editingCamera.id : undefined,
        name: values.name,
        ipAddress: values.ipAddress,
        rtsp_url: values.streamUrl,
      };

      // Gửi yêu cầu PUT (update) hoặc POST (add) đến backend
      const method = editingCamera ? "PUT" : "POST";
      const response = await fetch("http://localhost:7000/api/cameras", {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(cameraData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to save camera");
      }

      const result = await response.json();
      console.log(result.message);

      // Cập nhật state trong store
      if (editingCamera) {
        updateCamera({
          ...editingCamera,
          name: values.name,
          ipAddress: values.ipAddress,
          rtsp_url: values.streamUrl,
        });
      } else {
        addCamera({
          id: result.camera.id,
          name: values.name,
          ipAddress: values.ipAddress,
          rtsp_url: values.streamUrl,
        });
      }

      form.reset();
      setEditingCamera(null);
    } catch (error) {
      // Xử lý error với type guard
      const message = error instanceof Error ? error.message : "Failed to save camera.";
      console.error("Error submitting form:", error);
      form.setError("root", { message });
    }
  }

  // Xử lý xóa camera
  async function handleRemoveCamera(cameraId: string) {
    // Hiển thị thông báo xác nhận
    const confirmed = window.confirm("Are you sure you want to delete this camera?");
    if (!confirmed) return;

    try {
      // Gửi yêu cầu DELETE đến backend
      const response = await fetch(`http://localhost:7000/api/cameras/${cameraId}`, {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to delete camera");
      }

      // Xóa camera khỏi store
      removeCamera(cameraId);
      console.log(`Camera ${cameraId} deleted`);
    } catch (error) {
      // Xử lý error với type guard
      const message = error instanceof Error ? error.message : "Failed to delete camera.";
      console.error("Error deleting camera:", error);
      alert(message);
    }
  }

  function handleEdit(camera: Camera) {
    setEditingCamera(camera);
    form.reset({
      name: camera.name,
      ipAddress: camera.ipAddress || "",
      streamUrl: camera.rtsp_url,
    });
  }

  function handleCancel() {
    setEditingCamera(null);
    form.reset();
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>{editingCamera ? "Edit Camera" : "Add New Camera"}</CardTitle>
        </CardHeader>
        <CardContent>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
              <FormField
                control={form.control}
                name="name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Camera Name</FormLabel>
                    <FormControl>
                      <Input placeholder="Living Room Camera" {...field} />
                    </FormControl>
                    <FormDescription>A descriptive name for your camera</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="ipAddress"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>IP Address</FormLabel>
                    <FormControl>
                      <Input placeholder="192.168.1.100" {...field} />
                    </FormControl>
                    <FormDescription>The IP address of your camera (with optional port)</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="streamUrl"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Stream URL</FormLabel>
                    <FormControl>
                      <Input placeholder="rtsp://example.com/stream" {...field} />
                    </FormControl>
                    <FormDescription>The RTSP, HLS, or WebRTC URL for your camera stream</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
              {form.formState.errors.root && (
                <p className="text-red-500 text-sm">{form.formState.errors.root.message}</p>
              )}
              <div className="flex gap-2">
                <Button type="submit">{editingCamera ? "Update Camera" : "Add Camera"}</Button>
                {editingCamera && (
                  <Button type="button" variant="outline" onClick={handleCancel}>
                    Cancel
                  </Button>
                )}
              </div>
            </form>
          </Form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Camera List</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {cameras.length === 0 ? (
              <p className="text-muted-foreground">No cameras added yet</p>
            ) : (
              cameras.map((camera) => (
                <div key={camera.id} className="flex items-center justify-between rounded-md border p-3">
                  <div>
                    <div className="font-medium">{camera.name}</div>
                    <div className="text-sm text-muted-foreground">{camera.ipAddress}</div>
                    <div className="text-sm text-muted-foreground">{camera.rtsp_url}</div>
                  </div>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" onClick={() => handleEdit(camera)}>
                      Edit
                    </Button>
                    <Button variant="destructive" size="sm" onClick={() => handleRemoveCamera(camera.id)}>
                      Remove
                    </Button>
                  </div>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}