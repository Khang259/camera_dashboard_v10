// app/loading.tsx
"use client";
import { Progress } from "@/components/ui/progress";

export default function Loading() {
  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-background/80">
      <div className="w-1/3">
        <Progress value={70} />
        <div className="mt-4 text-center text-primary font-semibold animate-pulse">
          Đang tải dữ liệu...
        </div>
      </div>
    </div>
  );
}