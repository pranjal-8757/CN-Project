import tkinter as tk
from tkinter import ttk
import time
import threading
import random

class CCD_AQM_Final_Integrated:
    def __init__(self, root):
        self.root = root
        self.root.title("CCD-AQM: Priority Queue Implementation")
        self.root.geometry("1450x980")
        self.root.configure(bg="#f4f7f6")
        
        # State Management
        self.is_auto_on = False
        self.queues = { "X": [], "Y": [], "Z": [] }
        self.queue_history = { "X": [0, 0, 0], "Y": [0, 0, 0], "Z": [0, 0, 0] }
        
        # Statistics
        self.stats = {p: {"delivered": 0, "dropped": 0} for p in ["High", "Medium", "Low"]}
        self.total_sent = 0
        self.total_delivered = 0
        self.total_dropped = 0
        
        self.max_queue_size = 10
        self.priority_map = {"High": "#27ae60", "Medium": "#f1c40f", "Low": "#e74c3c"}
        self.priority_weights = {"High": 3, "Medium": 2, "Low": 1}
        
        self.port_in_coords = {}
        self.port_out_coords = {}
        self.fabric_lines = {} 

        self.setup_ui()

    def setup_ui(self):
        header = tk.Frame(self.root, bg="#2c3e50", height=70)
        header.pack(fill="x")
        tk.Label(header, text="CCD-AQM: Priority Queue Implementation", 
                 fg="white", bg="#2c3e50", font=("Arial", 16, "bold")).pack(pady=15)

        # Main Visualization
        self.canvas = tk.Canvas(self.root, width=1400, height=550, bg="white", 
                                highlightthickness=1, highlightbackground="#bdc3c7")
        self.canvas.pack(pady=15)

        self.draw_fabric()
        self.setup_bottom_dashboard()

    def draw_fabric(self):
        # Input Ports
        for i, name in enumerate(["A", "B", "C"]):
            y = 100 + (i * 150)
            self.canvas.create_rectangle(50, y-35, 130, y+35, fill="#ecf0f1", outline="#34495e", width=2)
            self.canvas.create_text(90, y, text=f"Input {name}", font=("Arial", 9, "bold"))
            self.port_in_coords[name] = (130, y)

        # Output Ports
        self.prob_labels = {}
        for i, name in enumerate(["X", "Y", "Z"]):
            y = 100 + (i * 150)
            self.canvas.create_rectangle(500, y-35, 580, y+35, fill="#ecf0f1", outline="#34495e", width=2)
            self.canvas.create_text(540, y, text=f"Output {name}", font=("Arial", 9, "bold"))
            self.port_out_coords[name] = (500, y)
            
            # Probability Labels
            self.prob_labels[name] = self.canvas.create_text(750, y-50, text="Drop Prob: 0%", font=("Arial", 9, "bold"), fill="#c0392b")
            
            # Draw Fabric Lines
            for in_name, in_coord in self.port_in_coords.items():
                line_id = self.canvas.create_line(in_coord[0], in_coord[1], 500, y, fill="#eeeeee", width=1)
                self.fabric_lines[f"{in_name}->{name}"] = line_id

    def setup_bottom_dashboard(self):
        dash = tk.Frame(self.root, bg="#f4f7f6")
        dash.pack(fill="x", padx=40, pady=10)

        # 1. Global Counters
        global_frame = tk.LabelFrame(dash, text=" Global Counters ", bg="white", font=("Arial", 10, "bold"))
        global_frame.pack(side="left", padx=10, fill="y")
        
        self.lbl_total_sent = tk.Label(global_frame, text="Total Sent: 0", bg="white", width=25, anchor="w")
        self.lbl_total_sent.pack(padx=10, pady=2)
        self.lbl_total_deliv = tk.Label(global_frame, text="Total Delivered: 0", bg="white", fg="#27ae60", width=25, anchor="w")
        self.lbl_total_deliv.pack(padx=10, pady=2)
        self.lbl_total_drop = tk.Label(global_frame, text="Total Dropped: 0", bg="white", fg="#c0392b", width=25, anchor="w")
        self.lbl_total_drop.pack(padx=10, pady=2)

        prio_frame = tk.LabelFrame(dash, text=" Priority Statistics ", bg="white", font=("Arial", 10, "bold"))
        prio_frame.pack(side="left", padx=10, expand=True, fill="both")
        
        cols = ["Priority", "Delivered", "Dropped", "Efficiency"]
        for j, c in enumerate(cols):
            tk.Label(prio_frame, text=c, font=("Arial", 9, "bold"), bg="white").grid(row=0, column=j, padx=35)

        self.table_widgets = {}
        for i, p in enumerate(["High", "Medium", "Low"]):
            tk.Label(prio_frame, text=p, fg=self.priority_map[p], font=("Arial", 9, "bold"), bg="white").grid(row=i+1, column=0)
            d_l = tk.Label(prio_frame, text="0", bg="white"); d_l.grid(row=i+1, column=1)
            dr_l = tk.Label(prio_frame, text="0", bg="white"); dr_l.grid(row=i+1, column=2)
            ef_l = tk.Label(prio_frame, text="0.0%", bg="white"); ef_l.grid(row=i+1, column=3)
            self.table_widgets[p] = (d_l, dr_l, ef_l)

        #Simulation Controls
        ctrl_frame = tk.Frame(dash, bg="#f4f7f6")
        ctrl_frame.pack(side="right", padx=10)
        self.btn_auto = tk.Button(ctrl_frame, text="START AUTO TRAFFIC", command=self.toggle_auto, 
                                  bg="#2980b9", fg="white", font=("Arial", 11, "bold"), padx=20, pady=10)
        self.btn_auto.pack()

        self.status = tk.Label(self.root, text="System Ready", bd=1, relief="sunken", anchor="w")
        self.status.pack(side="bottom", fill="x")

    def toggle_auto(self):
        self.is_auto_on = not self.is_auto_on
        if self.is_auto_on:
            self.btn_auto.config(text="STOP TRAFFIC", bg="#c0392b")
            threading.Thread(target=self.auto_loop, daemon=True).start()
        else:
            self.btn_auto.config(text="START AUTO TRAFFIC", bg="#2980b9")

    def auto_loop(self):
        while self.is_auto_on:
            s = random.choice(["A", "B", "C"])
            d = random.choice(["X", "Y", "Z"])
            p = random.choices(["High", "Medium", "Low"], weights=[30, 40, 30])[0]
            self.total_sent += 1
            threading.Thread(target=self.process_flow, args=(s, d, p)).start()
            time.sleep(random.uniform(0.6, 1.2))

    def get_ccd_prob(self, dest):
        q = len(self.queues[dest])
        if q < 2: return 0.0
        h = self.queue_history[dest]
        h.pop(0); h.append(q)
        prob = min(0.85, (q/10)+0.25) if h[2] > h[1] > h[0] else (q/10)*0.1
        self.canvas.itemconfig(self.prob_labels[dest], text=f"Drop Prob: {prob*100:.1f}%")
        return prob

    def process_flow(self, src, dest, pri):
        line_key = f"{src}->{dest}"
        self.canvas.itemconfig(self.fabric_lines[line_key], fill="#3498db", width=3)
        
        x1, y1 = self.port_in_coords[src]
        x2, y2 = self.port_out_coords[dest]
        
        # CCD-AQM Trend Rejection
        if pri != "High" and random.random() < self.get_ccd_prob(dest):
            self.status.config(text=f"CCD-AQM: Dropped {pri} due to trend", fg="#c0392b")
            self.canvas.itemconfig(self.fabric_lines[line_key], fill="#eeeeee", width=1)
            self.trigger_visual_drop((x1+x2)/2, (y1+y2)/2, pri, "TREND-DROP")
            return

        pkt = self.canvas.create_oval(x1-10, y1-10, x1+10, y1+10, fill=self.priority_map[pri], outline="white")
        steps = 50
        for _ in range(steps):
            self.canvas.move(pkt, (x2-x1)/steps, (y2-y1)/steps)
            self.root.update(); time.sleep(0.015)
        
        self.canvas.itemconfig(self.fabric_lines[line_key], fill="#eeeeee", width=1)
        self.canvas.delete(pkt)

        # 2. Buffer Management
        queue = self.queues[dest]
        if len(queue) < self.max_queue_size:
            queue.append(pri)
            self.update_buffer_view(dest)
            self.transmit_logic(dest)
        else:
            min_w = 4; idx = -1
            for i, p in enumerate(queue):
                if self.priority_weights[p] < min_w:
                    min_w = self.priority_weights[p]; idx = i
            
            if self.priority_weights[pri] > min_w:
                evicted = queue.pop(idx)
                self.trigger_visual_drop(650+(idx*45), y2, evicted, "EVICTED")
                queue.append(pri)
                self.update_buffer_view(dest)
                self.transmit_logic(dest)
            else:
                self.trigger_visual_drop(x2, y2, pri, "REJECTED")

    def transmit_logic(self, dest):
        time.sleep(random.uniform(2, 5))
        if self.queues[dest]:
            p = self.queues[dest].pop(0)
            self.stats[p]["delivered"] += 1
            self.total_delivered += 1
            self.update_ui_counters()
            self.update_buffer_view(dest)

    def trigger_visual_drop(self, x, y, pri, label):
        self.stats[pri]["dropped"] += 1
        self.total_dropped += 1
        self.update_ui_counters()
        d_p = self.canvas.create_oval(x-8, y-8, x+8, y+8, fill="#95a5a6")
        d_t = self.canvas.create_text(x, y-20, text=f"{label}: {pri}", fill="#7f8c8d", font=("Arial", 8, "bold"))
        for _ in range(25):
            self.canvas.move(d_p, 0, 5); self.canvas.move(d_t, 0, 5)
            self.root.update(); time.sleep(0.02)
        self.canvas.delete(d_p); self.canvas.delete(d_t)

    def update_buffer_view(self, dest):
        tag = f"buf_{dest}"
        self.canvas.delete(tag)
        y = self.port_out_coords[dest][1]
        order = {"High": 0, "Medium": 1, "Low": 2}
        self.queues[dest].sort(key=lambda x: order[x])
        
        for i in range(self.max_queue_size):
            x = 650 + (i * 45)
            self.canvas.create_rectangle(x, y-15, x+40, y+15, outline="#dfe6e9", tags=tag)
            if i < len(self.queues[dest]):
                c = self.priority_map[self.queues[dest][i]]
                self.canvas.create_rectangle(x+2, y-13, x+38, y+13, fill=c, outline="white", tags=tag)

    def update_ui_counters(self):
        self.lbl_total_sent.config(text=f"Total Sent: {self.total_sent}")
        self.lbl_total_deliv.config(text=f"Total Delivered: {self.total_delivered}")
        self.lbl_total_drop.config(text=f"Total Dropped: {self.total_dropped}")
        
        for p, d in self.stats.items():
            tot = d["delivered"] + d["dropped"]
            eff = (d["delivered"] / tot * 100) if tot > 0 else 0
            self.table_widgets[p][0].config(text=str(d["delivered"]))
            self.table_widgets[p][1].config(text=str(d["dropped"]))
            self.table_widgets[p][2].config(text=f"{eff:.1f}%")

if __name__ == "__main__":
    root = tk.Tk(); app = CCD_AQM_Final_Integrated(root); root.mainloop()