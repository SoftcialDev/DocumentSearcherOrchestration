import React, {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  ReactNode,
} from "react";

type Variant = "success" | "error" | "info" | "warning";

interface AlertInput {
  message: string;
  variant?: Variant;   // default 'info'
  duration?: number;   // ms, default 4 000
}

interface AlertItem {
  id: string;
  message: string;
  variant: Variant;   
  duration: number;
}

interface AlertContextShape {
  push: (payload: AlertInput) => void;
}

const AlertContext = createContext<AlertContextShape | null>(null);

/* ---------- provider ---------- */
export const AlertsProvider = ({ children }: { children: ReactNode }) => {
    const [alerts, setAlerts] = useState<AlertItem[]>([]);

    const push = useCallback((payload: AlertInput) => {
        setAlerts((list) => [
        ...list,
        {
            id: crypto.randomUUID(),
            ...payload,
            variant: payload.variant ?? "info",
            duration: payload.duration ?? 4000,
        },
        ]);
    }, []);

    const remove = (id: string) =>
        setAlerts((list) => list.filter((a) => a.id !== id));

    return (
        <AlertContext.Provider value={{ push }}>
        {children}

        {/* alert container */}
        <div className="fixed bottom-4 right-4 flex flex-col-reverse gap-2 items-end z-50">
            {alerts.map((a) => (
                <Alert key={a.id} {...a} onDone={() => remove(a.id)} />
            ))}
        </div>
        </AlertContext.Provider>
    );
    };

/* ---------- hook ---------- */
export const useAlerts = () => {
    const ctx = useContext(AlertContext);
    if (!ctx) throw new Error("useAlerts must be inside <AlertsProvider>");
    return ctx;
    };

    /* ---------- single alert ---------- */
    const colors: Record<Variant, string> = {
        success: "bg-green-600",
        error: "bg-red-600",
        info: "bg-blue-600",
        warning: "bg-yellow-600",
    };

    const Alert = ({id, message, variant, duration, onDone, }: AlertItem & { onDone: () => void }) => {
        const [show, setShow] = useState(true);

        /* auto-dismiss */
        useEffect(() => {
            const t = setTimeout(() => setShow(false), duration);
            return () => clearTimeout(t);
        }, [duration]);

        /* wait for fade-out then remove from context */
        useEffect(() => {
            if (!show) {
            const t = setTimeout(onDone, 200); // keep in DOM for fade animation
            return () => clearTimeout(t);
            }
        }, [show, onDone]);

        return (
            <div
            className={`text-white px-4 py-2 rounded-lg shadow transition-opacity duration-200 ${
                show ? "opacity-100" : "opacity-0"
            } ${colors[variant]}`}
            >
            <div className="flex items-start gap-3">
                <span className="flex-1">{message}</span>
                <button onClick={() => setShow(false)} aria-label="Close">
                ✕
                </button>
            </div>
            </div>
        );
    };
