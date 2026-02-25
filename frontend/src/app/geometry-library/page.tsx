import { GeometryLibrary } from "@/components/geometry/GeometryLibrary";

export default function GeometryLibraryPage() {
  return (
    <main className="min-h-screen bg-muted/30 p-4 md:p-6">
      <div className="mx-auto max-w-[1800px] rounded-2xl border bg-background p-4 md:p-6">
        <GeometryLibrary />
      </div>
    </main>
  );
}
