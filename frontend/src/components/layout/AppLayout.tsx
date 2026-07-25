import { Outlet, useLocation } from "react-router-dom";

import { GlassBackground } from "@/components/GlassBackground";
import { Header } from "@/components/layout/Header";
import { MobileNav } from "@/components/layout/MobileNav";
import { Sidebar } from "@/components/layout/Sidebar";
import { cn } from "@/lib/utils";

/** 版面結構（Aurora Glass §7）：外層不捲動、只有 main 捲動；手機底部導覽預留空間。
 * 主頁（導師）例外：main 不捲動、由對話訊息區內部捲動，輸入框固定在底部。 */
export function AppLayout() {
  const isAssistant = useLocation().pathname === "/";

  return (
    <>
      <GlassBackground />
      <div className="flex h-dvh overflow-hidden">
        <Sidebar />
        <div className="flex min-w-0 flex-1 flex-col">
          <Header />
          <main
            className={cn(
              "flex-1 nice-scroll",
              isAssistant
                ? "overflow-hidden p-4 pb-20 md:p-6 md:pb-6"
                : "overflow-auto p-4 pb-24 md:p-6 md:pb-6"
            )}
          >
            <div className={cn("mx-auto max-w-3xl", isAssistant ? "h-full" : "space-y-6")}>
              <Outlet />
            </div>
          </main>
        </div>
      </div>
      <MobileNav />
    </>
  );
}
