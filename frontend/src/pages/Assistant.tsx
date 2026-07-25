import { useEffect } from "react";

import { MentorChat } from "@/components/MentorChat";
import { usePageHeader } from "@/stores/pageHeader";

export default function AssistantPage() {
  useEffect(() => {
    usePageHeader.getState().set("靈感導師", "記錄、延伸、整理，一句話搞定");
  }, []);

  // fill：訊息區內部捲動、輸入框固定在底部（AppLayout 對主頁停用 main 捲動）
  return <MentorChat fill />;
}
