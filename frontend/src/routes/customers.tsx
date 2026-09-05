import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { ApplicationShell } from "@/components/shell/ApplicationShell";
import { api, Customer, CustomerDetail } from "@/lib/api";
import {
  ArrowLeft,
  Users,
  Search,
  Filter,
  ArrowUpDown,
  TrendingUp,
  AlertTriangle,
  ShoppingBag,
  Clock,
  X,
} from "lucide-react";

export const Route = createFileRoute("/customers")({
  head: () => ({
    meta: [
      { title: "CUSTOMERS — PayPilot" },
      { name: "description", content: "Customer intelligence and behavioral analytics." },
    ],
  }),
  component: CustomersView,
});

function CustomersView() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [selectedCustomerId, setSelectedCustomerId] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["customers", page, search],
    queryFn: () =>
      api.getCustomers({
        page,
        limit: 15,
        search: search || undefined,
      }),
  });

  const { data: selectedCustomer } = useQuery({
    queryKey: ["customer", selectedCustomerId],
    queryFn: () => (selectedCustomerId ? api.getCustomer(selectedCustomerId) : null),
    enabled: !!selectedCustomerId,
  });

  return (
    <ApplicationShell>
      <main className="min-h-screen pt-20 pb-16 px-8 max-w-[1600px] mx-auto">
        {/* Breadcrumb */}
        <div className="flex items-center justify-between border-b border-border/40 pb-6 mb-8">
          <div className="flex items-center gap-4">
            <Link
              to="/"
              search={{ state: "active" }}
              className="inline-flex items-center gap-2 font-mono text-[11px] tracking-[0.32em] text-muted-foreground transition-colors hover:text-foreground"
            >
              <ArrowLeft className="h-3.5 w-3.5" strokeWidth={1.5} />
              CORE
            </Link>
            <span className="text-border">/</span>
            <span className="font-mono text-[11px] tracking-[0.32em] text-accent">CUSTOMERS</span>
          </div>

          <span className="font-mono text-xs text-muted-foreground">
            {data ? `${data.total.toLocaleString()} Verified Accounts` : "Loading..."}
          </span>
        </div>

        {/* Title */}
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-8 gap-4">
          <div>
            <div className="font-mono text-[10px] tracking-[0.3em] text-muted-foreground mb-1">
              AUDIENCE INTELLIGENCE & LTV
            </div>
            <h1 className="font-display text-4xl md:text-5xl tracking-tight text-foreground">
              Customer Cohorts
            </h1>
          </div>

          {/* Search Bar */}
          <div className="relative min-w-[280px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search customer name or email..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              className="w-full pl-9 pr-3 py-2 bg-card/40 border border-border/60 rounded text-xs font-mono placeholder:text-muted-foreground/60 text-foreground focus:outline-none focus:border-accent"
            />
          </div>
        </div>

        {/* Customers Table */}
        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-32 space-y-4">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-accent border-t-transparent" />
            <p className="font-mono text-[11px] tracking-[0.3em] text-muted-foreground">
              LOADING CUSTOMER TELEMETRY...
            </p>
          </div>
        ) : !data || data.items.length === 0 ? (
          <div className="border border-border/40 bg-card/20 rounded-lg p-16 text-center">
            <p className="font-mono text-sm text-muted-foreground">No customers found.</p>
          </div>
        ) : (
          <div className="border border-border/60 bg-card/30 rounded-xl overflow-hidden backdrop-blur-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-secondary/40 border-b border-border/40 text-muted-foreground uppercase text-[10px] tracking-wider">
                  <tr>
                    <th className="py-3.5 px-4">Customer</th>
                    <th className="py-3.5 px-4">LTV (INR)</th>
                    <th className="py-3.5 px-4">Orders</th>
                    <th className="py-3.5 px-4">AOV</th>
                    <th className="py-3.5 px-4">Churn Risk</th>
                    <th className="py-3.5 px-4">Repeat Affinity</th>
                    <th className="py-3.5 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/20">
                  {data.items.map((cust) => (
                    <tr
                      key={cust.id}
                      onClick={() => setSelectedCustomerId(cust.id)}
                      className="hover:bg-secondary/30 transition-colors cursor-pointer"
                    >
                      <td className="py-3.5 px-4">
                        <div className="font-medium text-foreground">{cust.name}</div>
                        <div className="text-[10px] text-muted-foreground">{cust.email}</div>
                      </td>
                      <td className="py-3.5 px-4 font-semibold text-accent">
                        ₹{cust.lifetime_value.toLocaleString("en-IN")}
                      </td>
                      <td className="py-3.5 px-4 text-foreground">{cust.order_count}</td>
                      <td className="py-3.5 px-4 text-muted-foreground">
                        ₹{cust.average_order_value.toLocaleString("en-IN")}
                      </td>
                      <td className="py-3.5 px-4">
                        <span
                          className={`px-2 py-0.5 rounded text-[9px] ${
                            cust.churn_risk > 0.6
                              ? "bg-destructive/15 text-destructive border border-destructive/30"
                              : cust.churn_risk > 0.3
                              ? "bg-amber-500/15 text-amber-400 border border-amber-500/30"
                              : "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                          }`}
                        >
                          {(cust.churn_risk * 100).toFixed(0)}%
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-emerald-400">
                        {(cust.repeat_probability * 100).toFixed(0)}%
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedCustomerId(cust.id);
                          }}
                          className="px-2.5 py-1 rounded bg-secondary hover:bg-secondary/80 text-[10px] text-foreground transition-colors"
                        >
                          INSPECT
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls */}
            <div className="flex items-center justify-between p-4 border-t border-border/40 bg-secondary/10">
              <span className="text-[10px] text-muted-foreground">
                Showing {((page - 1) * 15) + 1} - {Math.min(page * 15, data.total)} of {data.total}
              </span>
              <div className="flex items-center gap-2">
                <button
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  className="px-3 py-1 bg-secondary rounded text-xs disabled:opacity-40 hover:bg-secondary/80"
                >
                  PREV
                </button>
                <span className="text-xs px-2 text-foreground font-semibold">{page}</span>
                <button
                  disabled={page * 15 >= data.total}
                  onClick={() => setPage((p) => p + 1)}
                  className="px-3 py-1 bg-secondary rounded text-xs disabled:opacity-40 hover:bg-secondary/80"
                >
                  NEXT
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Customer Detail Modal */}
        {selectedCustomer && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-md">
            <div className="relative w-full max-w-lg bg-card border border-border rounded-xl shadow-2xl p-6 space-y-6">
              <div className="flex items-center justify-between border-b border-border/40 pb-4">
                <div>
                  <span className="px-2 py-0.5 rounded text-[9px] font-mono uppercase bg-accent/15 text-accent border border-accent/30">
                    {selectedCustomer.segment || "Active Customer"}
                  </span>
                  <h3 className="font-display text-2xl text-foreground mt-1">{selectedCustomer.name}</h3>
                  <p className="font-mono text-xs text-muted-foreground">{selectedCustomer.email}</p>
                </div>
                <button
                  onClick={() => setSelectedCustomerId(null)}
                  className="p-1.5 text-muted-foreground hover:text-foreground rounded border border-border/40"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>

              <div className="grid grid-cols-2 gap-3 font-mono text-xs">
                <div className="p-3 bg-secondary/30 rounded border border-border/30">
                  <span className="text-[9px] text-muted-foreground block">LIFETIME VALUE</span>
                  <span className="text-lg text-accent font-semibold">
                    ₹{selectedCustomer.lifetime_value.toLocaleString("en-IN")}
                  </span>
                </div>
                <div className="p-3 bg-secondary/30 rounded border border-border/30">
                  <span className="text-[9px] text-muted-foreground block">TOTAL ORDERS</span>
                  <span className="text-lg text-foreground font-semibold">{selectedCustomer.order_count}</span>
                </div>
                <div className="p-3 bg-secondary/30 rounded border border-border/30">
                  <span className="text-[9px] text-muted-foreground block">AVG ORDER VALUE</span>
                  <span className="text-lg text-foreground font-semibold">
                    ₹{selectedCustomer.average_order_value.toLocaleString("en-IN")}
                  </span>
                </div>
                <div className="p-3 bg-secondary/30 rounded border border-border/30">
                  <span className="text-[9px] text-muted-foreground block">CHURN RISK SCORE</span>
                  <span className="text-lg text-amber-400 font-semibold">
                    {(selectedCustomer.churn_risk * 100).toFixed(0)}%
                  </span>
                </div>
              </div>

              {selectedCustomer.recent_failed_payments !== undefined && selectedCustomer.recent_failed_payments > 0 && (
                <div className="p-3 bg-destructive/10 border border-destructive/30 rounded-lg text-xs font-mono text-destructive flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4" />
                  <span>{selectedCustomer.recent_failed_payments} recent failed checkout attempts detected.</span>
                </div>
              )}

              <div className="pt-2 flex justify-end">
                <Link
                  to="/opportunities"
                  className="px-4 py-2 bg-accent text-accent-foreground font-mono text-xs rounded font-medium hover:opacity-90"
                >
                  VIEW TARGETED OPPORTUNITIES
                </Link>
              </div>
            </div>
          </div>
        )}
      </main>
    </ApplicationShell>
  );
}
