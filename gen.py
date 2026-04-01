import random
import tkinter as tk
from tkinter import ttk, colorchooser, messagebox, filedialog
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors

class CognitiveTargetGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("RCJ Rescue Maze 2026 Target Generator")
        
        # デフォルト設定 (ルールに基づく色の標準値)
        self.color_defs = {
            'Black':  {'hex': '#000000', 'val': -2},
            'Red':    {'hex': '#FF0000', 'val': -1},
            'Yellow': {'hex': '#FFFF00', 'val': 0},
            'Green':  {'hex': '#00FF00', 'val': 1},
            'Blue':   {'hex': '#0000FF', 'val': 2}
        }
        
        self.setup_ui()

    def setup_ui(self):
        # --- 色の設定エリア ---
        color_frame = ttk.LabelFrame(self.root, text="1. 色の設定 (RGB)")
        color_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.color_buttons = {}
        for i, (name, data) in enumerate(self.color_defs.items()):
            ttk.Label(color_frame, text=f"{name} ({data['val']}):").grid(row=i, column=0, padx=5, pady=2)
            btn = tk.Button(color_frame, bg=data['hex'], width=10, command=lambda n=name: self.pick_color(n))
            btn.grid(row=i, column=1, padx=5, pady=2)
            self.color_buttons[name] = btn

        # --- 個数の設定エリア ---
        count_frame = ttk.LabelFrame(self.root, text="2. 生成個数の設定")
        count_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.counts = {
            'Harmed': tk.IntVar(value=3),
            'Stable': tk.IntVar(value=3),
            'Unharmed': tk.IntVar(value=3),
            'Fake': tk.IntVar(value=3)
        }

        labels = [("Harmed (Sum=2)", 'Harmed'), ("Stable (Sum=1)", 'Stable'), 
                  ("Unharmed (Sum=0)", 'Unharmed'), ("Fake (Sum≠0,1,2)", 'Fake')]
        
        for i, (txt, key) in enumerate(labels):
            ttk.Label(count_frame, text=txt).grid(row=i, column=0, padx=5, pady=5)
            ttk.Spinbox(count_frame, from_=0, to=100, textvariable=self.counts[key], width=5).grid(row=i, column=1, padx=5, pady=5)

        # --- オプション設定エリア ---
        opt_frame = ttk.LabelFrame(self.root, text="3. オプション (ルール3.8.6準拠)")
        opt_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        ttk.Label(opt_frame, text="寸法スケール (±10%誤差のシミュレート):").grid(row=0, column=0, padx=5, pady=5)
        self.scale_val = tk.DoubleVar(value=1.0)
        scale_slider = ttk.Scale(opt_frame, from_=0.9, to=1.1, variable=self.scale_val, orient="horizontal", length=200)
        scale_slider.grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(opt_frame, textvariable=self.scale_val).grid(row=0, column=2, padx=5, pady=5)

        # --- 出力ボタン ---
        btn_generate = ttk.Button(self.root, text="PDFを出力する", command=self.generate_pdf)
        btn_generate.grid(row=2, column=0, columnspan=2, pady=20)

    def pick_color(self, name):
        color_code = colorchooser.askcolor(initialcolor=self.color_defs[name]['hex'])[1]
        if color_code:
            self.color_defs[name]['hex'] = color_code
            self.color_buttons[name].config(bg=color_code)

    def get_reportlab_color(self, hex_code):
        return colors.HexColor(hex_code)

    def get_random_pattern(self, target_sum):
        """指定された合計値になる5つの色をランダムに選択"""
        available_colors = list(self.color_defs.keys())
        while True:
            picked = [random.choice(available_colors) for _ in range(4)]
            current_sum = sum(self.color_defs[c]['val'] for c in picked)
            needed_val = target_sum - current_sum
            
            # 必要な値を持つ色が存在するか確認
            match = [name for name, data in self.color_defs.items() if data['val'] == needed_val]
            if match:
                picked.append(match[0])
                random.shuffle(picked)
                return picked

    def get_fake_pattern(self):
        """合計が0,1,2以外になるパターン"""
        available_colors = list(self.color_defs.keys())
        while True:
            picked = [random.choice(available_colors) for _ in range(5)]
            total = sum(self.color_defs[c]['val'] for c in picked)
            if total not in [0, 1, 2]:
                return picked, total

    def generate_pdf(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if not file_path:
            return

        try:
            c = canvas.Canvas(file_path, pagesize=A4)
            width, height = A4
            scale = self.scale_val.get()
            
            # 描画キューの作成
            queue = []
            for t_type in ['Harmed', 'Stable', 'Unharmed', 'Fake']:
                for _ in range(self.counts[t_type].get()):
                    queue.append(t_type)

            # レイアウト定数
            x_start, y_start = 3.0 * cm, height - 3.5 * cm
            x_gap, y_gap = 6.0 * cm, 8.0 * cm
            curr_x, curr_y = x_start, y_start

            for i, t_type in enumerate(queue):
                # パターンの決定
                if t_type == 'Fake':
                    pattern, total_sum = self.get_fake_pattern()
                    label_text = f"Fake (Sum={total_sum})"
                else:
                    sum_val = {'Harmed': 2, 'Stable': 1, 'Unharmed': 0}[t_type]
                    pattern = self.get_random_pattern(sum_val)
                    label_text = f"{t_type} (Sum={sum_val})"

                # ターゲットの描画 (直径5cm * scale)
                for ring_idx in range(5, 0, -1):
                    # 各リングの直径: 5cm, 4cm, 3cm, 2cm, 1cm
                    radius = (ring_idx * 1.0 * cm * scale) / 2
                    color_name = pattern[ring_idx-1]
                    
                    c.setFillColor(self.get_reportlab_color(self.color_defs[color_name]['hex']))
                    c.setStrokeColor(colors.black)
                    c.setLineWidth(0.5)
                    c.circle(curr_x, curr_y, radius, fill=1, stroke=1)

                # ラベルとスケール情報の描画
                c.setFillColor(colors.black)
                c.setFont("Helvetica-Bold", 8)
                c.drawCentredString(curr_x, curr_y - 3.2*cm, label_text)
                c.setFont("Helvetica", 6)
                c.drawCentredString(curr_x, curr_y - 3.6*cm, f"Scale: {scale:.2f}")

                # 次の位置へ
                curr_x += x_gap
                if curr_x > width - 2*cm:
                    curr_x = x_start
                    curr_y -= y_gap
                
                if curr_y < 3*cm and i < len(queue)-1:
                    c.showPage()
                    curr_x, curr_y = x_start, y_start

            c.save()
            messagebox.showinfo("成功", f"PDFが正常に保存されました:\n{file_path}")
        except Exception as e:
            messagebox.showerror("エラー", f"PDF生成中にエラーが発生しました:\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = CognitiveTargetGUI(root)
    root.mainloop()