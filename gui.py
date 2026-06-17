import sys, math
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QRadioButton, QButtonGroup,
    QFrame, QScrollArea, QTextEdit, QDialog, QSizePolicy,
    QGraphicsDropShadowEffect
)
from PyQt5.QtGui import (
    QPainter, QColor, QFont, QPen, QBrush,
    QLinearGradient, QRadialGradient, QPainterPath, QPixmap
)
from PyQt5.QtCore import Qt, QRectF, QPointF, pyqtSignal
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt5.QtCore import QUrl

from hotel_sim import (
    Customer, Table, CustomerState,
    ReservationType, CountingSemaphore, Scheduler
)
 
BG_BASE      = "#f5f0e8"   
BG_APP       = "#ede8de"   
BG_CARD      = "#faf7f2"   
BG_GLASS     = "#f0ece2"   
BG_SURFACE   = "#e8e2d4"   
BORDER       = "#d4c9b0"   
BORDER_LIT   = "#b8a98a"   
BORDER_ACT   = "#7a9e7e"   

WOOD_DARK    = "#5c3d1e"   
WOOD_MID     = "#8b5e2e"   
WOOD_LIGHT   = "#c4956a"   
WOOD_GRAIN   = "#a0722a"   

GREEN_DEEP   = "#2d5a3d"   
GREEN_MID    = "#4a7c59"   
GREEN_LIGHT  = "#7ab893"   
GREEN_LEAF   = "#5a8f4e"   
GREEN_FRESH  = "#8ab87a"   

CREAM        = "#faf7f0"   
CREAM2       = "#f5f0e4"   
AMBER_WARM   = "#d4843a"   
AMBER_LIGHT  = "#e8a84a"   
GOLD_WARM    = "#c8922a"   

T_DARK       = "#2a1f0e"   
T_MID        = "#5c4a2a"  
T_SOFT       = "#8a7454"   
T_MUTED      = "#b0946e"  
T_WHITE      = "#ffffff"

C_FREE       = "#4a7c59"   
C_OCC        = "#b85c3a"   
C_VIP        = "#7a5a9e"   
C_URGENT     = "#c87a3a"   

INPUT_BG     = "#faf8f2"
INPUT_BORDER = "#c8b896"
INPUT_FOCUS  = "#4a7c59"
INPUT_TEXT   = "#2a1f0e"

BTN_BG       = "#2d5a3d"
BTN_HOVER    = "#3d7a52"
BTN_TEXT     = "#f5f0e8"
BTN_BORDER   = "#1e3d2a"

def qc(h): return QColor(h)

def shadow(w, blur=16, dy=4, color="#00000025"):
    ef = QGraphicsDropShadowEffect()
    ef.setColor(QColor(color))
    ef.setBlurRadius(blur)
    ef.setOffset(0, dy)
    w.setGraphicsEffect(ef) 

class FloorCanvas(QWidget):
    def __init__(self, tables, parent=None):
        super().__init__(parent)
        self.tables = tables
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def refresh(self): self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        W, H = self.width(), self.height()
        self._floor(p, W, H)
        self._walls(p, W, H)
        self._ceiling(p, W, H)
        self._decor(p, W, H)
        self._tables(p, W, H)
        p.end()

    def _floor(self, p, W, H):
        plank_colors = ["#c8a878", "#c2a070", "#caa880", "#bea06a", "#c6a478"]
        for i, y in enumerate(range(0, H, 34)):
            p.fillRect(0, y, W, 34, QColor(plank_colors[i % 5]))
            p.setPen(QPen(qc("#b89060"), 1))
            p.drawLine(0, y, W, y)
        p.setPen(QPen(qc("#b8906050"), 1))
        for x in range(0, W, 80):
            p.drawLine(x, 0, x, H)

        for gx, gy, gc in [(W*0.3, H*0.5,"#d4a87040"),(W*0.7,H*0.4,"#c89a6030")]:
            gr = QRadialGradient(gx, gy, 300)
            gr.setColorAt(0, qc(gc)); gr.setColorAt(1, qc("#00000000"))
            p.fillRect(0, 0, W, H, gr)

    def _walls(self, p, W, H):
        wp = QPainterPath(); wp.addRect(QRectF(0, 0, 32, H))
        wg = QLinearGradient(0,0,32,0)
        wg.setColorAt(0, qc("#4a2e10")); wg.setColorAt(1, qc("#6b4420"))
        p.fillPath(wp, wg)
        p.setPen(QPen(qc("#3a2008"), 1))
        for y in range(0, H, 60):
            p.drawLine(0, y, 32, y)

        ceil_path = QPainterPath(); ceil_path.addRect(QRectF(0, 0, W, 42))
        cg = QLinearGradient(0,0,0,42)
        cg.setColorAt(0, qc("#e8dcc8")); cg.setColorAt(1, qc("#d8c8aa"))
        p.fillPath(ceil_path, cg)

        bb = QPainterPath(); bb.addRect(QRectF(32, H-14, W-32, 14))
        bg2 = QLinearGradient(0,H-14,0,H)
        bg2.setColorAt(0, qc("#7a5030")); bg2.setColorAt(1, qc("#5a3820"))
        p.fillPath(bb, bg2)

    def _ceiling(self, p, W, H):
        light_x = [W*0.25, W*0.5, W*0.75]
        for lx in light_x:
            
            p.setPen(QPen(qc("#8a6840"), 1))
            p.drawLine(QPointF(lx, 0), QPointF(lx, 26))

        
            shade = QPainterPath()
            shade.moveTo(lx-14, 26)
            shade.lineTo(lx+14, 26)
            shade.lineTo(lx+9, 46)
            shade.lineTo(lx-9, 46)
            shade.closeSubpath()
            sg = QLinearGradient(lx-14, 26, lx+14, 26)
            sg.setColorAt(0, qc("#5c3d1e")); sg.setColorAt(0.5, qc("#8b5e2e")); sg.setColorAt(1, qc("#5c3d1e"))
            p.fillPath(shade, sg)
            p.setPen(QPen(qc("#3a2008"), 1)); p.setBrush(Qt.NoBrush); p.drawPath(shade)

           
            gr = QRadialGradient(lx, 46, 200)
            gr.setColorAt(0.0, qc("#e8a84035"))
            gr.setColorAt(0.4, qc("#d4843018"))
            gr.setColorAt(1.0, qc("#00000000"))
            p.fillRect(int(lx-200), 46, 400, H, gr)

            
            p.setBrush(QBrush(qc("#fff8e0")))
            p.setPen(Qt.NoPen)
            p.drawEllipse(QRectF(lx-3, 40, 6, 6))

      
        p.setFont(QFont("Georgia", 50, QFont.Bold))
        p.setPen(qc("#c8a87840"))
        p.drawText(self.rect(), Qt.AlignCenter, "Café Lumière")

    def _decor(self, p, W, H):
        self._big_plant(p, 58, H*0.35)
        self._small_plant(p, 50, H-90, 1)
        self._small_plant(p, 82, H-78, 1)
        self._small_plant(p, W-50, H-90, -1)
        self._small_plant(p, W-82, H-78, -1)

        
        self._kitchen_counter(p, W, H)

        self._entrance(p, W, H)

        self._wall_frames(p, H)

        self._window(p, W, H)

    def _big_plant(self, p, cx, cy):
       
        p.setBrush(QBrush(qc("#c8764a"))); p.setPen(QPen(qc("#a85a32"), 1.5))
        p.drawRoundedRect(QRectF(cx-18, cy+20, 36, 30), 5, 5)
       
        p.setBrush(QBrush(qc("#5a3a1a"))); p.setPen(Qt.NoPen)
        p.drawEllipse(QRectF(cx-16, cy+18, 32, 10))
      
        leaf_data = [(-60,1,"#2d5a3d",38),(-20,1,"#3d6e4a",44),(20,-1,"#2d5a3d",40),(60,-1,"#4a7c59",36),(0,1,"#1e4028",46)]
        for angle, flip, lc, sz in leaf_data:
            rad = math.radians(angle - 90)
            lx = cx + sz*math.cos(rad); ly = cy+20 + sz*math.sin(rad)
            path = QPainterPath()
            path.moveTo(cx, cy+20)
            path.cubicTo(
                QPointF(cx + flip*14, cy+20-12),
                QPointF((cx+lx)/2 + flip*10, (cy+20+ly)/2 - 10),
                QPointF(lx, ly)
            )
            path.cubicTo(
                QPointF((cx+lx)/2 - flip*8, (cy+20+ly)/2 + 6),
                QPointF(cx - flip*10, cy+20+8),
                QPointF(cx, cy+20)
            )
            p.setBrush(QBrush(qc(lc))); p.setPen(Qt.NoPen); p.drawPath(path)
           
            p.setPen(QPen(qc("#1e3a2a60"), 1))
            p.drawLine(QPointF(cx, cy+20), QPointF(lx, ly))

    def _small_plant(self, p, cx, base_y, flip):
        p.setBrush(QBrush(qc("#b86840"))); p.setPen(QPen(qc("#8a4820"), 1))
        p.drawRoundedRect(QRectF(cx-10, base_y+28, 20, 18), 4, 4)
        p.setBrush(QBrush(qc("#5a3a1a"))); p.setPen(Qt.NoPen)
        p.drawEllipse(QRectF(cx-8, base_y+26, 16, 8))
        for angle, lc in [(-45*flip,"#3d6e4a"),(0,"#2d5a3d"),(45*flip,"#4a7c59"),(-85*flip,"#5a8f4e")]:
            rad = math.radians(angle - 90)
            lx = cx + 22*math.cos(rad); ly = base_y+28 + 22*math.sin(rad)
            path = QPainterPath()
            path.moveTo(cx, base_y+28)
            path.quadTo(QPointF((cx+lx)/2 - 7*flip, (base_y+28+ly)/2 - 7), QPointF(lx, ly))
            path.quadTo(QPointF((cx+lx)/2 + 7*flip, (base_y+28+ly)/2 + 5), QPointF(cx, base_y+28))
            p.setBrush(QBrush(qc(lc))); p.setPen(Qt.NoPen); p.drawPath(path)

    def _kitchen_counter(self, p, W, H):
        kx, ky, kw, kh = W-210, 44, 196, 125
        kpath = QPainterPath(); kpath.addRoundedRect(QRectF(kx, ky, kw, kh), 8, 8)
        kg = QLinearGradient(kx, ky, kx, ky+kh)
        kg.setColorAt(0, qc("#e8dcc8")); kg.setColorAt(1, qc("#d8c8aa"))
        p.fillPath(kpath, kg)
        p.setPen(QPen(qc(BORDER_LIT), 1.5)); p.setBrush(Qt.NoBrush); p.drawPath(kpath)

        p.setFont(QFont("Georgia", 8, QFont.Bold))
        p.setPen(qc(T_MID))
        p.drawText(QRectF(kx, ky+5, kw, 16), Qt.AlignCenter, "K I T C H E N")

        ct = QPainterPath(); ct.addRoundedRect(QRectF(kx+8, ky+24, kw-16, 14), 3, 3)
        ctg = QLinearGradient(kx+8, ky+24, kx+8, ky+38)
        ctg.setColorAt(0, qc("#e0d8c8")); ctg.setColorAt(1, qc("#ccc0a0"))
        p.fillPath(ct, ctg)
        p.setPen(QPen(qc("#b0a080"), 1)); p.setBrush(Qt.NoBrush); p.drawPath(ct)

        stove = QPainterPath(); stove.addRoundedRect(QRectF(kx+10, ky+40, 80, 50), 5, 5)
        stg = QLinearGradient(kx+10, ky+40, kx+10, ky+90)
        stg.setColorAt(0, qc("#c0b090")); stg.setColorAt(1, qc("#a89870"))
        p.fillPath(stove, stg)
        p.setPen(QPen(qc("#8a7850"), 1)); p.setBrush(Qt.NoBrush); p.drawPath(stove)

        for bx, by in [(kx+28,ky+52),(kx+52,ky+52),(kx+28,ky+72),(kx+52,ky+72)]:
            p.setBrush(QBrush(qc("#7a6840"))); p.setPen(QPen(qc("#5a4820"), 1))
            p.drawEllipse(QRectF(bx-9, by-9, 18, 18))
            p.setBrush(QBrush(qc("#9a8860"))); p.setPen(Qt.NoPen)
            p.drawEllipse(QRectF(bx-5, by-5, 10, 10))
            p.setBrush(QBrush(qc("#c8a06040"))); p.setPen(Qt.NoPen)
            p.drawEllipse(QRectF(bx-2, by-2, 4, 4))

        px2, py2 = kx+28, ky+40
        p.setBrush(QBrush(qc("#6a5030"))); p.setPen(QPen(qc("#4a3018"), 1.5))
        p.drawRoundedRect(QRectF(px2-10, py2-18, 20, 22), 3, 3)
        p.setBrush(QBrush(qc("#8a6840"))); p.setPen(QPen(qc("#6a4820"), 1))
        p.drawEllipse(QRectF(px2-11, py2-20, 22, 8))
   
        p.setPen(QPen(qc("#a09080a0"), 1.5))
        for sx in (px2-5, px2, px2+5):
            path = QPainterPath()
            path.moveTo(sx, py2-22)
            path.cubicTo(sx+4, py2-30, sx-4, py2-36, sx, py2-40)
            p.drawPath(path)

        ex, ey = kx+105, ky+36
        p.setBrush(QBrush(qc("#5a4030"))); p.setPen(QPen(qc("#3a2818"), 1.5))
        p.drawRoundedRect(QRectF(ex-16, ey, 32, 44), 6, 6)
        p.setBrush(QBrush(qc("#c8a06080"))); p.setPen(Qt.NoPen)
        p.drawEllipse(QRectF(ex-8, ey+8, 16, 14))
        p.setBrush(QBrush(qc("#e8c88040"))); p.setPen(Qt.NoPen)
        p.drawEllipse(QRectF(ex-4, ey+11, 8, 8))
        p.setPen(QPen(qc("#c89060"), 1))
        p.drawLine(QPointF(ex, ey+24), QPointF(ex+12, ey+34))
        p.setBrush(QBrush(qc("#8a6040"))); p.setPen(QPen(qc("#5a3820"), 1))
        p.drawEllipse(QRectF(ex+9, ey+31, 8, 8))

        dx, dy2 = kx+152, ky+38
        p.setBrush(QBrush(qc("#e8dcc880"))); p.setPen(QPen(qc("#c8b890"), 1))
        p.drawRoundedRect(QRectF(dx-16, dy2, 32, 42), 4, 4)
    
        for ci, (cy2, cc) in enumerate([(dy2+28,"#c8a07a"),(dy2+20,"#e8c89a"),(dy2+12,"#f0d8b0")]):
            p.setBrush(QBrush(qc(cc))); p.setPen(Qt.NoPen)
            p.drawRoundedRect(QRectF(dx-11, cy2, 22, 10), 2, 2)
        p.setBrush(QBrush(qc("#c85a5a"))); p.setPen(Qt.NoPen)
        p.drawEllipse(QRectF(dx-3, dy2+6, 6, 6))

        shelf_y = ky + 93
        p.setBrush(QBrush(qc(WOOD_MID))); p.setPen(QPen(qc(WOOD_DARK), 1))
        p.drawRoundedRect(QRectF(kx+8, shelf_y, kw-16, 10), 2, 2)
        for jx, jc in [(kx+20,"#8b5e2e"),(kx+42,"#4a7c59"),(kx+64,"#c87a3a"),
                        (kx+88,"#7a5a9e"),(kx+112,"#5c3d1e"),(kx+136,"#2d5a3d"),(kx+160,"#b85c3a")]:
            p.setBrush(QBrush(qc(jc+"88"))); p.setPen(QPen(qc(jc), 1))
            p.drawRoundedRect(QRectF(jx-9, shelf_y-18, 18, 16), 3, 3)
            p.setBrush(QBrush(qc(jc))); p.setPen(Qt.NoPen)
            p.drawRoundedRect(QRectF(jx-7, shelf_y-22, 14, 6), 2, 2)

    def _entrance(self, p, W, H):
        dx, dy2, dw, dh = W//2-46, H-70, 92, 64
        p.setBrush(QBrush(qc(WOOD_DARK))); p.setPen(QPen(qc("#3a2008"), 1.5))
        p.drawRoundedRect(QRectF(dx-5, dy2-5, dw+10, dh+5), 4, 4)
        door_g = QLinearGradient(dx, dy2, dx+dw, dy2)
        door_g.setColorAt(0, qc("#8b6040")); door_g.setColorAt(0.5, qc("#a07848")); door_g.setColorAt(1, qc("#8b6040"))
        p.setBrush(QBrush(door_g)); p.setPen(QPen(qc(WOOD_DARK), 1))
        p.drawRoundedRect(QRectF(dx, dy2, dw, dh), 3, 3)
        p.setBrush(Qt.NoBrush); p.setPen(QPen(qc(WOOD_MID), 2))
        p.drawArc(QRectF(dx+8, dy2, dw-16, 30), 0, 180*16)
        p.setPen(QPen(qc(WOOD_DARK), 1))
        p.drawLine(QPointF(dx+dw//2, dy2+12), QPointF(dx+dw//2, dy2+dh-6))
        p.drawRoundedRect(QRectF(dx+5, dy2+14, dw//2-10, dh-24), 2, 2)
        p.drawRoundedRect(QRectF(dx+dw//2+5, dy2+14, dw//2-10, dh-24), 2, 2)
        p.setBrush(QBrush(qc(AMBER_WARM))); p.setPen(QPen(qc(GOLD_WARM), 1))
        p.drawEllipse(QRectF(dx+dw//2-12, dy2+36, 8, 8))
        p.drawEllipse(QRectF(dx+dw//2+4, dy2+36, 8, 8))
        p.setFont(QFont("Georgia", 7, QFont.Bold))
        p.setPen(qc(T_MID))
        p.drawText(QRectF(dx, dy2+50, dw, 14), Qt.AlignCenter, "ENTRANCE")

    def _wall_frames(self, p, H):
        for fy, fc in [(H*0.15, "#4a7c59"),(H*0.48, "#5c3d1e")]:
            frame = QPainterPath(); frame.addRoundedRect(QRectF(36, fy, 50, 64), 3, 3)
            p.fillPath(frame, qc("#e8dcc8"))
            p.setPen(QPen(qc(WOOD_DARK), 2)); p.setBrush(Qt.NoBrush); p.drawPath(frame)
            inner = QPainterPath(); inner.addRoundedRect(QRectF(41, fy+5, 40, 54), 2, 2)
            p.fillPath(inner, qc("#f5f0e8"))
            p.setPen(QPen(qc(fc), 1.5))
            for i in range(4):
                p.drawLine(QPointF(44, fy+12+i*10), QPointF(78, fy+18+i*8))
            p.setBrush(QBrush(qc(fc+"60"))); p.setPen(Qt.NoPen)
            p.drawEllipse(QRectF(50, fy+8, 22, 18))

    def _window(self, p, W, H):
        wx, wy, ww, wh = W-215, H*0.45, 28, 80
        p.setBrush(QBrush(qc("#e8f4e0"))); p.setPen(QPen(qc(WOOD_DARK), 2))
        p.drawRoundedRect(QRectF(wx, wy, ww, wh), 4, 4)
        p.setPen(QPen(qc(WOOD_MID), 1))
        p.drawLine(QPointF(wx+ww//2, wy), QPointF(wx+ww//2, wy+wh))
        p.drawLine(QPointF(wx, wy+wh//2), QPointF(wx+ww, wy+wh//2))
        gr = QRadialGradient(wx+ww//2, wy+wh//2, 80)
        gr.setColorAt(0, qc("#a8d8a030")); gr.setColorAt(1, qc("#00000000"))
        p.fillRect(int(wx-60), int(wy-20), 160, wh+40, gr)

    def _tables(self, p, W, H):
        cols   = 4
        rows_n = math.ceil(len(self.tables) / cols)
        px, py = 48, 52
        pw     = W - px - 222
        ph     = H - py - 82
        cw     = pw / cols; ch = ph / rows_n
        for i, tbl in enumerate(self.tables):
            cx = px + (i%cols)*cw + cw/2
            cy = py + (i//cols)*ch + ch/2
            self._table(p, tbl, cx, cy, cw*0.80, ch*0.74)

    def _table(self, p, tbl, cx, cy, cw, ch):
        tw = min(cw*0.46, 94); th = min(ch*0.42, 62)
        if tbl.is_occupied and tbl.occupied_by:
            rt = tbl.occupied_by.reservation_type
            hc = C_VIP if rt==ReservationType.VIP else C_URGENT if rt==ReservationType.URGENT else C_OCC
        else:
            hc = C_FREE
        color = qc(hc)

        shadow_g = QRadialGradient(cx, cy+th/2+5, tw*0.8)
        shadow_g.setColorAt(0, qc("#00000030")); shadow_g.setColorAt(1, qc("#00000000"))
        p.fillRect(int(cx-tw), int(cy+th/2-5), int(tw*2), 30, shadow_g)

        surf = QRadialGradient(cx, cy-th*0.1, max(tw,th)*0.7)
        surf.setColorAt(0.0, qc("#d4a870")); surf.setColorAt(0.5, qc("#c49060")); surf.setColorAt(1.0, qc("#a87040"))
        p.setBrush(QBrush(surf)); p.setPen(QPen(color, 2.5))
        p.drawEllipse(QRectF(cx-tw/2, cy-th/2, tw, th))

        p.setPen(QPen(qc("#b8804050"), 1))
        for off in (-8, -2, 4, 10):
            x1 = cx - tw/2 + 8; x2 = cx + tw/2 - 8; y = cy + off
            if cy-th/2 < y < cy+th/2:
                p.drawLine(QPointF(x1, y), QPointF(x2, y))


        p.setBrush(Qt.NoBrush); p.setPen(QPen(qc("#e8c09060"), 1))
        p.drawEllipse(QRectF(cx-tw/2+2, cy-th/2+2, tw-4, th-4))

        p.setBrush(Qt.NoBrush); p.setPen(QPen(color, 2))
        p.drawEllipse(QRectF(cx-tw/2, cy-th/2, tw, th))

        if tbl.is_occupied:
            for sp, al in [(12,15),(6,25)]:
                gc = QColor(color); gc.setAlpha(al)
                p.setPen(QPen(gc, 1)); p.setBrush(Qt.NoBrush)
                p.drawEllipse(QRectF(cx-tw/2-sp, cy-th/2-sp, tw+sp*2, th+sp*2))

       
        p.setFont(QFont("Georgia", 9, QFont.Bold))
        p.setPen(qc(T_DARK))
        p.drawText(QRectF(cx-tw/2, cy-th/2, tw, th*0.54), Qt.AlignCenter, f"T{tbl.table_id}")

        
        p.setFont(QFont("Helvetica", 7))
        p.setPen(qc(T_MID))
        sub = tbl.occupied_by.name.split()[0][:10] if (tbl.is_occupied and tbl.occupied_by) else f"{tbl.capacity} seats"
        p.drawText(QRectF(cx-tw/2, cy+2, tw, th*0.46), Qt.AlignCenter, sub)

        rx, ry = tw/2+20, th/2+20
        for s in range(tbl.capacity):
            ang = 2*math.pi*s/tbl.capacity - math.pi/2
            sx2 = cx + rx*math.cos(ang); sy2 = cy + ry*math.sin(ang)
         
            sg2 = QRadialGradient(sx2, sy2+4, 8)
            sg2.setColorAt(0, qc("#00000025")); sg2.setColorAt(1, qc("#00000000"))
            p.fillRect(int(sx2-10), int(sy2-6), 20, 20, sg2)
            
            ch_g = QRadialGradient(sx2-1, sy2-1, 7)
            ch_g.setColorAt(0, qc("#c8a070")); ch_g.setColorAt(1, qc("#a07840"))
            p.setBrush(QBrush(ch_g)); p.setPen(QPen(color, 1.5))
            p.drawEllipse(QRectF(sx2-7, sy2-7, 14, 14))
            p.setBrush(QBrush(qc("#e8d0b060")))
            p.setPen(Qt.NoPen)
            p.drawEllipse(QRectF(sx2-3.5, sy2-3.5, 7, 7))

class Panel(QWidget):
    def __init__(self, title="", accent=GREEN_DEEP, parent=None):
        super().__init__(parent)
        self.accent = accent
        root = QVBoxLayout(self); root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        if title:
            hdr = QWidget(); hdr.setFixedHeight(36)
            hl  = QHBoxLayout(hdr); hl.setContentsMargins(12,0,12,0)
            bar = QFrame(); bar.setFixedSize(3,15)
            bar.setStyleSheet(f"background:{accent}; border-radius:2px;")
            hl.addWidget(bar); hl.addSpacing(7)
            lb = QLabel(title)
            lb.setStyleSheet(f"color:{T_MID}; font-size:9px; font-weight:bold; letter-spacing:1.5px; background:transparent;")
            hl.addWidget(lb); hl.addStretch()
            root.addWidget(hdr)
            div = QFrame(); div.setFixedHeight(1); div.setStyleSheet(f"background:{BORDER};")
            root.addWidget(div)
        self.body = QWidget(); self.body.setStyleSheet("background:transparent;")
        self.bl   = QVBoxLayout(self.body)
        self.bl.setContentsMargins(10,8,10,10); self.bl.setSpacing(7)
        root.addWidget(self.body)

    def paintEvent(self, _):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        W, H = self.width(), self.height()
        path = QPainterPath(); path.addRoundedRect(QRectF(0,0,W,H), 10,10)
        grad = QLinearGradient(0,0,0,H)
        grad.setColorAt(0, qc(BG_CARD)); grad.setColorAt(1, qc(BG_GLASS))
        p.fillPath(path, grad)
        p.setPen(QPen(qc(BORDER_LIT), 1)); p.setBrush(Qt.NoBrush); p.drawPath(path)
        sh = QLinearGradient(0,0,W,0)
        sh.setColorAt(0, qc("#ffffff20")); sh.setColorAt(0.5, qc("#ffffff60")); sh.setColorAt(1, qc("#ffffff20"))
        p.fillRect(QRectF(1,1,W-2,1), sh); p.end()

    def add(self, w):    self.bl.addWidget(w)
    def addl(self, l):   self.bl.addLayout(l)
    def adds(self, n=5): self.bl.addSpacing(n)
  
class SemBar(QWidget):
    def __init__(self):
        super().__init__(); self.setFixedHeight(24)
        self.ratio = 1.0; self.label = "S = 8 / 8"

    def set_value(self, v, t):
        self.ratio = v/t if t else 0
        self.label = f"S = {v}  /  {t}"
        self.update()

    def paintEvent(self, _):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        W, H = self.width(), self.height()
        tp = QPainterPath(); tp.addRoundedRect(QRectF(0,0,W,H), 6,6)
        p.fillPath(tp, qc(BG_SURFACE))
        p.setPen(QPen(qc(BORDER), 1)); p.drawPath(tp)
        if self.ratio > 0:
            col = qc(C_FREE) if self.ratio>0.5 else qc(AMBER_WARM) if self.ratio>0.25 else qc(C_OCC)
            fl = QLinearGradient(0,0,W*self.ratio,0)
            fl.setColorAt(0, col.darker(115)); fl.setColorAt(1, col)
            fp = QPainterPath(); fp.addRoundedRect(QRectF(1,1,max((W-2)*self.ratio,10),H-2), 5,5)
            p.fillPath(fp, fl)
            sp = QPainterPath(); sp.addRoundedRect(QRectF(2,2,max((W-4)*self.ratio,6),(H-4)*0.4), 3,3)
            p.fillPath(sp, qc("#ffffff50"))
        p.setFont(QFont("Helvetica", 8, QFont.Bold))
        p.setPen(qc(CREAM) if self.ratio>0.3 else qc(GREEN_DEEP))
        p.drawText(QRectF(0,0,W,H), Qt.AlignCenter, self.label); p.end()

class StatChip(QWidget):
    def __init__(self, label, color):
        super().__init__(); self.setStyleSheet("background:transparent;")
        lay = QVBoxLayout(self); lay.setContentsMargins(8,6,8,6); lay.setSpacing(1)
        self._l = QLabel(label)
        self._l.setStyleSheet(f"color:{T_MUTED}; font-size:7px; font-weight:bold; letter-spacing:1px; background:transparent;")
        self._v = QLabel("—")
        self._v.setStyleSheet(f"color:{color}; font-size:17px; font-weight:bold; background:transparent;")
        lay.addWidget(self._l); lay.addWidget(self._v)

    def set(self, v): self._v.setText(str(v))

    def paintEvent(self, _):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath(); path.addRoundedRect(QRectF(0,0,self.width(),self.height()), 7,7)
        p.fillPath(path, qc(BG_SURFACE))
        p.setPen(QPen(qc(BORDER), 1)); p.drawPath(path); p.end()
 
class Header(QWidget):
    algo_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__(); self.setFixedHeight(74); self._algo = "FCFS"
        lay = QHBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)
        ac = QFrame(); ac.setFixedWidth(6)
        ac.setStyleSheet(f"background:qlineargradient(y1:0,y2:1,stop:0 {WOOD_LIGHT},stop:0.5 {WOOD_MID},stop:1 {WOOD_DARK});")
        lay.addWidget(ac)

        brand = QWidget(); brand.setStyleSheet("background:transparent;")
        bl = QVBoxLayout(brand); bl.setContentsMargins(20,10,20,10); bl.setSpacing(3)
        t1 = QLabel("Café  Lumière")
        t1.setStyleSheet(f"""
            color: {WOOD_DARK};
            font-family: Georgia;
            font-size: 26px;
            font-weight: bold;
            font-style: italic;
            background: transparent;
            letter-spacing: 5px;
        """)
        t2 = QLabel("✦   Hotel & Dining Reservation   ·   OS Process Simulator   ✦")
        t2.setStyleSheet(f"""
            color: {T_SOFT};
            font-family: Georgia;
            font-size: 9px;
            font-style: italic;
            background: transparent;
            letter-spacing: 2px;
        """)
        bl.addWidget(t1); bl.addWidget(t2)
        lay.addWidget(brand); lay.addStretch()

        ab = QWidget(); ab.setStyleSheet("background:transparent;")
        al = QVBoxLayout(ab); al.setContentsMargins(0,12,0,12); al.setSpacing(5)
        albl = QLabel("SCHEDULING ALGORITHM")
        albl.setStyleSheet(f"color:{T_MUTED}; font-size:7px; font-weight:bold; letter-spacing:2px; background:transparent;")
        albl.setAlignment(Qt.AlignCenter); al.addWidget(albl)
        brow = QHBoxLayout(); brow.setSpacing(3)
        self.b_fcfs = QPushButton("FCFS"); self.b_pri = QPushButton("Priority")
        for b in (self.b_fcfs, self.b_pri):
            b.setCursor(Qt.PointingHandCursor); b.setCheckable(True); brow.addWidget(b)
        self.b_fcfs.setChecked(True)
        self.b_fcfs.clicked.connect(lambda: self._set("FCFS"))
        self.b_pri.clicked.connect(lambda: self._set("Priority"))
        self._style(); al.addLayout(brow)
        lay.addWidget(ab); lay.addSpacing(16)

        ac2 = QFrame(); ac2.setFixedWidth(6)
        ac2.setStyleSheet(f"background:qlineargradient(y1:0,y2:1,stop:0 {WOOD_LIGHT},stop:0.5 {WOOD_MID},stop:1 {WOOD_DARK});")
        lay.addWidget(ac2)

    def paintEvent(self, _):
        p = QPainter(self); W, H = self.width(), self.height()
        grad = QLinearGradient(0,0,0,H)
        grad.setColorAt(0, qc("#faf5ec")); grad.setColorAt(1, qc("#f0e8d8"))
        p.fillRect(0,0,W,H, grad)
        p.setPen(QPen(qc(BORDER_LIT), 1))
        p.drawLine(0, H-1, W, H-1); p.end()

    def _set(self, v):
        self._algo = v; self.b_fcfs.setChecked(v=="FCFS"); self.b_pri.setChecked(v=="Priority")
        self._style(); self.algo_changed.emit(v)

    def _style(self):
        on  = f"""QPushButton{{
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {GREEN_DEEP},stop:1 {GREEN_MID});
            color:{CREAM}; border:none; border-radius:7px; padding:6px 18px;
            font-family:Georgia; font-size:10px; font-weight:bold; letter-spacing:1px;
        }}"""
        off = f"""QPushButton{{
            background:{BG_SURFACE}; color:{T_SOFT};
            border:1px solid {BORDER}; border-radius:7px; padding:6px 18px;
            font-family:Helvetica; font-size:10px; letter-spacing:1px;
        }}QPushButton:hover{{color:{T_DARK}; border-color:{GREEN_MID};}}"""
        self.b_fcfs.setStyleSheet(on if self.b_fcfs.isChecked() else off)
        self.b_pri.setStyleSheet(on  if self.b_pri.isChecked()  else off)

    def get_algo(self): return self._algo

def mk_inp(default=""):
    e = QLineEdit(default)
    e.setStyleSheet(f"""
        QLineEdit {{
            background: {INPUT_BG};
            color: {INPUT_TEXT};
            border: 1px solid {INPUT_BORDER};
            border-radius: 7px;
            padding: 7px 12px;
            font-family: Helvetica;
            font-size: 10px;
        }}
        QLineEdit:focus {{
            border: 1px solid {INPUT_FOCUS};
            background: #ffffff;
        }}
    """)
    return e

def mk_btn(text):
    b = QPushButton(text); b.setCursor(Qt.PointingHandCursor)
    b.setStyleSheet(f"""
        QPushButton {{
            background: {BTN_BG};
            color: {BTN_TEXT};
            border: 1px solid {BTN_BORDER};
            border-radius: 7px;
            padding: 8px 14px;
            font-family: Georgia;
            font-size: 10px;
            font-weight: bold;
            letter-spacing: 0.8px;
        }}
        QPushButton:hover {{
            background: {BTN_HOVER};
            color: {CREAM};
        }}
        QPushButton:pressed {{
            background: {GREEN_DEEP};
            color: {CREAM};
        }}
    """)
    return b

def mk_radio(text, color):
    rb = QRadioButton(text)
    rb.setStyleSheet(f"""
        QRadioButton {{
            color: {color};
            font-family: Helvetica;
            font-size: 10px;
            font-weight: bold;
            background: transparent;
            spacing: 6px; padding: 3px 8px;
        }}
        QRadioButton::indicator {{
            width: 12px; height: 12px;
            border-radius: 6px;
            border: 2px solid {color};
            background: {BG_SURFACE};
        }}
        QRadioButton::indicator:checked {{ background: {color}; }}
    """)
    return rb

def mk_div():
    f = QFrame(); f.setFrameShape(QFrame.HLine); f.setFixedHeight(1)
    f.setStyleSheet(f"background:{BORDER}; border:none;"); return f

def field_col(lbl_txt, widget):
    col = QVBoxLayout(); col.setSpacing(3)
    lb  = QLabel(lbl_txt)
    lb.setStyleSheet(f"color:{T_MUTED}; font-size:7px; font-weight:bold; letter-spacing:1.5px; background:transparent;")
    col.addWidget(lb); col.addWidget(widget); return col

def cap_lbl(txt):
    l = QLabel(txt)
    l.setStyleSheet(f"color:{T_SOFT}; font-size:7px; font-weight:bold; letter-spacing:2px; background:transparent;")
    return l


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Café Lumière  —  Reservation OS Simulator")
        self.resize(1540, 940); self.setMinimumSize(1280, 820)
        self.setStyleSheet(f"QMainWindow{{background:{BG_APP};}}")

        self.tables    = self._make_tables()
        self.semaphore = CountingSemaphore(len(self.tables))
        self.scheduler = Scheduler(self.tables, self.semaphore)
        self._cust_id  = 0

        cw = QWidget(); cw.setStyleSheet(f"background:{BG_APP};")
        self.setCentralWidget(cw)
        root = QVBoxLayout(cw); root.setContentsMargins(0,0,0,0); root.setSpacing(0)

        self.hdr = Header()
        self.hdr.algo_changed.connect(self._on_algo_change)
        root.addWidget(self.hdr)
        root.addWidget(mk_div())

        body = QWidget(); body.setStyleSheet(f"background:{BG_APP};")
        bl   = QHBoxLayout(body); bl.setContentsMargins(8,8,8,8); bl.setSpacing(8)
        root.addWidget(body, stretch=1)

        floor_card = Panel("DINING FLOOR PLAN  —  LIVE VIEW", GREEN_DEEP)
        leg = QHBoxLayout(); leg.setSpacing(4)
        for txt, col in [("● Available",C_FREE),("● Occupied",C_OCC),("● VIP",C_VIP),("● Urgent",C_URGENT)]:
            l = QLabel(txt)
            l.setStyleSheet(f"color:{col}; font-size:9px; font-weight:bold; background:transparent; padding-right:10px;")
            leg.addWidget(l)
        leg.addStretch()
        floor_card.addl(leg)
        self.floor = FloorCanvas(self.tables)
        floor_card.bl.addWidget(self.floor, stretch=1)
        floor_card.bl.setContentsMargins(10,6,10,10)
        shadow(floor_card, 20, 5, "#00000020")
        bl.addWidget(floor_card, stretch=1)

        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setFixedWidth(320)
        right_scroll.setStyleSheet(f"""
            QScrollArea {{ background:transparent; border:none; }}
            QScrollBar:vertical {{
                background:{BG_SURFACE}; width:4px; border-radius:2px; margin:0;
            }}
            QScrollBar::handle:vertical {{ background:{BORDER_LIT}; border-radius:2px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0; }}
        """)
        right_widget = QWidget(); right_widget.setStyleSheet(f"background:{BG_APP};")
        rl = QVBoxLayout(right_widget); rl.setContentsMargins(0,0,4,0); rl.setSpacing(8)
        right_scroll.setWidget(right_widget)
        bl.addWidget(right_scroll)

        self._build_form(rl)
        self._build_semaphore(rl)
        self._build_queue(rl)
        self._build_log(rl)
        rl.addStretch()

        self._build_statusbar(root)

    def _make_tables(self):
        return [Table(tid, cap) for tid, cap in
                [(1,2),(2,2),(3,4),(4,4),(5,4),(6,6),(7,6),(8,8)]]

    def _build_form(self, pl):
        card = Panel("NEW RESERVATION  —  GUEST PROCESS", GREEN_DEEP)

        row1 = QHBoxLayout(); row1.setSpacing(8)
        self.i_name   = mk_inp("Ahmed Khan")
        self.i_guests = mk_inp("4"); self.i_guests.setFixedWidth(76)
        row1.addLayout(field_col("CUSTOMER NAME", self.i_name))
        row1.addLayout(field_col("GUESTS", self.i_guests))
        card.addl(row1)

        row2 = QHBoxLayout(); row2.setSpacing(8)
        self.i_arrival = mk_inp("7:30 PM")
        self.i_dur     = mk_inp("45")
        row2.addLayout(field_col("ARRIVAL TIME", self.i_arrival))
        row2.addLayout(field_col("DURATION (MIN)", self.i_dur))
        card.addl(row2)

        card.add(cap_lbl("RESERVATION TYPE"))
        tr = QHBoxLayout(); tr.setSpacing(2)
        self.rg   = QButtonGroup()
        self.rb_n = mk_radio("Normal", GREEN_DEEP)
        self.rb_v = mk_radio("VIP",    C_VIP)
        self.rb_u = mk_radio("Urgent", C_URGENT)
        self.rb_n.setChecked(True)
        for rb in (self.rb_n, self.rb_v, self.rb_u):
            self.rg.addButton(rb); tr.addWidget(rb)
        tr.addStretch(); card.addl(tr)

        card.add(cap_lbl("ACTIONS"))
        br1 = QHBoxLayout(); br1.setSpacing(6)
        self.b_reserve = mk_btn("Reserve")
        self.b_release = mk_btn("Release Table")
        br1.addWidget(self.b_reserve); br1.addWidget(self.b_release)
        card.addl(br1)

        br2 = QHBoxLayout(); br2.setSpacing(6)
        self.b_report  = mk_btn("Summary Report")
        self.b_reset   = mk_btn("Reset")
        br2.addWidget(self.b_report); br2.addWidget(self.b_reset)
        card.addl(br2)

        self.b_reserve.clicked.connect(self._on_reserve)
        self.b_release.clicked.connect(self._on_release_dialog)
        self.b_report.clicked.connect(self._show_report)
        self.b_reset.clicked.connect(self._on_reset)
        shadow(card, 16, 4, "#00000018"); pl.addWidget(card)

    def _build_semaphore(self, pl):
        card = Panel("SEMAPHORE  —  RESOURCE CONTROLLER", WOOD_MID)
        nums = QHBoxLayout(); nums.setSpacing(5)
        self.sc_t = StatChip("TOTAL",     T_DARK)
        self.sc_a = StatChip("AVAILABLE", GREEN_DEEP)
        self.sc_o = StatChip("OCCUPIED",  C_OCC)
        for sc in (self.sc_t, self.sc_a, self.sc_o): nums.addWidget(sc)
        card.addl(nums)
        card.add(cap_lbl("SEMAPHORE  S  →"))
        self.sem_bar = SemBar(); card.add(self.sem_bar)
        self.lbl_op = QLabel("Last operation: —")
        self.lbl_op.setWordWrap(True)
        self.lbl_op.setStyleSheet(f"color:{GREEN_DEEP}; font-family:Courier New; font-size:9px; background:{BG_SURFACE}; border-radius:5px; padding:5px 8px; border:1px solid {BORDER};")
        card.add(self.lbl_op)
        shadow(card, 14, 3, "#00000015"); pl.addWidget(card)

    def _build_queue(self, pl):
        card = Panel("WAITING QUEUE  —  READY QUEUE", AMBER_WARM)
        card.bl.setContentsMargins(8,6,8,8)
        self.q_widget = QWidget(); self.q_widget.setStyleSheet("background:transparent;")
        self.q_layout = QVBoxLayout(self.q_widget)
        self.q_layout.setContentsMargins(0,0,0,0); self.q_layout.setSpacing(4)
        self.q_layout.addStretch()
        card.bl.addWidget(self.q_widget)
        shadow(card, 14, 3, "#00000015"); pl.addWidget(card)

    def _build_log(self, pl):
        card = Panel("OS EVENT LOG  —  P( ) / V( ) OPERATIONS", GREEN_MID)
        card.bl.setContentsMargins(8,6,8,8)
        self.log_box = QTextEdit(); self.log_box.setReadOnly(True)
        self.log_box.setFixedHeight(175)
        self.log_box.setStyleSheet(f"""
            QTextEdit {{
                background:{BG_SURFACE}; color:{GREEN_DEEP};
                font-family:Courier New; font-size:9px;
                border:1px solid {BORDER}; border-radius:6px; padding:7px;
            }}
            QScrollBar:vertical {{
                background:{BG_GLASS}; width:4px; border-radius:2px;
            }}
            QScrollBar::handle:vertical {{ background:{BORDER_LIT}; border-radius:2px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0; }}
        """)
        card.bl.addWidget(self.log_box)
        shadow(card, 14, 3, "#00000015"); pl.addWidget(card)

    def _build_statusbar(self, rl):
        rl.addWidget(mk_div())
        self.status = QLabel("  ✦  Café Lumière  —  Add a reservation to begin.")
        self.status.setStyleSheet(f"background:{BG_CARD}; color:{T_MUTED}; font-family:Georgia; font-size:9px; font-style:italic; letter-spacing:1px; padding:6px 16px;")
        rl.addWidget(self.status)

    def _refresh_all(self):
        self.floor.refresh()
        s = self.semaphore
        self.sc_t.set(s.total); self.sc_a.set(s.value); self.sc_o.set(s.occupied)
        self.lbl_op.setText(f"Last operation:  {s.last_op()}")
        self.sem_bar.set_value(s.value, s.total)
        self._refresh_queue(); self._refresh_log()

    def _refresh_queue(self):
        while self.q_layout.count() > 1:
            it = self.q_layout.takeAt(0)
            if it.widget(): it.widget().deleteLater()
        queue = self.scheduler.waiting_queue
        if not queue:
            e = QLabel("  No customers waiting")
            e.setStyleSheet(f"color:{T_MUTED}; font-size:9px; background:transparent; padding:6px; font-style:italic;")
            self.q_layout.insertWidget(0, e); return
        algo = self.hdr.get_algo()
        sq   = (sorted(queue, key=lambda c:(c.priority,c.arrival_order)) if algo=="Priority"
                else sorted(queue, key=lambda c:c.arrival_order))
        for idx, cu in enumerate(sq):
            row = QWidget()
            row.setStyleSheet(f"background:{BG_GLASS}; border:1px solid {BORDER}; border-radius:7px;")
            rl2 = QHBoxLayout(row); rl2.setContentsMargins(7,4,9,4); rl2.setSpacing(6)
            pos = QLabel(f"#{idx+1}")
            pos.setStyleSheet(f"background:{'qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 '+GREEN_DEEP+',stop:1 '+GREEN_MID+')' if idx==0 else BG_SURFACE};color:{CREAM if idx==0 else T_MUTED};font-size:8px;font-weight:bold;border-radius:4px;padding:2px 6px;")
            rl2.addWidget(pos)
            pc = {"Normal":GREEN_DEEP,"VIP":C_VIP,"Urgent":C_URGENT}[cu.priority_label]
            pri = QLabel(cu.priority_label)
            pri.setStyleSheet(f"background:{pc}20;color:{pc};font-size:8px;font-weight:bold;border:1px solid {pc}50;border-radius:4px;padding:2px 6px;")
            rl2.addWidget(pri)
            nm = QLabel(cu.name)
            nm.setStyleSheet(f"color:{T_DARK}; font-size:10px; background:transparent;")
            rl2.addWidget(nm)
            info = QLabel(f"👥{cu.num_guests}")
            info.setStyleSheet(f"color:{T_SOFT}; font-size:9px; background:transparent;")
            rl2.addWidget(info); rl2.addStretch()
            self.q_layout.insertWidget(idx, row)

    def _refresh_log(self):
        self.log_box.setPlainText("\n".join(self.scheduler.log[-60:]))
        sb = self.log_box.verticalScrollBar(); sb.setValue(sb.maximum())

    def _on_reserve(self):
        name = self.i_name.text().strip(); guests = self.i_guests.text().strip()
        arrival = self.i_arrival.text().strip(); dur = self.i_dur.text().strip()
        if not name:       self._msg("Customer name cannot be empty."); return
        try:    guests=int(guests); assert guests>=1
        except: self._msg("Guests must be a positive number."); return
        try:    dur=int(dur); assert dur>=1
        except: self._msg("Duration must be a positive number."); return
        if not arrival:    self._msg("Please enter arrival time."); return
        cb    = self.rg.checkedButton()
        rtype = {"Normal":ReservationType.NORMAL,"VIP":ReservationType.VIP,"Urgent":ReservationType.URGENT}[cb.text() if cb else "Normal"]
        self._cust_id += 1
        cust  = Customer(self._cust_id, name, guests, arrival, dur, rtype)
        _, msg = self.scheduler.add_customer(cust)
        self.status.setText(f"  ✦  {msg}"); self._refresh_all()

    def _on_release_dialog(self):
        occ = [t for t in self.tables if t.is_occupied]
        if not occ: self._msg("No tables are currently occupied."); return
        dlg = QDialog(self); dlg.setWindowTitle("Release Table"); dlg.setFixedSize(480, 400)
        dlg.setStyleSheet(f"QDialog{{background:{BG_APP};}} QLabel{{background:transparent;}}")
        lay = QVBoxLayout(dlg); lay.setContentsMargins(22,22,22,22); lay.setSpacing(10)
        tl = QLabel("Select table to release")
        tl.setStyleSheet(f"color:{T_DARK}; font-family:Georgia; font-size:14px; font-weight:bold;")
        lay.addWidget(tl)
        grp = QButtonGroup(dlg); rbs = []
        for t in occ:
            nm = t.occupied_by.name if t.occupied_by else "?"
            pt = t.occupied_by.priority_label if t.occupied_by else ""
            pc = {"Normal":GREEN_DEEP,"VIP":C_VIP,"Urgent":C_URGENT}.get(pt, T_DARK)
            card = QWidget()
            card.setStyleSheet(f"background:{BG_GLASS}; border:1px solid {BORDER}; border-radius:8px;")
            cl = QHBoxLayout(card); cl.setContentsMargins(14,10,14,10)
            rb = QRadioButton(f"Table {t.table_id}  ({t.capacity} seats)  —  {nm}  [{pt}]")
            rb.setStyleSheet(f"QRadioButton{{color:{pc};font-size:10px;background:transparent;spacing:8px;}}QRadioButton::indicator{{width:13px;height:13px;border-radius:7px;border:2px solid {pc};background:{BG_SURFACE};}}QRadioButton::indicator:checked{{background:{pc};}}")
            rb.table_ref = t; grp.addButton(rb); rbs.append(rb); cl.addWidget(rb); lay.addWidget(card)
        if rbs: rbs[0].setChecked(True)
        def do():
            for rb in rbs:
                if rb.isChecked():
                    msgs = self.scheduler.release_table(rb.table_ref)
                    self.status.setText(f"  ✦  {' | '.join(msgs)}"); break
            dlg.accept(); self._refresh_all()
        b = mk_btn("Confirm Release"); b.clicked.connect(do)
        lay.addWidget(b, alignment=Qt.AlignCenter); dlg.exec_()

    def _on_algo_change(self, v):
        self.scheduler.algorithm = v; self._refresh_queue()
        self.status.setText(f"  ✦  Algorithm switched to {v}.")

    def _on_reset(self):
        from PyQt5.QtWidgets import QMessageBox
        if QMessageBox.question(self,"Reset","Reset the entire simulation?",
                                QMessageBox.Yes|QMessageBox.No) != QMessageBox.Yes: return
        self.tables = self._make_tables(); self.semaphore = CountingSemaphore(len(self.tables))
        self.scheduler = Scheduler(self.tables, self.semaphore); self._cust_id = 0
        self.floor.tables = self.tables; self.status.setText("  ✦  Simulation reset.")
        self._refresh_all()

    def _show_report(self):
        stats   = self.scheduler.get_stats()
        history = self.scheduler.seat_history

        dlg = QDialog(self)
        dlg.setWindowTitle("Summary Report  —  Café Lumière")
        dlg.setFixedSize(760, 820)
        dlg.setStyleSheet(f"QDialog{{background:{BG_APP};}} QLabel{{background:transparent;}}")

        
        outer = QVBoxLayout(dlg); outer.setContentsMargins(0,0,0,0); outer.setSpacing(0)
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea{{background:transparent; border:none;}}
            QScrollBar:vertical{{background:{BG_SURFACE}; width:5px; border-radius:3px;}}
            QScrollBar::handle:vertical{{background:{BORDER_LIT}; border-radius:3px;}}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical{{height:0;}}
        """)
        content = QWidget(); content.setStyleSheet(f"background:{BG_APP};")
        lay = QVBoxLayout(content); lay.setContentsMargins(24,20,24,20); lay.setSpacing(8)
        scroll.setWidget(content); outer.addWidget(scroll)

        
        t1 = QLabel("Café  Lumière")
        t1.setStyleSheet(f"color:{WOOD_DARK}; font-family:Georgia; font-size:24px; font-weight:bold; font-style:italic; letter-spacing:4px;")
        t1.setAlignment(Qt.AlignCenter)
        t2 = QLabel("✦   Simulation Summary Report   ✦")
        t2.setStyleSheet(f"color:{T_SOFT}; font-family:Georgia; font-size:10px; font-style:italic; letter-spacing:3px;")
        t2.setAlignment(Qt.AlignCenter)
        lay.addWidget(t1); lay.addWidget(t2); lay.addSpacing(4)

        
        stat_lbl = cap_lbl("SIMULATION STATISTICS"); lay.addWidget(stat_lbl)
        grid = QWidget(); grid.setStyleSheet("background:transparent;")
        gl   = QHBoxLayout(grid); gl.setContentsMargins(0,0,0,0); gl.setSpacing(8)

        def stat_chip(label, value, color):
            w = QWidget()
            w.setStyleSheet(f"background:{BG_GLASS}; border:1px solid {BORDER}; border-radius:8px;")
            wl = QVBoxLayout(w); wl.setContentsMargins(12,8,12,8); wl.setSpacing(2)
            lbl = QLabel(label); lbl.setStyleSheet(f"color:{T_MUTED}; font-size:7px; font-weight:bold; letter-spacing:1px;")
            val = QLabel(str(value)); val.setStyleSheet(f"color:{color}; font-size:20px; font-weight:bold;")
            wl.addWidget(lbl); wl.addWidget(val); return w

        gl.addWidget(stat_chip("TOTAL",          stats["total_customers"],  T_DARK))
        gl.addWidget(stat_chip("SERVED",         stats["served"],           GREEN_DEEP))
        gl.addWidget(stat_chip("SEATED NOW",     stats["currently_seated"], GREEN_MID))
        gl.addWidget(stat_chip("WAITING",        stats["waiting"],          AMBER_WARM))
        gl.addWidget(stat_chip("REJECTED",       stats["rejected"],         C_OCC))
        gl.addWidget(stat_chip("SEMAPHORE  S",   stats["semaphore_value"],  C_VIP))
        lay.addWidget(grid)

        
        algo_row = QWidget()
        algo_row.setStyleSheet(f"background:{BG_GLASS}; border:1px solid {BORDER}; border-radius:8px;")
        arl = QHBoxLayout(algo_row); arl.setContentsMargins(16,10,16,10)
        al = QLabel("Algorithm Used")
        al.setStyleSheet(f"color:{T_SOFT}; font-size:10px;"); al.setFixedWidth(200)
        av = QLabel(self.hdr.get_algo())
        av.setStyleSheet(f"color:{C_VIP}; font-size:13px; font-weight:bold;")
        av.setAlignment(Qt.AlignRight)
        arl.addWidget(al); arl.addWidget(av)
        lay.addWidget(algo_row)

        
        lay.addSpacing(4)
        gantt_lbl = cap_lbl("GANTT CHART  —  TABLE ALLOCATION TIMELINE")
        lay.addWidget(gantt_lbl)

        gantt_card = QWidget()
        gantt_card.setStyleSheet(f"background:{BG_GLASS}; border:1px solid {BORDER}; border-radius:8px;")
        gcl = QVBoxLayout(gantt_card); gcl.setContentsMargins(14,12,14,12); gcl.setSpacing(6)

        if not history:
            empty = QLabel("  No data yet — add and serve customers to see the Gantt chart.")
            empty.setStyleSheet(f"color:{T_MUTED}; font-size:9px; font-style:italic;")
            gcl.addWidget(empty)
        else:
            
            sorted_h = sorted(history, key=lambda x: x["order"])
            max_dur  = max(h["duration"] for h in sorted_h) if sorted_h else 1

            hdr_row = QWidget(); hdr_row.setStyleSheet("background:transparent;")
            hrl = QHBoxLayout(hdr_row); hrl.setContentsMargins(0,0,0,0); hrl.setSpacing(0)
            name_h = QLabel("Customer"); name_h.setFixedWidth(110)
            name_h.setStyleSheet(f"color:{T_MUTED}; font-size:8px; font-weight:bold; letter-spacing:1px;")
            tbl_h  = QLabel("Table"); tbl_h.setFixedWidth(48)
            tbl_h.setStyleSheet(f"color:{T_MUTED}; font-size:8px; font-weight:bold;")
            bar_h  = QLabel("Duration (proportional to dining time)  →")
            bar_h.setStyleSheet(f"color:{T_MUTED}; font-size:8px; font-weight:bold;")
            hrl.addWidget(name_h); hrl.addWidget(tbl_h); hrl.addWidget(bar_h)
            gcl.addWidget(hdr_row)

           
            div = QFrame(); div.setFrameShape(QFrame.HLine)
            div.setStyleSheet(f"background:{BORDER}; max-height:1px;")
            gcl.addWidget(div)

            
            p_colors = {"Normal": GREEN_DEEP, "VIP": C_VIP, "Urgent": C_URGENT}

           
            for h in sorted_h:
                col   = p_colors.get(h["priority"], GREEN_MID)
                ratio = h["duration"] / max_dur

                row_w = QWidget(); row_w.setStyleSheet("background:transparent;")
                rl3   = QHBoxLayout(row_w); rl3.setContentsMargins(0,2,0,2); rl3.setSpacing(6)

                name_l = QLabel(h["name"][:12])
                name_l.setFixedWidth(104)
                name_l.setStyleSheet(f"color:{T_DARK}; font-size:9px; font-weight:bold;")
                rl3.addWidget(name_l)

            
                tbl_l = QLabel(f"T{h['table_id']}")
                tbl_l.setFixedWidth(28)
                tbl_l.setStyleSheet(f"""
                    background:{col}; color:{CREAM}; font-size:8px;
                    font-weight:bold; border-radius:4px; padding:2px 4px;
                """)
                rl3.addWidget(tbl_l)

                bar_container = QWidget(); bar_container.setStyleSheet("background:transparent;")
                bar_container.setFixedHeight(22)
                bar_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

                class GanttBar(QWidget):
                    def __init__(self, ratio, color, duration, parent=None):
                        super().__init__(parent)
                        self._r  = ratio
                        self._c  = color
                        self._d  = duration
                        self.setFixedHeight(22)
                        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                    def paintEvent(self, _):
                        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
                        W, H = self.width(), self.height()
                        # Background track
                        path = QPainterPath(); path.addRoundedRect(QRectF(0,2,W,H-4), 4,4)
                        p.fillPath(path, qc(BG_SURFACE))
                        # Filled bar
                        fw = max(int(W * self._r), 28)
                        fill = QPainterPath(); fill.addRoundedRect(QRectF(0,2,fw,H-4), 4,4)
                        grad = QLinearGradient(0,0,fw,0)
                        base = QColor(self._c)
                        grad.setColorAt(0, base.darker(120))
                        grad.setColorAt(1, base)
                        p.fillPath(fill, grad)
                        # Shine
                        shine = QPainterPath(); shine.addRoundedRect(QRectF(1,3,fw-2,(H-6)*0.45), 3,3)
                        p.fillPath(shine, qc("#ffffff30"))
                        # Duration text
                        p.setFont(QFont("Helvetica", 8, QFont.Bold))
                        p.setPen(qc(CREAM))
                        p.drawText(QRectF(4,0,fw-6,H), Qt.AlignVCenter|Qt.AlignLeft, f"{self._d} min")
                        p.end()

                gb = GanttBar(ratio, col, h["duration"])
                rl3.addWidget(gb)

               
                pri_l = QLabel(h["priority"])
                pri_l.setFixedWidth(52)
                pri_l.setStyleSheet(f"""
                    background:{col}22; color:{col};
                    font-size:7px; font-weight:bold;
                    border:1px solid {col}50; border-radius:4px;
                    padding:2px 4px;
                """)
                pri_l.setAlignment(Qt.AlignCenter)
                rl3.addWidget(pri_l)

                gcl.addWidget(row_w)

        lay.addWidget(gantt_card)

        
        lay.addSpacing(4)
        comp_lbl = cap_lbl("ALGORITHM COMPARISON OUTPUT"); lay.addWidget(comp_lbl)

        comp_card = QWidget()
        comp_card.setStyleSheet(f"background:{BG_GLASS}; border:1px solid {BORDER}; border-radius:8px;")
        ccl = QVBoxLayout(comp_card); ccl.setContentsMargins(0,0,0,8)

       
        hdr_bg = QWidget()
        hdr_bg.setStyleSheet(f"background:{WOOD_DARK}; border-radius:7px 7px 0 0;")
        hbl = QHBoxLayout(hdr_bg); hbl.setContentsMargins(14,8,14,8)
        for txt, w in [("Algorithm",100),("Avg Wait Time",130),("Customers Served",150),("Fairness",120)]:
            lh = QLabel(txt); lh.setFixedWidth(w)
            lh.setStyleSheet(f"color:{CREAM}; font-size:9px; font-weight:bold; letter-spacing:1px;")
            hbl.addWidget(lh)
        hbl.addStretch()
        ccl.addWidget(hdr_bg)

        total_served = stats["served"]
        for alg, col, fairness in [
            ("FCFS",     GREEN_DEEP, "High  —  No starvation"),
            ("Priority", C_VIP,      "VIP-Focused  —  Starvation risk for Normal"),
        ]:
            rw = QWidget()
            rw.setStyleSheet(f"background:{'#f5f0e8' if alg=='FCFS' else BG_GLASS};")
            rwl = QHBoxLayout(rw); rwl.setContentsMargins(14,8,14,8)
            for txt, w in [
                (alg,                     100),
                ("N/A (simulated)",        130),
                (str(total_served),        150),
                (fairness,                 120),
            ]:
                lv = QLabel(txt); lv.setFixedWidth(w)
                lv.setStyleSheet(f"color:{col}; font-size:9px; font-weight:bold;")
                rwl.addWidget(lv)
            rwl.addStretch()
            ccl.addWidget(rw)

        lay.addWidget(comp_card)

        if self.scheduler.served:
            lay.addSpacing(4)
            sl = cap_lbl("COMPLETED GUESTS"); lay.addWidget(sl)
            for cu in self.scheduler.served:
                l = QLabel(f"  ✔  {cu.name}  ·  {cu.priority_label}  ·  "
                           f"{cu.num_guests} guests  ·  {cu.dining_duration} min")
                l.setStyleSheet(f"color:{GREEN_DEEP}; font-size:9px;")
                lay.addWidget(l)

        lay.addSpacing(8)
        b = mk_btn("Close"); b.clicked.connect(dlg.accept)
        lay.addWidget(b, alignment=Qt.AlignCenter)
        dlg.exec_()

    def _msg(self, txt):
        from PyQt5.QtWidgets import QMessageBox
        mb = QMessageBox(self); mb.setText(txt)
        mb.setStyleSheet(f"QMessageBox{{background:{BG_APP};color:{T_DARK};}}QLabel{{color:{T_DARK};background:transparent;}}QPushButton{{background:{BTN_BG};color:{BTN_TEXT};border:1px solid {BTN_BORDER};border-radius:6px;padding:5px 18px;font-weight:bold;}}")
        mb.exec_()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())