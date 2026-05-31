"use client";

import { AppShell } from "@/components/AppShell";
import { CameraViewport } from "@/components/CameraViewport";
import { ClassificationPanel } from "@/components/ClassificationPanel";
import { CameraControls } from "@/components/CameraControls";
import { DetectionControls } from "@/components/DetectionControls";
import { ModelControls } from "@/components/ModelControls";
import { PickupTelemetry } from "@/components/PickupTelemetry";

export default function HomePage() {
  return (
    <AppShell>
      <div className="grid min-h-0 grid-cols-1 gap-gutter lg:grid-cols-12">
        <div className="lg:col-span-8">
          <CameraViewport />
          <div className="mt-gutter grid grid-cols-1 gap-gutter md:grid-cols-2">
            <ClassificationPanel />
            <PickupTelemetry />
          </div>
        </div>
        <div className="lg:col-span-4">
          <CameraControls />
          <ModelControls />
          <DetectionControls />
        </div>
      </div>
    </AppShell>
  );
}
