import { create } from "zustand"
import { persist } from "zustand/middleware"
import type { Camera } from "@/lib/types"


//Nơi lưu trữ state của camera.
interface CameraState {
  cameras: Camera[] //Danh sách camera
  addCamera: (camera: Camera) => void //Add thêm camera mới
  updateCamera: (camera: Camera) => void //Thông tin camera
  removeCamera: (id: string) => void //Xoá camera
  setCameras: (cameras: Camera[]) => void //Cập nhật danh sách camera
}
// sử dụng persist middleware để lưu trữ vào localStorage.
// Khi thay đổi số lượng camera gọi hàm cameraState

export const useCameraStore = create<CameraState>()(
  persist(
    (set) => ({
      cameras: [],
      addCamera: (camera) => set((state) => ({ cameras: [...state.cameras, camera] })),
      updateCamera: (updatedCamera) =>
        set((state) => ({
          cameras: state.cameras.map((camera) => (camera.id === updatedCamera.id ? updatedCamera : camera)),
        })),
      removeCamera: (id) =>
        set((state) => ({
          cameras: state.cameras.filter((camera) => camera.id !== id),
        })),
      setCameras: (cameras) => set({ cameras }),
    }),
    {
      name: "camera-storage",
    },
  ),
)
