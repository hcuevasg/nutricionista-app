import customtkinter as ctk
import database.db_manager as db
from datetime import date, datetime

try:
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    _MPL_OK = True
except ImportError:
    _MPL_OK = False

_C_PRIMARY    = "#4b7c60"
_C_TERRACOTTA = "#c06c52"
_C_SAGE       = "#8da399"
_C_BG         = "#F7F5F2"
_C_CARD       = "#FFFFFF"
_C_BORDER     = "#E5EAE7"
_C_MUTED      = "#6b7280"


class DashboardFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, corner_radius=0, fg_color=(_C_BG, "#0d1a12"))
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build_ui()

    def _build_ui(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=28, pady=(24, 0))
        hdr.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            hdr, text="Inicio",
            font=ctk.CTkFont(size=26, weight="bold")
        ).grid(row=0, column=0, sticky="w")

        # Scrollable main content
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.grid(row=1, column=0, sticky="nsew", padx=0, pady=(12, 0))
        scroll.grid_columnconfigure(0, weight=1)

        self._stat_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self._stat_frame.grid(row=0, column=0, sticky="ew", padx=28, pady=(0, 20))
        for i in range(4):
            self._stat_frame.grid_columnconfigure(i, weight=1)

        mid = ctk.CTkFrame(scroll, fg_color="transparent")
        mid.grid(row=1, column=0, sticky="ew", padx=28, pady=(0, 20))
        mid.grid_columnconfigure(0, weight=1)
        mid.grid_columnconfigure(1, weight=1)

        self._patients_panel = ctk.CTkFrame(
            mid, fg_color=(_C_CARD, "#1a2620"),
            corner_radius=12, border_width=1, border_color=(_C_BORDER, "#2a3d30")
        )
        self._patients_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self._patients_panel.grid_columnconfigure(0, weight=1)

        self._activity_panel = ctk.CTkFrame(
            mid, fg_color=(_C_CARD, "#1a2620"),
            corner_radius=12, border_width=1, border_color=(_C_BORDER, "#2a3d30")
        )
        self._activity_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        self._activity_panel.grid_columnconfigure(0, weight=1)

        self._chart_panel = ctk.CTkFrame(
            scroll, fg_color=(_C_CARD, "#1a2620"),
            corner_radius=12, border_width=1, border_color=(_C_BORDER, "#2a3d30")
        )
        self._chart_panel.grid(row=2, column=0, sticky="ew", padx=28, pady=(0, 28))
        self._chart_panel.grid_columnconfigure(0, weight=1)

    def on_show(self):
        self._refresh()

    def _refresh(self):
        self._build_stats()
        self._build_recent_patients()
        self._build_activity()
        self._build_chart()

    def _stat_card(self, parent, col, title, value, subtitle, sub_color=None):
        card = ctk.CTkFrame(
            parent, fg_color=(_C_CARD, "#1a2620"),
            corner_radius=12, border_width=1, border_color=(_C_BORDER, "#2a3d30")
        )
        card.grid(row=0, column=col, sticky="nsew",
                  padx=(0 if col == 0 else 8, 0))

        # Top bar (sage accent)
        accent = ctk.CTkFrame(card, height=4, fg_color=_C_SAGE, corner_radius=2)
        accent.pack(fill="x", padx=0, pady=(0, 0))
        accent.pack_propagate(False)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=18, pady=14)

        ctk.CTkLabel(
            inner, text=title.upper(),
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=(_C_MUTED, "#9ab0a0")
        ).pack(anchor="w")

        ctk.CTkLabel(
            inner, text=str(value),
            font=ctk.CTkFont(size=28, weight="bold"),
        ).pack(anchor="w", pady=(2, 0))

        ctk.CTkLabel(
            inner, text=subtitle,
            font=ctk.CTkFont(size=11),
            text_color=(sub_color or _C_MUTED, "#9ab0a0")
        ).pack(anchor="w", pady=(4, 0))

    def _build_stats(self):
        for w in self._stat_frame.winfo_children():
            w.destroy()

        patients = db.get_all_patients()
        n_patients = len(patients)

        today = date.today().isoformat()
        month_start = date.today().replace(day=1).isoformat()

        # Count pautas this month
        pautas_mes = 0
        try:
            for p in patients:
                try:
                    pautas = db.get_pautas_paciente(p["id"])
                    for pa in pautas:
                        if pa.get("fecha", "") >= month_start:
                            pautas_mes += 1
                except Exception:
                    pass
        except Exception:
            pautas_mes = 0

        # Count evaluations today
        evals_hoy = 0
        try:
            for p in patients:
                records = db.get_anthropometrics(p["id"])
                for r in records:
                    if r.get("session_date", "") == today:
                        evals_hoy += 1
        except Exception:
            evals_hoy = 0

        self._stat_card(self._stat_frame, 0, "Total Pacientes", n_patients,
                        "registrados en total")
        self._stat_card(self._stat_frame, 1, "Pautas este mes", pautas_mes,
                        f"desde el 01/{date.today().strftime('%m/%Y')}",
                        _C_PRIMARY)
        self._stat_card(self._stat_frame, 2, "Evaluaciones hoy", evals_hoy,
                        "sesiones de hoy", _C_MUTED)
        self._stat_card(self._stat_frame, 3, "Pacientes activos",
                        n_patients,
                        "en el sistema", _C_TERRACOTTA)

    def _build_recent_patients(self):
        for w in self._patients_panel.winfo_children():
            w.destroy()

        hdr = ctk.CTkFrame(self._patients_panel, fg_color="transparent")
        hdr.pack(fill="x", padx=18, pady=(16, 8))

        ctk.CTkLabel(
            hdr, text="Pacientes recientes",
            font=ctk.CTkFont(size=15, weight="bold")
        ).pack(side="left")

        ctk.CTkButton(
            hdr, text="Ver todos",
            font=ctk.CTkFont(size=12), width=80, height=28,
            fg_color="transparent", hover_color=("#e8f2ed", "#1f3028"),
            text_color=(_C_PRIMARY, "#6ec896"),
            command=lambda: self.app._show_frame("patients")
        ).pack(side="right")

        patients = db.get_all_patients()
        recent = patients[:5] if patients else []

        if not recent:
            ctk.CTkLabel(
                self._patients_panel,
                text="No hay pacientes registrados",
                font=ctk.CTkFont(size=12), text_color=_C_MUTED
            ).pack(pady=20)
            return

        for p in recent:
            self._patient_row(self._patients_panel, p)

        ctk.CTkFrame(self._patients_panel, height=12, fg_color="transparent").pack()

    def _patient_row(self, parent, p):
        from utils.image_helpers import get_initials
        row = ctk.CTkFrame(parent, fg_color="transparent", cursor="hand2")
        row.pack(fill="x", padx=12, pady=2)

        initials = get_initials(p.get("name", "?"))[:2]

        avatar = ctk.CTkLabel(
            row, text=initials, width=44, height=44,
            fg_color=(_C_SAGE + "40", "#2a3d30"),
            corner_radius=22,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=(_C_PRIMARY, "#6ec896")
        )
        avatar.pack(side="left", padx=(6, 10), pady=8)

        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            info, text=p.get("name", "—"),
            font=ctk.CTkFont(size=13, weight="bold"), anchor="w"
        ).pack(anchor="w")

        age_str = f"{p.get('age')} años" if p.get("age") else "—"
        contact = p.get("phone") or p.get("email") or "—"
        ctk.CTkLabel(
            info, text=f"{age_str}  ·  {contact}",
            font=ctk.CTkFont(size=11), text_color=_C_MUTED, anchor="w"
        ).pack(anchor="w")

        ctk.CTkLabel(
            row, text="›",
            font=ctk.CTkFont(size=18), text_color=(_C_MUTED, "#5a7a68")
        ).pack(side="right", padx=12)

        def on_click(pid=p["id"]):
            self.app.set_patient(pid)
            self.app._show_frame("anthropometrics")
        row.bind("<Button-1>", lambda e, pid=p["id"]: on_click(pid))
        for child in row.winfo_children():
            child.bind("<Button-1>", lambda e, pid=p["id"]: on_click(pid))

    def _build_activity(self):
        for w in self._activity_panel.winfo_children():
            w.destroy()

        ctk.CTkLabel(
            self._activity_panel, text="Actividad reciente",
            font=ctk.CTkFont(size=15, weight="bold")
        ).pack(anchor="w", padx=18, pady=(16, 12))

        # Try to get recent anthropometric sessions
        items = []
        try:
            patients = db.get_all_patients()
            for p in patients[:10]:
                records = db.get_anthropometrics(p["id"])
                for r in records[:1]:
                    items.append({
                        "type": "eval",
                        "text": "Evaluación guardada",
                        "sub": f"Paciente: {p['name']}",
                        "date": r.get("session_date", "")
                    })
            items.sort(key=lambda x: x["date"], reverse=True)
            items = items[:5]
        except Exception:
            pass

        try:
            patients = db.get_all_patients()
            for p in patients[:5]:
                try:
                    pautas = db.get_pautas_paciente(p["id"])
                    for pa in pautas[:1]:
                        items.append({
                            "type": "pauta",
                            "text": "Pauta nutricional",
                            "sub": f"Paciente: {p['name']}",
                            "date": pa.get("fecha", "")
                        })
                except Exception:
                    pass
            items.sort(key=lambda x: x["date"], reverse=True)
            items = items[:6]
        except Exception:
            pass

        if not items:
            ctk.CTkLabel(
                self._activity_panel,
                text="Sin actividad reciente",
                font=ctk.CTkFont(size=12), text_color=_C_MUTED
            ).pack(pady=20)
            ctk.CTkFrame(self._activity_panel, height=8, fg_color="transparent").pack()
            return

        for item in items:
            self._activity_row(self._activity_panel, item)

        ctk.CTkFrame(self._activity_panel, height=12, fg_color="transparent").pack()

    def _activity_row(self, parent, item):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=18, pady=3)

        dot = ctk.CTkFrame(row, width=10, height=10, corner_radius=5,
                           fg_color=_C_TERRACOTTA)
        dot.pack(side="left", padx=(0, 12), pady=12)

        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            info, text=item["text"],
            font=ctk.CTkFont(size=12, weight="bold"), anchor="w"
        ).pack(anchor="w")

        ctk.CTkLabel(
            info, text=item["sub"],
            font=ctk.CTkFont(size=11), text_color=_C_MUTED, anchor="w"
        ).pack(anchor="w")

        date_str = item.get("date", "")
        if date_str:
            try:
                d = datetime.fromisoformat(date_str)
                disp = d.strftime("%d/%m")
            except Exception:
                disp = date_str[:10]
        else:
            disp = "—"

        ctk.CTkLabel(
            row, text=disp,
            font=ctk.CTkFont(size=10), text_color=_C_MUTED
        ).pack(side="right")

    def _build_chart(self):
        for w in self._chart_panel.winfo_children():
            w.destroy()

        hdr = ctk.CTkFrame(self._chart_panel, fg_color="transparent")
        hdr.pack(fill="x", padx=18, pady=(16, 4))

        ctk.CTkLabel(
            hdr, text="Evaluaciones por mes",
            font=ctk.CTkFont(size=15, weight="bold")
        ).pack(side="left")

        ctk.CTkLabel(
            hdr, text="Últimos 6 meses",
            font=ctk.CTkFont(size=11), text_color=_C_MUTED
        ).pack(side="right")

        if not _MPL_OK:
            ctk.CTkLabel(
                self._chart_panel,
                text="Instala matplotlib para ver el gráfico",
                font=ctk.CTkFont(size=12), text_color=_C_MUTED
            ).pack(pady=20)
            return

        # Build monthly data
        import calendar
        today = date.today()
        months = []
        counts = []
        for i in range(5, -1, -1):
            m = today.month - i
            y = today.year
            while m <= 0:
                m += 12
                y -= 1
            months.append(calendar.month_abbr[m][:3])
            month_str = f"{y:04d}-{m:02d}"
            try:
                patients = db.get_all_patients()
                cnt = 0
                for p in patients:
                    recs = db.get_anthropometrics(p["id"])
                    for r in recs:
                        sd = r.get("session_date", "")
                        if sd and sd[:7] == month_str:
                            cnt += 1
                counts.append(cnt)
            except Exception:
                counts.append(0)

        try:
            import matplotlib.ticker as mticker
            fig = Figure(figsize=(8, 2.2), dpi=96, facecolor="#FFFFFF")
            ax = fig.add_subplot(111)
            ax.set_facecolor("#FFFFFF")
            ax.bar(months, counts, color=_C_SAGE, width=0.5, edgecolor="none")
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.spines["left"].set_visible(False)
            ax.tick_params(axis="y", left=False, labelsize=8, colors="#6b7280")
            ax.tick_params(axis="x", labelsize=9, colors="#6b7280")
            ax.yaxis.set_major_locator(
                mticker.MaxNLocator(integer=True, nbins=3)
            )
            ax.grid(axis="y", linestyle="--", alpha=0.3, color=_C_SAGE)
            fig.tight_layout(pad=0.5)

            canvas = FigureCanvasTkAgg(fig, master=self._chart_panel)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="x", padx=18, pady=(0, 16))
        except Exception:
            ctk.CTkLabel(
                self._chart_panel,
                text="No se pudo renderizar el gráfico.",
                font=ctk.CTkFont(size=12), text_color=_C_MUTED
            ).pack(pady=20)
