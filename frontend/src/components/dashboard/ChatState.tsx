import {
  Dispatch,
  FormEvent,
  SetStateAction,
  useEffect,
  useState,
} from "react";
import { Message, RawTasks, ScheduleItem } from "@/types";
import { HitlPayload, PrioritizerTask, ResumeData } from "@/hooks/useChat";
import { ChatMessage } from "./ChatMessage";
import { TypingIndicator } from "./TypingIndicator";
import { ChatInput } from "./ChatInput";
import { CounselorApproveBar } from "./CounselorApproveBar";
import { ResultState } from "./ResultState";
import { X, ChevronRight, Folder } from "lucide-react";

interface ChatStateProps {
  messages: Message[];
  isTyping: boolean;
  inputValue: string;
  setInputValue: (val: string) => void;
  handleSend: (
    e: FormEvent | null,
    resumeData?: ResumeData,
    questionnaireData?: {
      energyLevel: number;
      mood: number;
      availableTime: string;
    },
  ) => void;
  messagesEndRef: React.RefObject<HTMLDivElement | null>;
  hitlPayload: HitlPayload | null;
  scheduleItems: ScheduleItem[];
  setScheduleItems: Dispatch<SetStateAction<ScheduleItem[]>>;
  isEditingSchedule: boolean;
  setIsEditingSchedule: Dispatch<SetStateAction<boolean>>;
  setIsResult: Dispatch<SetStateAction<boolean>>;
  setIsAnalyzing: Dispatch<SetStateAction<boolean>>;
  prioritizerTasks: PrioritizerTask[] | undefined;
  onApprove: () => {};
}

export function ChatState({
  messages,
  isTyping,
  inputValue,
  setInputValue,
  handleSend,
  messagesEndRef,
  hitlPayload,
  scheduleItems,
  setScheduleItems,
  isEditingSchedule,
  setIsEditingSchedule,
  setIsResult,
  setIsAnalyzing,
  prioritizerTasks,
  onApprove,
}: ChatStateProps) {
  const [isOpenRawTasks, setIsOpenRawTasks] = useState(false);

  const [rawTasks, setRawTasks] = useState<RawTasks[] | null>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });

    try {
      const storedTasks = sessionStorage.getItem("raw_tasks");

      if (storedTasks) {
        setRawTasks(JSON.parse(storedTasks));
      }
    } catch (error) {
      console.error("Failed to parse raw_tasks:", error);
      setRawTasks(null);
    }
  }, [messages, isTyping]);

  const isAwaitingApproval =
    (messages.length > 0 &&
      messages[messages.length - 1].role === "system" &&
      hitlPayload?.type === "counselor_chat") ||
    "counselor_review";

  const handleInputSubmit = (e: FormEvent) => {
    if (isAwaitingApproval) {
      handleSend(e, { approved: false, additional_context: inputValue });
    } else {
      handleSend(e);
    }
  };

  return (
    <main className="flex-1 flex h-full bg-[#FFFFFF] overflow-hidden">
      <div
        className={`flex flex-col h-full transition-all duration-300 ease-in-out ${
          isOpenRawTasks ? "w-1/2" : "w-full"
        }`}
      >
        <header className="relative flex justify-end p-5">
          <button
            className={`flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-full border transition-colors ${
              isOpenRawTasks
                ? "bg-black text-white border-black"
                : "text-gray-500 border-gray-200 hover:border-gray-400 hover:text-black"
            }`}
            onClick={() => setIsOpenRawTasks(!isOpenRawTasks)}
          >
            <Folder />
            raw_tasks
            <ChevronRight
              size={12}
              className={`transition-transform duration-200 ${isOpenRawTasks ? "rotate-180" : ""}`}
            />
          </button>
          <div className="absolute left-0 right-0 -bottom-4 h-4 bg-linear-to-b from-white to-transparent pointer-events-none" />
        </header>

        <div className="flex-1 overflow-y-auto px-6 pt-10 pb-6">
          <div className="max-w-4xl mx-auto flex flex-col gap-8">
            {messages.map((msg, index) => {
              const isLastIndex = index === messages.length - 1;

              return (
                <div key={index} className="flex flex-col gap-4">
                  {msg.role !== "system" && <ChatMessage message={msg} />}

                  {msg.role === "system" &&
                    (!isTyping || !isLastIndex) &&
                    (hitlPayload?.type === "counselor_chat" ||
hitlPayload?.type === "counselor_review" && isLastIndex ? (
                      <ChatMessage message={msg} payload={hitlPayload} />
                    ) : (
                      <ChatMessage message={msg} />
                    ))}
                </div>
              );
            })}
            {hitlPayload?.type === "task_review" && (
              <ResultState
                scheduleItems={scheduleItems}
                setScheduleItems={setScheduleItems}
                isEditingSchedule={isEditingSchedule}
                setIsEditingSchedule={setIsEditingSchedule}
                setIsResult={setIsResult}
                setIsAnalyzing={setIsAnalyzing}
                prioritizerTasks={hitlPayload.tasks}
                onApprove={onApprove}
              />
            )}
            {isTyping && <TypingIndicator />}
            <div ref={messagesEndRef} />
          </div>
        </div>

        <ChatInput
          value={inputValue}
          onChange={setInputValue}
          onSubmit={handleInputSubmit}
          disabled={isTyping}
          placeholder={
            isAwaitingApproval
              ? "Ketik di sini untuk menambah cerita..."
              : "Type your message..."
          }
          counselorBar={
            ( hitlPayload?.type === "counselor_review") && (
              <CounselorApproveBar
                payload={hitlPayload}
                onApprove={(editedDraft) =>
                  handleSend(null, {
                    approved: true,
                    additional_context: editedDraft ?? null,
                  })
                }
                onReject={() =>
                  handleSend(null, {
                    approved: false,
                    additional_context: null,
                  })
                }
              />
            )
          }
        />
      </div>

      {/* ── Raw Tasks Sidebar Panel ── */}
      <div
        className={`flex flex-col h-full border-l border-gray-100 bg-[#F9F9F9] transition-all duration-300 ease-in-out overflow-hidden ${
          isOpenRawTasks
            ? "w-1/2 opacity-100"
            : "w-0 opacity-0 pointer-events-none"
        }`}
      >
        {/* Panel Header */}
        <div className="flex items-center justify-between px-6 py-5 border-b border-gray-100">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-black" />
            <span className="text-sm font-semibold text-black tracking-tight">
              Raw Tasks
            </span>
          </div>
          <button
            onClick={() => setIsOpenRawTasks(false)}
            className="p-1 rounded-md text-gray-400 hover:text-black hover:bg-gray-100 transition-colors"
          >
            <X size={14} />
          </button>
        </div>

        {/* Panel Content */}
        <div className="flex-1 overflow-y-auto px-6 py-5 font-mono text-xs">
          {rawTasks && rawTasks.length > 0 ? (
            <div className="flex flex-col gap-3">
              {rawTasks.map((task, i) => (
                <div
                  key={i}
                  className="rounded-lg border border-gray-200 bg-white p-4 flex flex-col gap-2"
                >
                  {/* Task number badge */}
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">
                      Task {i + 1}
                    </span>
                  </div>
                  {/* Render each key-value pair */}
                  {Object.entries(task).map(([key, value]) => (
                    <div key={key} className="flex flex-col gap-0.5">
                      <span className="text-[10px] text-gray-400 uppercase tracking-wider">
                        {key}
                      </span>
                      <span className="text-gray-800 wrap-break-word">
                        {typeof value === "object"
                          ? JSON.stringify(value, null, 2)
                          : String(value)}
                      </span>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-full gap-3 text-gray-300">
              <div className="text-5xl">∅</div>
              <p className="text-xs">No raw tasks yet</p>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
