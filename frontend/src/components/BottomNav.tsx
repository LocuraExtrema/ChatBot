import { Link, useLocation } from "@tanstack/react-router";
import { Icon } from "./Icon";
import { useLti } from "@/lib/lti-context";

const baseItems = [
  { to: "/", label: "Inicio", icon: "home" },
  { to: "/chatbot", label: "Chatbot", icon: "chat_bubble" },
  { to: "/panel", label: "Panel", icon: "monitoring" },
] as const;

export function BottomNav() {
  const { pathname } = useLocation();
  const { user } = useLti();
  const items =
    user.role === "Instructor"
      ? [...baseItems, { to: "/profesor", label: "Auditoría", icon: "reviews" } as const]
      : baseItems;

  return (
    <nav className="md:hidden fixed bottom-0 left-0 w-full z-50 bg-surface-container-lowest flex justify-around items-center px-2 py-2 rounded-t-2xl shadow-[0_-8px_24px_-12px_rgba(0,18,67,0.12)] border-t border-outline-variant/30">
      {items.map((item) => {
        const active = pathname === item.to;
        return (
          <Link
            key={item.to}
            to={item.to}
            className={
              "flex items-center justify-center gap-1.5 transition-all active:scale-90 " +
              (active
                ? "bg-secondary-container text-on-secondary-container rounded-full px-4 py-2"
                : "flex-col text-on-surface-variant px-3 py-1 hover:text-secondary")
            }
          >
            <Icon name={item.icon} filled={active} />
            <span className="text-[12px] font-semibold tracking-wide">
              {item.label}
            </span>
          </Link>
        );
      })}
    </nav>
  );
}
