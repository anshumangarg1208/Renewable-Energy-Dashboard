"""
Renewable Energy & CO2 Analytics Dashboard
Tkinter desktop UI for the existing cleaned dataset and saved graphs.
Run: python main.py
"""
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "cleaned_dataset.csv")
GRAPH_FILES = {
    "Renewable Energy Trend": "graph1_renewable_trend.png",
    "Top 10 Countries by Renewable Electricity": "graph2_top_countries.png",
    "Renewable Share vs CO₂ Emissions": "graph3_renewable_vs_co2.png",
    "Renewable vs Fossil Electricity": "graph4_renewable_vs_fossil.png",
    "Correlation Heatmap": "graph5_correlation_heatmap.png",
}
C_RENEW = "Renewable energy share in the total final energy consumption (%)"
C_CO2 = "Value_co2_emissions_kt_by_country"
C_REN_ELEC = "Electricity from renewables (TWh)"
C_FOSSIL = "Electricity from fossil fuels (TWh)"
C_GDP = "gdp_per_capita"
C_ENERGY = "Primary energy consumption per capita (kWh/person)"

# Calm, iOS-inspired palette: clean surfaces, restrained blue, no glass effects.
BG = "#F5F6FA"
CARD = "#FFFFFF"
NAV = "#FBFCFE"
ACCENT = "#3867F5"
TEXT = "#151A2D"
MUTED = "#7C8498"
BORDER = "#E9ECF3"
GREEN = "#16A982"
SOFT_BLUE = "#EAF0FF"
SIDEBAR_TEXT = "#687187"
INK = "#202943"
LAVENDER = "#F0EDFF"
MINT = "#E6F8F1"

class OfflineMap(tk.Canvas):
    """Offline Natural Earth country outlines with a smooth fly-to camera."""
    WATER = "#E9F1FA"
    LAND = "#DCE8E2"
    EDGE = "#B6CBBF"
    SELECTED = "#BFEAD9"
    DOT = "#078B68"

    def __init__(self, master, **kwargs):
        super().__init__(master, bg=self.WATER, highlightthickness=0, **kwargs)
        self.center_lat, self.center_lon, self.zoom = 18.0, 0.0, 0.72
        self.country = "World"
        self.record = None
        self._animation_id = None
        self.boundaries = []
        path = os.path.join(BASE_DIR, "world_boundaries.geojson")
        try:
            import json
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            for feature in data.get("features", []):
                name = feature.get("properties", {}).get("name", "")
                geom = feature.get("geometry") or {}
                coords = geom.get("coordinates", [])
                polygons = [coords] if geom.get("type") == "Polygon" else coords if geom.get("type") == "MultiPolygon" else []
                for poly in polygons:
                    if not poly: continue
                    ring = poly[0]
                    if len(ring) >= 4:
                        self.boundaries.append((name, [(float(pt[1]), float(pt[0])) for pt in ring]))
        except (OSError, ValueError, KeyError):
            self.boundaries = []
        self.bind("<Configure>", lambda _e: self.draw_map())
        self.draw_map()

    @staticmethod
    def _ease(t):
        return 1 - (1 - t) ** 4

    def set_location(self, country, lat, lon, record=None):
        try:
            lat, lon = float(lat), float(lon)
            if not (-90 <= lat <= 90 and -180 <= lon <= 180): raise ValueError
        except (TypeError, ValueError):
            self.country, self.record = country, record
            self.draw_map()
            return
        if self._animation_id is not None:
            try: self.after_cancel(self._animation_id)
            except tk.TclError: pass
        self.country, self.record = country, record
        start = (self.center_lat, self.center_lon, self.zoom)
        end = (max(-65, min(78, lat)), lon, 3.2)
        self._fly(start, end, 0, 42)

    def _fly(self, start, end, step, total):
        pull, travel = 12, 18
        if step < pull:
            t = self._ease((step + 1) / pull)
            self.center_lat, self.center_lon = start[0], start[1]
            self.zoom = start[2] + (0.48 - start[2]) * t
        elif step < pull + travel:
            t = self._ease((step - pull + 1) / travel)
            delta = ((end[1] - start[1] + 180) % 360) - 180
            self.center_lat = start[0] + (end[0] - start[0]) * t
            self.center_lon = start[1] + delta * t
            self.zoom = 0.48
        else:
            t = self._ease((step - pull - travel + 1) / (total - pull - travel))
            self.center_lat, self.center_lon = end[0], end[1]
            self.zoom = 0.48 + (end[2] - 0.48) * t
        self.draw_map()
        if step + 1 < total:
            self._animation_id = self.after(16, lambda: self._fly(start, end, step + 1, total))
        else:
            self.center_lat, self.center_lon, self.zoom = end
            self.draw_map()
            self._animation_id = None

    def _xy(self, lat, lon, w, h):
        dlon = ((lon - self.center_lon + 180) % 360) - 180
        scale = min(w / 360, h / 180) * self.zoom
        return w / 2 + dlon * scale, h / 2 - (lat - self.center_lat) * scale

    def draw_map(self):
        self.delete("all")
        w, h = max(self.winfo_width(), 320), max(self.winfo_height(), 240)
        self.create_rectangle(0, 0, w, h, fill=self.WATER, outline="")
        # Gentle graticule behind the real bundled country outlines.
        for lat in (-60, -30, 0, 30, 60):
            pts = [self._xy(lat, lon, w, h) for lon in range(-180, 181, 5)]
            self.create_line(*[v for xy in pts for v in xy], fill="#D7E4F0", width=1, smooth=True)
        for lon in range(-150, 181, 30):
            pts = [self._xy(lat, lon, w, h) for lat in range(-85, 86, 4)]
            self.create_line(*[v for xy in pts for v in xy], fill="#D7E4F0", width=1, smooth=True)
        for name, coords in self.boundaries:
            pts = [self._xy(lat, lon, w, h) for lat, lon in coords]
            flat = [v for xy in pts for v in xy]
            if len(flat) >= 6:
                fill = self.SELECTED if name.casefold() == str(self.country).casefold() else self.LAND
                self.create_polygon(*flat, fill=fill, outline=self.EDGE, width=1, smooth=False)
        if self.record is not None:
            try:
                lat, lon = float(self.record.get("Latitude")), float(self.record.get("Longitude"))
                x, y = self._xy(lat, lon, w, h)
                # Focus reticle and marker, drawn above actual geography.
                self.create_oval(x-16, y-16, x+16, y+16, outline="#52B99A", width=2)
                self.create_oval(x-9, y-9, x+9, y+9, fill="white", outline="")
                self.create_oval(x-5, y-5, x+5, y+5, fill=self.DOT, outline="")
                lx = min(w-8, max(8, x+20)); ly = min(h-12, max(12, y-18))
                self.create_text(lx, ly, text=self.country, anchor="w", fill="#153D32", font=("Segoe UI", 10, "bold"))
            except (TypeError, ValueError): pass
        self.create_text(16, 15, text="WORLD ATLAS  /  OFFLINE", anchor="nw", fill="#59758C", font=("Segoe UI", 8, "bold"))
        self.create_text(w-14, h-12, text="Natural Earth • country boundaries", anchor="se", fill="#6E8799", font=("Segoe UI", 8))


class RenewableDashboard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Renewable Energy & CO₂ Analytics")
        self.geometry("1400x850")
        self.minsize(1100, 700)
        self.configure(bg=BG)
        self.df = self.load_data()
        self.filtered = self.df.copy()
        self._images = []
        self._setup_style()
        self._build_shell()
        self.show_page("Dashboard")

    def load_data(self):
        if not os.path.exists(DATA_FILE):
            messagebox.showerror("Dataset not found",
                "Place cleaned_dataset.csv in the same folder as main.py.")
            return pd.DataFrame()
        try:
            data = pd.read_csv(DATA_FILE)
            if "Entity" not in data or "Year" not in data:
                raise ValueError("Dataset must contain Entity and Year columns.")
            data["Year"] = pd.to_numeric(data["Year"], errors="coerce")
            return data
        except Exception as exc:
            messagebox.showerror("Could not load dataset", str(exc))
            return pd.DataFrame()

    def _setup_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Treeview", rowheight=39, font=("Segoe UI", 10),
                        background="#FFFFFF", fieldbackground="#FFFFFF", foreground=TEXT,
                        borderwidth=0, relief="flat")
        style.map("Treeview", background=[("selected", "#E6ECFF")],
                  foreground=[("selected", TEXT)])
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"),
                        background="#F5F6FA", foreground="#737C91", padding=(12, 13),
                        relief="flat", borderwidth=0)
        style.map("Treeview.Heading", background=[("active", "#EEF1F8")])
        style.configure("TCombobox", padding=9, fieldbackground="#FFFFFF",
                        background="#FFFFFF", foreground=TEXT, borderwidth=0)
        style.configure("TEntry", padding=10, fieldbackground="#FFFFFF",
                        foreground=TEXT, borderwidth=0)
        style.configure("TButton", padding=(15, 11), font=("Segoe UI", 9, "bold"),
                        background="#ECEFF5", foreground=TEXT, borderwidth=0,
                        focusthickness=0, focuscolor="#ECEFF5")
        style.map("TButton", background=[("active", "#E1E6F0")])
        style.configure("Nav.TButton", background=NAV, foreground=SIDEBAR_TEXT,
                        borderwidth=0, padding=(14, 12), anchor="w", font=("Segoe UI", 10))
        style.map("Nav.TButton", background=[("active", "#EEF1FF")],
                  foreground=[("active", ACCENT)])
        style.configure("Primary.TButton", background=ACCENT, foreground="#FFFFFF",
                        padding=(17, 12), borderwidth=0, focusthickness=0,
                        font=("Segoe UI", 9, "bold"))
        style.map("Primary.TButton", background=[("active", "#2855E8")],
                  foreground=[("active", "#FFFFFF")])
        style.configure("Vertical.TScrollbar", background="#E4E8F0",
                        troughcolor="#FFFFFF", bordercolor="#FFFFFF", arrowcolor="#7C8498")
    def _build_shell(self):
        # Clean, native-feeling app rail: light surfaces, restrained colour and a clear active pill.
        self.sidebar = tk.Frame(self, bg=NAV, width=244)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        brand = tk.Frame(self.sidebar, bg=NAV)
        brand.pack(fill="x", padx=22, pady=(28, 34))
        mark = tk.Canvas(brand, width=38, height=38, bg=NAV, highlightthickness=0)
        mark.pack(side="left")
        mark.create_oval(2, 2, 36, 36, fill=ACCENT, outline="")
        mark.create_text(19, 19, text="↗", fill="white", font=("Segoe UI", 21, "bold"))
        brand_text = tk.Frame(brand, bg=NAV)
        brand_text.pack(side="left", padx=(10, 0))
        tk.Label(brand_text, text="ENERGY", bg=NAV, fg=TEXT,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w")
        tk.Label(brand_text, text="INSIGHTS", bg=NAV, fg=MUTED,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(1, 0))

        tk.Label(self.sidebar, text="YOUR WORKSPACE", bg=NAV, fg="#A0A7B7",
                 font=("Segoe UI", 8, "bold"), anchor="w").pack(fill="x", padx=23, pady=(0, 10))
        self.nav_buttons = {}
        self.nav_items = {}
        for name, icon in [
            ("Dashboard", "⌂"), ("Visualizations", "◫"), ("Country Analysis", "◎"),
            ("Dataset Explorer", "▦"), ("About Project", "ⓘ")
        ]:
            item = tk.Frame(self.sidebar, bg=NAV, height=45)
            item.pack(fill="x", padx=12, pady=3)
            item.pack_propagate(False)
            marker = tk.Frame(item, bg=NAV, width=3)
            marker.pack(side="left", fill="y", padx=(0, 6))
            btn = tk.Button(item, text=f"{icon}   {name}", anchor="w", relief="flat",
                            bd=0, cursor="hand2", bg=NAV, fg=SIDEBAR_TEXT,
                            activebackground="#EEF1FF", activeforeground=ACCENT,
                            font=("Segoe UI", 10), padx=13,
                            command=lambda n=name: self.show_page(n))
            btn.pack(side="left", fill="both", expand=True)
            self.nav_buttons[name] = btn
            self.nav_items[name] = (item, marker)
            btn.bind("<Enter>", lambda _e, b=btn, n=name: b.configure(
                bg="#F0F3FC" if self._active_page != n else "#E9EDFF"))
            btn.bind("<Leave>", lambda _e, b=btn, n=name: b.configure(
                bg="#E9EDFF" if self._active_page == n else NAV))

        tk.Frame(self.sidebar, bg=BORDER, height=1).pack(fill="x", padx=22, pady=23)
        tk.Label(self.sidebar, text="DATASET RANGE", bg=NAV, fg="#A0A7B7",
                 font=("Segoe UI", 8, "bold"), anchor="w").pack(fill="x", padx=23)
        tk.Label(self.sidebar, text="2000  —  2020", bg=NAV, fg=TEXT,
                 font=("Segoe UI", 13, "bold"), anchor="w", padx=23, pady=10).pack(fill="x")
        status = tk.Frame(self.sidebar, bg="#F0F8F5")
        status.pack(side="bottom", fill="x", padx=16, pady=18)
        tk.Label(status, text="●  OFFLINE READY", bg="#F0F8F5", fg="#16876A",
                 font=("Segoe UI", 8, "bold"), anchor="w").pack(fill="x", padx=12, pady=10)

        self.main = tk.Frame(self, bg=BG)
        self.main.pack(side="left", fill="both", expand=True)
        self.header = tk.Frame(self.main, bg=BG)
        self.header.pack(fill="x", padx=38, pady=(30, 14))
        title_block = tk.Frame(self.header, bg=BG)
        title_block.pack(side="left", fill="x", expand=True)
        self.page_title = tk.Label(title_block, text="", bg=BG, fg=TEXT,
                                   font=("Segoe UI", 27, "bold"))
        self.page_title.pack(anchor="w")
        self.page_subtitle = tk.Label(title_block, text="", bg=BG, fg=MUTED,
                                      font=("Segoe UI", 9))
        self.page_subtitle.pack(anchor="w", pady=(5, 0))
        self.header_badge = tk.Label(self.header, text="●  LIVE DATASET",
                                     bg=MINT, fg="#16876A",
                                     font=("Segoe UI", 8, "bold"), padx=12, pady=8)
        self.header_badge.pack(side="right", anchor="n", pady=(4, 0))
        self.body = tk.Frame(self.main, bg=BG)
        self.body.pack(fill="both", expand=True, padx=38, pady=(8, 28))
        self._active_page = ""

    def show_page(self, name):
        for child in self.body.winfo_children():
            child.destroy()
        self._active_page = name
        for nav_name, btn in self.nav_buttons.items():
            active = nav_name == name
            btn.configure(bg="#E9EDFF" if active else NAV,
                          fg=ACCENT if active else SIDEBAR_TEXT,
                          font=("Segoe UI", 10, "bold" if active else "normal"))
            item, marker = self.nav_items[nav_name]
            item.configure(bg=NAV)
            marker.configure(bg=ACCENT if active else NAV)
        self.page_title.config(text=name)
        self.page_subtitle.config(text="GLOBAL RENEWABLE ENERGY  /  CO₂  /  ECONOMIC INDICATORS")
        self.header_badge.config(text="●  " + ("DATA EXPLORER" if name == "Dataset Explorer" else "ANALYTICS WORKSPACE"))
        if name == "Dashboard":
            self.page_dashboard()
        elif name == "Visualizations":
            self.page_visualizations()
        elif name == "Country Analysis":
            self.page_country()
        elif name == "Dataset Explorer":
            self.page_dataset()
        else:
            self.page_about()

    def card(self, parent, title, value, note, accent=ACCENT):
        frame = tk.Frame(parent, bg=CARD, highlightbackground="#ECEFF5",
                         highlightthickness=1, padx=18, pady=17)
        top = tk.Frame(frame, bg=CARD)
        top.pack(fill="x")
        dot = tk.Canvas(top, width=28, height=28, bg=CARD, highlightthickness=0)
        dot.pack(side="left")
        dot.create_oval(3, 3, 25, 25, fill=accent, outline="")
        dot.create_oval(10, 10, 18, 18, fill="#FFFFFF", outline="")
        tk.Label(top, text=title, bg=CARD, fg=MUTED,
                 font=("Segoe UI", 9, "bold")).pack(side="left", padx=(9, 0))
        tk.Label(frame, text=value, bg=CARD, fg=TEXT,
                 font=("Segoe UI", 24, "bold")).pack(anchor="w", pady=(13, 3))
        tk.Label(frame, text=note, bg=CARD, fg=MUTED,
                 font=("Segoe UI", 8), wraplength=220).pack(anchor="w")
        return frame

    def _metric(self, col, series):
        if col not in self.df.columns:
            return "—"
        s = pd.to_numeric(series, errors="coerce").dropna()
        if s.empty:
            return "—"
        return f"{s.mean():,.2f}"

    def page_dashboard(self):
        if self.df.empty:
            return
        years = self.df["Year"].dropna()
        countries = self.df["Entity"].nunique()
        row = tk.Frame(self.body, bg=BG)
        row.pack(fill="x", pady=(0, 16))
        metrics = [
            ("Countries covered", f"{countries:,}", "Unique entities in cleaned dataset", "#2E6BE6"),
            ("Country-year records", f"{len(self.df):,}", "Rows available for analysis", "#0F9D8A"),
            ("Average renewable share", self._metric(C_RENEW, self.df[C_RENEW]) if C_RENEW in self.df else "—",
             "Mean across available country-year records (%)", "#7C5CE0"),
            ("Average CO₂ emissions", self._metric(C_CO2, self.df[C_CO2]) if C_CO2 in self.df else "—",
             "Mean across records (kt)", "#E27B43"),
        ]
        for title, value, note, color in metrics:
            c = self.card(row, title, value, note, color)
            c.pack(side="left", fill="both", expand=True, padx=(0, 12))
        info = tk.Frame(self.body, bg=BG)
        info.pack(fill="both", expand=True)
        left = tk.Frame(info, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        left.pack(side="left", fill="both", expand=True, padx=(0, 12))
        tk.Label(left, text="Project overview", bg=CARD, fg=TEXT,
                 font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=18, pady=(16, 5))
        tk.Label(left, text=("Explore how renewable energy adoption, electricity generation, "
                 "economic indicators and CO₂ emissions vary across countries from 2000 to 2020."),
                 bg=CARD, fg=MUTED, font=("Segoe UI", 10), wraplength=510,
                 justify="left").pack(anchor="w", padx=18, pady=(0, 14))
        for label, desc in [
            ("01  Trend analysis", "Track average renewable energy share over time."),
            ("02  Country ranking", "Compare the leading countries by renewable electricity in 2020."),
            ("03  Emissions relationship", "Inspect renewable share versus CO₂ emissions."),
            ("04  Correlation analysis", "Review relationships among energy and economic indicators."),
        ]:
            tk.Label(left, text=label, bg=CARD, fg=TEXT,
                     font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=18, pady=(7, 1))
            tk.Label(left, text=desc, bg=CARD, fg=MUTED,
                     font=("Segoe UI", 9)).pack(anchor="w", padx=36, pady=(0, 2))
        right = tk.Frame(info, bg=CARD, width=330, highlightbackground=BORDER, highlightthickness=1)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)
        tk.Label(right, text="Quick actions", bg=CARD, fg=TEXT,
                 font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=18, pady=(16, 12))
        ttk.Button(right, text="Open visualizations  →", style="Primary.TButton",
                   command=lambda: self.show_page("Visualizations")).pack(fill="x", padx=18, pady=5)
        ttk.Button(right, text="Explore countries  →",
                   command=lambda: self.show_page("Country Analysis")).pack(fill="x", padx=18, pady=5)
        ttk.Button(right, text="View cleaned dataset  →",
                   command=lambda: self.show_page("Dataset Explorer")).pack(fill="x", padx=18, pady=5)
        tk.Label(right, text="Dataset summary", bg=CARD, fg=TEXT,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=18, pady=(22, 7))
        yrmin = int(years.min()) if not years.empty else "—"
        yrmax = int(years.max()) if not years.empty else "—"
        for line in [f"Years available: {yrmin}–{yrmax}",
                     f"Columns: {len(self.df.columns)}",
                     f"Missing cells: {int(self.df.isna().sum().sum()):,}",
                     "Graphs: 5 supplied visualizations"]:
            tk.Label(right, text="•  " + line, bg=CARD, fg=MUTED,
                     font=("Segoe UI", 9)).pack(anchor="w", padx=18, pady=3)

    def page_visualizations(self):
        intro = tk.Frame(self.body, bg=BG)
        intro.pack(fill="x", pady=(0, 10))
        tk.Label(intro, text="Select a graph to view your existing analysis.",
                 bg=BG, fg=MUTED, font=("Segoe UI", 10)).pack(side="left")
        names = list(GRAPH_FILES)
        self.graph_choice = tk.StringVar(value=names[0])
        combo = ttk.Combobox(intro, textvariable=self.graph_choice, values=names,
                             state="readonly", width=42)
        combo.pack(side="right", padx=(8, 0))
        ttk.Button(intro, text="Show graph", style="Primary.TButton",
                   command=self.render_graph).pack(side="right")
        self.graph_area = tk.Frame(self.body, bg=CARD, highlightbackground=BORDER,
                                   highlightthickness=1)
        self.graph_area.pack(fill="both", expand=True)
        self.graph_label = tk.Label(self.graph_area, bg=CARD, fg=MUTED,
                                    font=("Segoe UI", 11))
        self.graph_label.pack(fill="both", expand=True, padx=12, pady=12)
        self.render_graph()

    def render_graph(self):
        name = self.graph_choice.get()
        path = os.path.join(BASE_DIR, GRAPH_FILES[name])
        if not os.path.exists(path):
            self.graph_label.config(image="", text=f"Graph file not found:\n{path}\n\nCopy the PNG into the application folder.")
            return
        try:
            from PIL import Image, ImageTk
            image = Image.open(path).convert("RGB")
            max_w = max(500, self.graph_area.winfo_width() - 50)
            max_h = max(350, self.graph_area.winfo_height() - 50)
            image.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            self._images = [photo]
            self.graph_label.config(image=photo, text="")
        except ImportError:
            self.graph_label.config(image="", text=(
                "Install Pillow to display graph images inside the app:\n"
                "python -m pip install pillow\n\n"
                f"Graph file: {os.path.basename(path)}"))
        except Exception as exc:
            self.graph_label.config(image="", text=f"Could not display graph:\n{exc}")

    def page_country(self):
        if self.df.empty:
            return
        controls = tk.Frame(self.body, bg=BG)
        controls.pack(fill="x", pady=(0, 12))
        tk.Label(controls, text="Country", bg=BG, fg=TEXT,
                 font=("Segoe UI", 9, "bold")).pack(side="left")
        self.country_var = tk.StringVar(value=sorted(self.df["Entity"].dropna().unique())[0])
        countries = sorted(self.df["Entity"].dropna().unique())
        ttk.Combobox(controls, textvariable=self.country_var, values=countries,
                     state="readonly", width=28).pack(side="left", padx=(8, 18))
        tk.Label(controls, text="Year", bg=BG, fg=TEXT,
                 font=("Segoe UI", 9, "bold")).pack(side="left")
        year_values = sorted(self.df["Year"].dropna().astype(int).unique())
        self.year_var = tk.StringVar(value=str(year_values[-1]))
        ttk.Combobox(controls, textvariable=self.year_var,
                     values=[str(y) for y in year_values], state="readonly",
                     width=10).pack(side="left", padx=8)
        ttk.Button(controls, text="Apply filters", style="Primary.TButton",
                   command=self.update_country).pack(side="left", padx=8)
        self.country_results = tk.Frame(self.body, bg=BG)
        self.country_results.pack(fill="both", expand=True)
        self.update_country()

    def update_country(self):
        for w in self.country_results.winfo_children():
            w.destroy()
        country = self.country_var.get()
        year = int(self.year_var.get())
        row = self.df[(self.df["Entity"] == country) & (self.df["Year"] == year)]
        if row.empty:
            tk.Label(self.country_results, text="No record found for this country and year.",
                     bg=BG, fg=MUTED).pack(anchor="w")
            return
        r = row.iloc[0]
        metrics = [
            ("Renewable share", C_RENEW, "%", "#2E6BE6"),
            ("CO₂ emissions", C_CO2, "kt", "#E27B43"),
            ("Renewable electricity", C_REN_ELEC, "TWh", "#0F9D8A"),
            ("Fossil electricity", C_FOSSIL, "TWh", "#7C5CE0"),
            ("GDP per capita", C_GDP, "", "#C24B68"),
            ("Energy consumption per capita", C_ENERGY, "kWh/person", "#64748B"),
        ]
        grid = tk.Frame(self.country_results, bg=BG)
        grid.pack(fill="x")
        for i, (title, col, unit, color) in enumerate(metrics):
            val = pd.to_numeric(pd.Series([r.get(col)]), errors="coerce").iloc[0] if col in row.columns else float("nan")
            value = "—" if pd.isna(val) else f"{val:,.2f} {unit}".strip()
            c = self.card(grid, title, value, f"{country} • {year}", color)
            c.grid(row=i//2, column=i%2, sticky="nsew", padx=(0, 12), pady=(0, 12))
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)
        detail = tk.Frame(self.country_results, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        detail.pack(fill="both", expand=True, pady=(4, 0))
        tk.Label(detail, text=f"{country} — available indicators in {year}",
                 bg=CARD, fg=TEXT, font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=16, pady=12)
        tree = ttk.Treeview(detail, columns=("indicator", "value"), show="headings")
        tree.heading("indicator", text="Indicator")
        tree.heading("value", text="Value")
        tree.column("indicator", width=430)
        tree.column("value", width=250)
        tree.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        for col in self.df.columns:
            if col not in ("Entity", "Year"):
                v = r[col]
                if pd.notna(v):
                    display = f"{v:,.3f}" if isinstance(v, (int, float)) else str(v)
                    tree.insert("", "end", values=(col, display))

    def page_dataset(self):
        if self.df.empty:
            return
        top = tk.Frame(self.body, bg=BG)
        top.pack(fill="x", pady=(0, 10))
        tk.Label(top, text="Search country or indicator value", bg=BG, fg=TEXT).pack(side="left")
        self.search_var = tk.StringVar()
        entry = ttk.Entry(top, textvariable=self.search_var, width=32)
        entry.pack(side="left", padx=8)
        entry.bind("<Return>", lambda _e: self.populate_dataset())
        ttk.Button(top, text="Search", style="Primary.TButton",
                   command=self.populate_dataset).pack(side="left")
        ttk.Button(top, text="Export filtered CSV",
                   command=self.export_dataset).pack(side="right")

        # Explorer split view: familiar dataset table + offline map that follows selection.
        split = tk.Frame(self.body, bg=BG)
        split.pack(fill="both", expand=True)
        split.columnconfigure(0, weight=3, minsize=420)
        split.columnconfigure(1, weight=2, minsize=300)
        split.rowconfigure(0, weight=1)

        self.table_frame = tk.Frame(split, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        self.table_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        map_panel = tk.Frame(split, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        map_panel.grid(row=0, column=1, sticky="nsew")
        map_header = tk.Frame(map_panel, bg=CARD)
        map_header.pack(fill="x", padx=16, pady=(14, 6))
        tk.Label(map_header, text="Country explorer", bg=CARD, fg=TEXT,
                 font=("Segoe UI", 14, "bold")).pack(anchor="w")
        tk.Label(map_header, text="Select any row to fly to its coordinates",
                 bg=CARD, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", pady=(3, 0))
        self.dataset_map = OfflineMap(map_panel, height=320)
        self.dataset_map.pack(fill="both", expand=True, padx=12, pady=(4, 10))
        self.map_info = tk.Frame(map_panel, bg="#F5F9F7")
        self.map_info.pack(fill="x", padx=12, pady=(0, 12))
        self.map_country_label = tk.Label(self.map_info, text="Choose a dataset row",
                 bg="#F5F9F7", fg=TEXT, font=("Segoe UI", 12, "bold"), anchor="w")
        self.map_country_label.pack(fill="x", padx=12, pady=(10, 2))
        self.map_detail_label = tk.Label(self.map_info, text="Country coordinates and indicators will appear here.",
                 bg="#F5F9F7", fg=MUTED, font=("Segoe UI", 9), anchor="w", justify="left")
        self.map_detail_label.pack(fill="x", padx=12, pady=(0, 10))
        self.populate_dataset()

    def _select_dataset_record(self, record):
        country = str(record.get("Entity", "Unknown country"))
        year = record.get("Year", "—")
        year_text = str(int(year)) if pd.notna(year) else "—"
        self.dataset_map.set_location(country, record.get("Latitude"), record.get("Longitude"), record)
        lat, lon = record.get("Latitude"), record.get("Longitude")
        try:
            coord_text = f"{float(lat):.4f}°, {float(lon):.4f}°"
        except (TypeError, ValueError):
            coord_text = "Coordinates unavailable"
        renewable = record.get(C_RENEW)
        try:
            renewable_text = f"{float(renewable):.1f}% renewable share"
        except (TypeError, ValueError):
            renewable_text = "Renewable share unavailable"
        self.map_country_label.config(text=f"{country}  ·  {year_text}")
        self.map_detail_label.config(text=f"{coord_text}    •    {renewable_text}")

    def populate_dataset(self):
        for w in self.table_frame.winfo_children():
            w.destroy()
        query = self.search_var.get().strip().lower()
        data = self.df
        if query:
            mask = data.astype(str).apply(lambda col: col.str.lower().str.contains(query, na=False)).any(axis=1)
            data = data[mask]
        columns = list(data.columns[:8])
        wrapper = tk.Frame(self.table_frame, bg=CARD)
        wrapper.pack(fill="both", expand=True)
        tree = ttk.Treeview(wrapper, columns=columns, show="headings", selectmode="browse")
        yscroll = ttk.Scrollbar(wrapper, orient="vertical", command=tree.yview)
        xscroll = ttk.Scrollbar(self.table_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        for c in columns:
            tree.heading(c, text=c)
            tree.column(c, width=155, minwidth=100, anchor="w")
        records = data.head(1000)
        # Keep the full row behind each visible table item, including hidden coordinates.
        self._dataset_records = {}
        for idx, (_, r) in enumerate(records.iterrows()):
            vals = []
            for c in columns:
                v = r[c]
                vals.append("" if pd.isna(v) else (f"{v:,.3f}" if isinstance(v, (int, float)) else str(v)))
            item_id = tree.insert("", "end", values=vals)
            self._dataset_records[item_id] = r.to_dict()
        tree.pack(side="left", fill="both", expand=True)
        yscroll.pack(side="right", fill="y")
        xscroll.pack(fill="x")
        shown = min(len(data), 1000)
        tk.Label(self.table_frame, text=f"Showing {shown:,} of {len(data):,} matching records • first 8 columns",
                 bg=CARD, fg=MUTED, anchor="w").pack(fill="x", padx=8, pady=6)
        def on_select(_event=None):
            selected = tree.selection()
            if selected:
                record = self._dataset_records.get(selected[0])
                if record:
                    self._select_dataset_record(record)
        tree.bind("<<TreeviewSelect>>", on_select)
        # Select the first result automatically so the map is populated immediately.
        first = tree.get_children()
        if first:
            tree.selection_set(first[0])
            tree.focus(first[0])
            on_select()
        else:
            self.map_country_label.config(text="No matching records")
            self.map_detail_label.config(text="Try a different search term.")

    def export_dataset(self):
        query = self.search_var.get().strip().lower()
        data = self.df
        if query:
            mask = data.astype(str).apply(lambda col: col.str.lower().str.contains(query, na=False)).any(axis=1)
            data = data[mask]
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                    filetypes=[("CSV files", "*.csv")], initialfile="filtered_energy_data.csv")
        if path:
            data.to_csv(path, index=False)
            messagebox.showinfo("Export complete", f"Saved {len(data):,} records to:\n{path}")

    def page_about(self):
        panel = tk.Frame(self.body, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        panel.pack(fill="both", expand=True)
        tk.Label(panel, text="Renewable Energy Adoption and CO₂ Emissions",
                 bg=CARD, fg=TEXT, font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=24, pady=(24, 10))
        statement = ("Problem definition: To analyze renewable energy adoption and energy-related "
                     "indicators across countries from 2000 to 2020, and investigate their relationship "
                     "with CO₂ emissions using data cleaning, visualization, statistical analysis, "
                     "and forecasting techniques.")
        tk.Label(panel, text=statement, bg=CARD, fg=MUTED, font=("Segoe UI", 11),
                 wraplength=850, justify="left").pack(anchor="w", padx=24, pady=(0, 20))
        tk.Label(panel, text="Included visualizations", bg=CARD, fg=TEXT,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=24, pady=(0, 8))
        for item in GRAPH_FILES:
            tk.Label(panel, text="•  " + item, bg=CARD, fg=MUTED,
                     font=("Segoe UI", 10)).pack(anchor="w", padx=42, pady=4)

if __name__ == "__main__":
    app = RenewableDashboard()
    app.mainloop()
