import { useState, useRef, useEffect } from "react";
import { useNavigate } from "@tanstack/react-router";
import { auth, DEMO_MERCHANTS, MerchantContext, UserProfile } from "@/lib/auth";
import {
  Building2,
  User,
  Settings,
  LogOut,
  Check,
  ChevronDown,
  Shield,
} from "lucide-react";

export function MerchantMenu() {
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);
  const [activeMerchant, setActiveMerchant] = useState<MerchantContext>(auth.getActiveMerchant());
  const [user, setUser] = useState<UserProfile>(auth.getUser());
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const update = () => {
      setActiveMerchant(auth.getActiveMerchant());
      setUser(auth.getUser());
    };
    return auth.subscribe(update);
  }, []);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [isOpen]);

  const handleSelectMerchant = (merchantId: string) => {
    auth.setActiveMerchant(merchantId);
    setIsOpen(false);
  };

  const handleSignOut = () => {
    auth.logout();
    setIsOpen(false);
    navigate({ to: "/login" });
  };

  return (
    <div className="relative" ref={menuRef}>
      {/* Trigger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-3 border-l border-border/60 pl-7 text-left group focus:outline-none"
      >
        <div className="text-right leading-tight">
          <div className="font-mono text-[10px] tracking-[0.22em] text-foreground group-hover:text-accent transition-colors flex items-center justify-end gap-1">
            <span>{user.name.toUpperCase()}</span>
            <ChevronDown className="h-3 w-3 text-muted-foreground group-hover:text-accent transition-transform" />
          </div>
          <div className="font-mono text-[9px] tracking-[0.22em] text-muted-foreground">
            {activeMerchant.name.toUpperCase()}
          </div>
        </div>
        <div className="flex h-7 w-7 items-center justify-center rounded-full border border-border/70 group-hover:border-accent/80 font-mono text-[10px] text-muted-foreground group-hover:text-foreground transition-all bg-secondary/40">
          {user.initials}
        </div>
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute right-0 mt-3 w-64 bg-card/95 border border-border rounded-xl shadow-2xl backdrop-blur-xl p-2 space-y-2 z-50 animate-fade-in">
          {/* User Info Header */}
          <div className="p-3 bg-secondary/40 rounded-lg border border-border/40 space-y-1">
            <div className="flex items-center gap-2">
              <User className="h-3.5 w-3.5 text-accent" />
              <span className="font-mono text-xs text-foreground font-semibold">{user.name}</span>
            </div>
            <div className="text-[10px] font-mono text-muted-foreground">{user.email}</div>
            <div className="text-[9px] font-mono text-accent/80 uppercase tracking-wider">{user.role}</div>
          </div>

          {/* Switch Merchant List */}
          <div className="space-y-1">
            <span className="font-mono text-[9px] text-muted-foreground uppercase tracking-wider px-2 block pt-1">
              DEMO MERCHANT CONTEXT
            </span>
            {DEMO_MERCHANTS.map((m) => {
              const isCurrent = m.id === activeMerchant.id;
              return (
                <button
                  key={m.id}
                  onClick={() => handleSelectMerchant(m.id)}
                  className={`w-full flex items-center justify-between px-2.5 py-2 rounded-lg text-xs font-mono text-left transition-colors ${
                    isCurrent
                      ? "bg-accent/15 text-accent font-medium border border-accent/30"
                      : "text-muted-foreground hover:bg-secondary/60 hover:text-foreground"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <Building2 className="h-3.5 w-3.5 opacity-70" />
                    <div>
                      <div className="text-foreground">{m.name}</div>
                      <div className="text-[9px] text-muted-foreground">{m.category} • {m.currency}</div>
                    </div>
                  </div>
                  {isCurrent && <Check className="h-3.5 w-3.5 text-accent" />}
                </button>
              );
            })}
          </div>

          {/* Quick Actions */}
          <div className="pt-2 border-t border-border/40 space-y-1">
            <button
              onClick={() => {
                setIsOpen(false);
                navigate({ to: "/admin" });
              }}
              className="w-full flex items-center gap-2 px-2.5 py-2 rounded-lg text-xs font-mono text-muted-foreground hover:bg-secondary/60 hover:text-foreground transition-colors text-left"
            >
              <Settings className="h-3.5 w-3.5" />
              <span>MERCHANT & SYSTEM ADMIN</span>
            </button>

            <button
              onClick={handleSignOut}
              className="w-full flex items-center gap-2 px-2.5 py-2 rounded-lg text-xs font-mono text-destructive hover:bg-destructive/10 transition-colors text-left"
            >
              <LogOut className="h-3.5 w-3.5" />
              <span>SIGN OUT</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
