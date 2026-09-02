import AmericanSurfaceAtlas from "@/components/research/AmericanSurfaceAtlas";


export default function SurfaceAtlasPage() {
  return (
    <main
      className="ql-page"
      style={{
        display: "grid",
        gap: 18,
      }}
    >
      <AmericanSurfaceAtlas />
    </main>
  );
}