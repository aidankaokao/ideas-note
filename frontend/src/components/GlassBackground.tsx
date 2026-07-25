/** 漂浮光暈背景（Aurora Glass §3.2），掛最外層。 */
export function GlassBackground() {
  return (
    <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
      <div
        className="absolute -left-24 -top-24 h-[42rem] w-[42rem] rounded-full blur-3xl animate-blob"
        style={{ background: "hsl(var(--glow-1) / 0.40)" }}
      />
      <div
        className="absolute -top-16 right-[-8rem] h-[38rem] w-[38rem] rounded-full blur-3xl animate-blob"
        style={{ background: "hsl(var(--glow-2) / 0.40)", animationDelay: "6s" }}
      />
      <div
        className="absolute bottom-[-10rem] left-1/3 h-[36rem] w-[36rem] rounded-full blur-3xl animate-blob"
        style={{ background: "hsl(var(--glow-3) / 0.40)", animationDelay: "12s" }}
      />
    </div>
  );
}
