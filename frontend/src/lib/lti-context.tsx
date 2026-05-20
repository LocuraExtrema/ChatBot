import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";

export type LtiRole = "Learner" | "Instructor" | "Maestro";

export type LtiUser = {
  user_id: string;
  course_id: string;
  role: LtiRole;
  email: string;
};

export type ChatMessage = {
  id: string;
  role: "user" | "ai";
  text: string;
  /** When role==='ai', this links back to the user pregunta it answered */
  inReplyTo?: string;
};

type LtiContextValue = {
  user: LtiUser;
  setUser: (u: LtiUser) => void;
  messages: ChatMessage[];
  addMessage: (m: Omit<ChatMessage, "id">) => ChatMessage;
  resetMessages: () => void;
};

// Simulated LTI launch payload
const DEFAULT_LTI_USER: LtiUser = {
  user_id: "alumno-225",
  course_id: "unraf-intro-2026",
  role: "Learner",
  email: "alumno225@unraf.edu.ar",
};

const WELCOME: ChatMessage = {
  id: "welcome",
  role: "ai",
  text: "Hola, soy Faro. Estoy aquí para orientarte en tu trayectoria académica. ¿En qué puedo ayudarte hoy?",
};

const LtiContext = createContext<LtiContextValue | null>(null);

function uid() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

export function LtiProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<LtiUser>(DEFAULT_LTI_USER);
  const [messages, setMessages] = useState<ChatMessage[]>([WELCOME]);

  const addMessage = useCallback((m: Omit<ChatMessage, "id">): ChatMessage => {
    const msg: ChatMessage = { ...m, id: uid() };
    setMessages((prev) => [...prev, msg]);
    return msg;
  }, []);

  const resetMessages = useCallback(() => setMessages([WELCOME]), []);

  const value = useMemo(
    () => ({ user, setUser, messages, addMessage, resetMessages }),
    [user, messages, addMessage, resetMessages],
  );

  return <LtiContext.Provider value={value}>{children}</LtiContext.Provider>;
}

export function useLti(): LtiContextValue {
  const ctx = useContext(LtiContext);
  if (!ctx) throw new Error("useLti must be used within <LtiProvider>");
  return ctx;
}
