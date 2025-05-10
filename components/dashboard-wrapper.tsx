"use client"

import React, { useEffect } from 'react';
import { useTaskStore } from "@/lib/stores/task-store";
import { useUIStore } from "@/lib/stores/ui-store";

interface DashboardWrapperProps {
  children: React.ReactNode;
}

export function DashboardWrapper({ children }: DashboardWrapperProps) {
  const { isAutoMode } = useTaskStore();
  const { dashboardBgColor, setDashboardBgColor } = useUIStore();
  
  // Màu được yêu cầu là 0x7a2c8b9f
  // Format: #RGB + alpha
  // Ở đây 7a2c8b là mã màu RGB, 9f là alpha (opacity ~62%)
  
  useEffect(() => {
    if (isAutoMode) {
      setDashboardBgColor("bg-[#7a2c8b]");
    } else {
      setDashboardBgColor("bg-black");
    }
  }, [isAutoMode, setDashboardBgColor]);

  return (
    <div style={{ 
      backgroundColor: isAutoMode ? 'rgba(122, 44, 139, 0.62)' : 'black', 
      transition: 'background-color 0.3s ease' 
    }} 
    className="rounded-lg p-4">
      {children}
    </div>
  );
} 