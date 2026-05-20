import { Link, useLocation } from "@tanstack/react-router";
import { Icon } from "./Icon";
import { useLti } from "@/lib/lti-context";

const baseNav = [
  { to: "/", label: "Inicio" },
  { to: "/chatbot", label: "Chatbot" },
  { to: "/panel", label: "Panel" },
] as const;

export function AppHeader({ anonymousId }: { anonymousId?: string }) {
  const { pathname } = useLocation();
  const { user, setUser } = useLti();
  const isInstructor = user.role === "Instructor";

  const navItems = isInstructor
    ? [...baseNav, { to: "/profesor", label: "Auditoría Docente" } as const]
    : baseNav;

  const toggleRole = () => {
    if (isInstructor) {
      setUser({
        ...user,
        role: "Learner",
        email: "alumno225@unraf.edu.ar",
      });
    } else {
      setUser({
        ...user,
        role: "Instructor",
        email: "profesor@unraf.edu.ar",
      });
    }
  };

  return (
    <header className="bg-surface/90 backdrop-blur fixed top-0 left-0 w-full z-50 flex justify-between items-center h-16 px-4 md:px-20 border-b border-outline-variant/40">
      <Link to="/" className="flex items-center gap-3">
        <Icon name="school" filled className="text-primary" />
        <span className="text-[20px] font-bold text-primary tracking-tight">
          Faro UNRaf
        </span>
      </Link>

      <div className="flex items-center gap-2 md:gap-4">
        <nav className="hidden md:flex gap-1">
          {navItems.map((item) => {
            const active = pathname === item.to;
            const highlight = item.to === "/profesor";
            return (
              <Link
                key={item.to}
                to={item.to}
                className={
                  "px-3 py-2 text-[14px] font-semibold tracking-wide rounded-lg transition-colors inline-flex items-center gap-1.5 " +
                  (active
                    ? "text-primary border-b-2 border-primary rounded-none"
                    : highlight
                      ? "text-secondary hover:bg-secondary-container/60"
                      : "text-on-surface-variant hover:bg-surface-container")
                }
              >
                {highlight && <Icon name="reviews" filled className="text-[18px]" />}
                {item.label}
              </Link>
            );
          })}
        </nav>

        <button
          onClick={toggleRole}
          title="Cambiar rol simulado (LTI)"
          className={
            "hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[12px] font-bold uppercase tracking-wider border transition-colors " +
            (isInstructor
              ? "bg-secondary text-on-secondary border-secondary"
              : "bg-surface-container text-on-surface-variant border-outline-variant hover:border-secondary")
          }
        >
          <Icon name="switch_account" className="text-[16px]" />
          {user.role}
        </button>

        {anonymousId && (
          <div className="hidden md:flex items-center gap-1.5 px-3 py-1 bg-surface-container-high rounded-full">
            <Icon name="fingerprint" filled className="text-[18px] text-primary" />
            <span className="text-[13px] font-semibold text-on-surface">
              #{anonymousId}
            </span>
          </div>
        )}

        <button
          aria-label="Cuenta"
          className="text-primary p-2 rounded-full hover:bg-surface-container transition-colors"
        >
          <Icon name="account_circle" />
        </button>
      </div>
    </header>
  );
}
