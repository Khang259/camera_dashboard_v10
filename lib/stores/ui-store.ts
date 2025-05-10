import { create } from "zustand"
import { persist } from "zustand/middleware"

interface UIState {
  dashboardBgColor: string;
  setDashboardBgColor: (color: string) => void;
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      dashboardBgColor: "bg-black",
      
      setDashboardBgColor: (color) => {
        set({ dashboardBgColor: color })
      },
    }),
    {
      name: "ui-storage",
    }
  )
) 