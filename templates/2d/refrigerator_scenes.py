"""冰箱分集 · 纪录片手绘风 2D。"""

from __future__ import annotations

import math
import random
from typing import Callable

from PIL import Image, ImageDraw

from pipeline.fonts import load_cjk_font as _font

PAPER = (248, 245, 238)
WALL = (242, 238, 230)
FLOOR = (218, 214, 206)
INK = (38, 36, 34)
MUTED = (110, 105, 98)
ACCENT = (180, 75, 45)
COLD = (70, 140, 185)
COLD_LT = (180, 215, 235)
HOT = (195, 90, 55)
HOT_LT = (240, 190, 150)
LINE = (180, 175, 168)
WHITE = (252, 250, 246)
METAL = (168, 172, 178)
METAL_DK = (105, 110, 118)
BODY = (235, 238, 242)
COPPER = (175, 115, 65)
GREEN = (80, 160, 110)


FONT_HERO, FONT_L, FONT_M, FONT_S, FONT_XS = _font(62, True), _font(44, True), _font(34), _font(28), _font(24)


def _clamp01(t): return max(0.0, min(1.0, t))
def _ease(t): t=_clamp01(t); return t*t*(3-2*t)
def _spring(t, start=0.0, dur=0.3):
    if t < start: return 0.0
    p=_clamp01((t-start)/dur); return 1-math.exp(-6*p)*math.cos(p*math.pi*2.5)
def _lerp(a,b,t): return a+(b-a)*_clamp01(t)
def _scene_t(t,a,b):
    if t<=a: return 0.0
    if t>=b: return 1.0
    return (t-a)/(b-a)
def _pulse(ts, speed=2.5, lo=0.85, hi=1.0): return lo+(hi-lo)*(0.5+0.5*math.sin(ts*speed*math.tau))
def _wobble(x,y,seed,amp=1.2): return x+math.sin(seed*1.7)*amp, y+math.cos(seed*2.3)*amp
def _cam_drift(ts, ax=5.0, ay=3.0): return math.sin(ts*0.7)*ax, math.cos(ts*0.55)*ay


def _paper_bg(w,h,seed=7):
    img=Image.new("RGB",(w,h),PAPER); d=ImageDraw.Draw(img)
    d.rectangle((0,0,w,int(h*0.62)),fill=WALL); d.rectangle((0,int(h*0.62),w,h),fill=FLOOR)
    d.line((0,int(h*0.62),w,int(h*0.62)),fill=LINE,width=2)
    rng=random.Random(seed); px=img.load()
    for _ in range(int(w*h*0.008)):
        x,y=rng.randint(0,w-1),rng.randint(0,h-1); r,g,b=px[x,y]; n=rng.randint(-5,5)
        px[x,y]=(max(0,min(255,r+n)),max(0,min(255,g+n)),max(0,min(255,b+n)))
    return img


def _sketch_line(d,p1,p2,color=INK,width=2,seed=0):
    x1,y1=p1; x2,y2=p2; steps=max(int(math.hypot(x2-x1,y2-y1)/12),2); pts=[]
    for i in range(steps+1):
        f=i/steps; x,y=_lerp(x1,x2,f),_lerp(y1,y2,f); pts.append(_wobble(x,y,seed+i,0.8))
    for i in range(len(pts)-1): d.line((pts[i],pts[i+1]),fill=color,width=width)


def _callout(d, tip, label, text, color=INK, alpha=1.0):
    if alpha<=0.01: return
    _sketch_line(d, tip, label, color, 2, int(tip[0]+tip[1]))
    d.ellipse((tip[0]-5,tip[1]-5,tip[0]+5,tip[1]+5),fill=color)
    d.text(label, text, font=FONT_S, fill=(*color,int(255*_clamp01(alpha))), anchor="lm")


def _fade_text(d,xy,text,font,color,alpha,anchor="mm",dy=0.0):
    if alpha<=0.01: return
    d.text((xy[0],xy[1]+dy), text, font=font, fill=(*color,int(255*_clamp01(alpha))), anchor=anchor)


def _ken_badge(d,y,alpha=1.0,scale=1.0):
    if alpha<=0: return
    a=int(255*_clamp01(alpha)); bw=int(400*scale)
    d.rounded_rectangle((540-bw//2,y-36,540+bw//2,y+36),radius=18,fill=(255,253,248,a),outline=ACCENT,width=2)
    d.text((540,y),"身边原理 · Ken",font=FONT_S,fill=(*ACCENT,a),anchor="mm")


def _fridge(d, cx, cy, *, scale=1.0, open_door=0.0, time_sec=0.0, show_loop=False, heat_back=0.0):
    s=scale; w,h=220*s,380*s; x0,y0=cx-w/2,cy-h/2
    d.rounded_rectangle((x0+4,y0+6,x0+w+4,y0+h+6),radius=14*s,fill=(200,196,190))
    d.rounded_rectangle((x0,y0,x0+w,y0+h),radius=14*s,fill=BODY,outline=INK,width=2)
    # freezer / fridge split
    mid=y0+h*0.32
    d.line((x0+10,mid,x0+w-10,mid),fill=LINE,width=2)
    door_w=w*(1-0.7*open_door)
    d.rounded_rectangle((x0+8,y0+12,x0+door_w,mid-4),radius=6,fill=WHITE,outline=METAL_DK,width=1)
    d.rounded_rectangle((x0+8,mid+4,x0+door_w,y0+h-12),radius=6,fill=WHITE,outline=METAL_DK,width=1)
    if open_door>0.3:
        # cold glow inside
        d.rounded_rectangle((x0+w*0.35,y0+20,x0+w-16,y0+h-20),radius=6,fill=(*COLD_LT,120))
        for i in range(5):
            px=x0+w*0.5+i*12; py=y0+h*0.55+math.sin(time_sec*3+i)*6
            d.ellipse((px-4,py-4,px+4,py+4),fill=COLD)
    # seal
    d.rectangle((x0+2,y0+10,x0+8,y0+h-10),fill=METAL_DK)
    if show_loop:
        # evaporator inside
        d.rounded_rectangle((x0+w*0.4,y0+40,x0+w-30,y0+100),radius=4,fill=COLD,outline=INK,width=1)
        # compressor bottom
        d.ellipse((cx-30*s,y0+h+5,cx+30*s,y0+h+55*s),fill=METAL_DK,outline=INK,width=2)
        # condenser back coils
        for i in range(6):
            yy=y0+60+i*28*s
            _sketch_line(d,(x0+w+8,yy),(x0+w+40*s,yy),COPPER if heat_back<0.5 else HOT,3,i)
        if heat_back>0:
            for i in range(5):
                yy=y0+80+i*30
                _sketch_line(d,(x0+w+42*s,yy),(x0+w+70*s+math.sin(time_sec*4+i)*8,yy-10),HOT,2,i)
    return {"body":(x0,y0,x0+w,y0+h),"comp":(cx,y0+h+30*s)}


def _step_ring(d,x,y,num,name,active,ts):
    r=(34 if active else 26)*(_pulse(ts,5,0.92,1.08) if active else 1)
    col=COLD if active else MUTED
    d.ellipse((x-r,y-r,x+r,y+r),fill=COLD if active else WHITE,outline=COLD,width=3)
    d.text((x,y),str(num),font=FONT_M,fill=WHITE if active else COLD,anchor="mm")
    if active: d.text((x,y+r+26+math.sin(ts*4)*3),name,font=FONT_S,fill=col,anchor="mm")


def draw_hook(t,w,h,time_sec=0.0):
    dx,_=_cam_drift(time_sec); img=_paper_bg(w,h,91).convert("RGBA"); d=ImageDraw.Draw(img)
    intro=_spring(t,0,0.3)
    if intro>0:
        _ken_badge(d,170,intro,0.85+0.15*intro)
        _fade_text(d,(540+dx,300),"我是 Ken",FONT_HERO,INK,intro,dy=(1-intro)*36)
        _fade_text(d,(540,390),"挑战每天用 3 分钟",FONT_L,INK,_spring(t,0.05,0.28))
        _fade_text(d,(540,460),"带你了解一个身边原理",FONT_M,MUTED,_spring(t,0.1,0.28))
        _fade_text(d,(540,550),"今天：冰箱怎么保持低温",FONT_L,ACCENT,_spring(t,0.16,0.3))
    show=_ease(_scene_t(t,0.28,0.45))
    if show>0: _fridge(d,540+dx,int(900+(1-show)*50),scale=1.1,open_door=0.55 if t>0.45 else 0.1,time_sec=time_sec,show_loop=t>0.55,heat_back=0.6 if t>0.6 else 0)
    if t>0.5:
        wrong=_ease(_scene_t(t,0.5,0.64)); right=_spring(t,0.66,0.28)
        if wrong>0 and right<0.35:
            d.rounded_rectangle((140,1280,940,1380),radius=12,fill=(255,240,235))
            d.text((540,1330),"❌ 不是往里灌冷气",font=FONT_M,fill=ACCENT,anchor="mm")
        if right>0:
            d.rounded_rectangle((100,1260,980,1440),radius=14,fill=(235,245,252))
            d.text((540,1320),"✓  把箱子里的热带到外面",font=FONT_L,fill=COLD,anchor="mm")
            d.text((540,1395),"和空调同一套搬家逻辑",font=FONT_S,fill=MUTED,anchor="mm")
    return img.convert("RGB")


def draw_cutaway(t,w,h,time_sec=0.0):
    img=_paper_bg(w,h,93).convert("RGBA"); d=ImageDraw.Draw(img)
    _fade_text(d,(540,95),"拆开看：冷从哪来",FONT_L,INK,_spring(t,0,0.2),dy=(1-_spring(t,0,0.2))*18)
    show=_spring(t,0.05,0.28)
    if show>0:
        parts=_fridge(d,480,560,scale=1.2,open_door=0.7,time_sec=time_sec,show_loop=True,heat_back=0.5)
        if t>0.25: _callout(d,(560,420),(760,340),"蒸发器吸热",COLD,_spring(t,0.22,0.25))
        if t>0.4: _callout(d,parts["comp"],(760,700),"压缩机",MUTED,_spring(t,0.4,0.25))
        if t>0.55: _callout(d,(620,500),(760,520),"冷凝器放热",HOT,_spring(t,0.55,0.25))
    if t>0.65:
        d.rounded_rectangle((100,1050,980,1280),radius=14,fill=(255,253,248))
        d.text((540,1120),"门封条密封不好 → 冷气漏、更费电",font=FONT_M,fill=INK,anchor="mm")
        d.text((540,1200),"冷冻更冷：蒸发与风道分配不同",font=FONT_S,fill=MUTED,anchor="mm")
    return img.convert("RGB")


def draw_cycle(t,w,h,time_sec=0.0):
    img=_paper_bg(w,h,97).convert("RGBA"); d=ImageDraw.Draw(img)
    d.text((540,90),"热量搬家四步曲",font=FONT_L,fill=INK,anchor="mm")
    active=-1 if t<0.06 else min(3,int((t-0.06)/0.2))
    _fridge(d,270,480,scale=0.9,open_door=0.5,time_sec=time_sec,show_loop=True,heat_back=0.7 if active>=2 else 0.2)
    # loop diagram
    path=[(700,280),(900,400),(700,560),(500,400),(700,280)]
    for i in range(4): _sketch_line(d,path[i],path[i+1],COPPER,3,i)
    names=["蒸发","压缩","冷凝","节流"]; pos=[(500,400),(700,280),(900,400),(700,560)]
    for i,(name,(x,y)) in enumerate(zip(names,pos)):
        on=i==active; r=32 if on else 24
        col=COLD if i in (0,3) else HOT
        d.ellipse((x-r,y-r,x+r,y+r),fill=col if on else WHITE,outline=col,width=3)
        d.text((x,y),str(i+1),font=FONT_M,fill=WHITE if on else col,anchor="mm")
        if on: d.text((x,y+48),name,font=FONT_S,fill=col,anchor="mm")
    # particles
    prog=(time_sec*0.35)%1; segs=4; si=int(prog*segs)%segs; loc=prog*segs-si
    x=_lerp(path[si][0],path[si+1][0],loc); y=_lerp(path[si][1],path[si+1][1],loc)
    d.ellipse((x-8,y-8,x+8,y+8),fill=HOT if si in (1,2) else COLD)
    tips=["① 蒸发器吸热，制冷剂变气","② 压缩机压成高温高压","③ 冷凝器把热交给箱外空气","④ 节流降压，回到蒸发器"]
    if active>=0:
        d.rounded_rectangle((80,1100,1000,1220),radius=14,fill=(255,253,248))
        d.text((540,1160),tips[active],font=FONT_M,fill=INK,anchor="mm")
    if t>0.85: d.text((540,1400),"和空调同一套：压缩·冷凝·节流·蒸发",font=FONT_S,fill=MUTED,anchor="mm")
    return img.convert("RGB")


def draw_analogy(t,w,h,time_sec=0.0):
    img=_paper_bg(w,h,99).convert("RGBA"); d=ImageDraw.Draw(img)
    d.text((540,95),"几个现象，一次说清",font=FONT_L,fill=INK,anchor="mm")
    cards=[(0.08,"为什么后背烫？","那是热量出口"),(0.32,"为什么塞太满降温慢？","空气对流受阻，换热变差"),(0.55,"为什么门老开费电？","等于不断给箱内加热")]
    for idx,(start,title,sub) in enumerate(cards):
        a=_spring(t,start,0.25)
        if a<=0: continue
        y=260+idx*300+(1-a)*40
        d.rounded_rectangle((90,y,990,y+260),radius=16,fill=(255,253,248),outline=LINE,width=2)
        d.text((540,y+45),title,font=FONT_M,fill=INK,anchor="mm")
        d.text((540,y+100),sub,font=FONT_S,fill=MUTED,anchor="mm")
        if idx==0: _fridge(d,540,y+185,scale=0.55,show_loop=True,heat_back=1.0,time_sec=time_sec,open_door=0.2)
        elif idx==1:
            _fridge(d,300,y+185,scale=0.5,open_door=0.6,time_sec=time_sec); d.text((300,y+245),"太满 ✗",font=FONT_XS,fill=HOT,anchor="mm")
            _fridge(d,780,y+185,scale=0.5,open_door=0.6,time_sec=time_sec); d.text((780,y+245),"留空 ✓",font=FONT_XS,fill=GREEN,anchor="mm")
        else:
            _fridge(d,540+math.sin(time_sec*6)*8,y+185,scale=0.55,open_door=0.85,time_sec=time_sec)
            d.text((540,y+245),"冷气外逃",font=FONT_XS,fill=ACCENT,anchor="mm")
    if t>0.78:
        d.text((540,1240),"冰箱是小型热量搬运站",font=FONT_L,fill=INK,anchor="mm")
        d.text((540,1310),"冷 = 把热带走之后的结果",font=FONT_M,fill=COLD,anchor="mm")
    return img.convert("RGB")


def draw_outro(t,w,h,time_sec=0.0):
    img=_paper_bg(w,h,101).convert("RGBA"); d=ImageDraw.Draw(img)
    a=_spring(t,0,0.35)
    _fridge(d,540,int(480+(1-a)*30),scale=1.15,open_door=0.4,time_sec=time_sec,show_loop=True,heat_back=0.6)
    if t>0.2:
        d.rounded_rectangle((80,820,1000,1020),radius=16,fill=(255,253,248),outline=ACCENT,width=2)
        d.text((540,880),"口诀记住",font=FONT_S,fill=MUTED,anchor="mm")
        d.text((540,950),"箱内吸热 · 箱外放热 · 压缩机当队长",font=FONT_L,fill=INK,anchor="mm")
    if t>0.5:
        b=_spring(t,0.5,0.25); _ken_badge(d,1140,b,0.9+0.1*b)
        _fade_text(d,(540,1230),"关注身边原理 · 我是 Ken",FONT_L,INK,b)
        _fade_text(d,(540,1300),"明天继续 3 分钟了解下一个原理",FONT_M,ACCENT,_spring(t,0.56,0.25))
    if t>0.75:
        d.text((540,1480),"评论区：电饭煲 / 热水器 / 路由器？",font=FONT_S,fill=(*MUTED,int(255*(0.6+0.4*_pulse(time_sec,2)))),anchor="mm")
    return img.convert("RGB")


SCENE_DRAWERS={"hook":draw_hook,"cutaway":draw_cutaway,"cycle":draw_cycle,"analogy":draw_analogy,"outro":draw_outro}

def draw_scene(scene_name,t,width=1080,height=1920,*,time_sec=None):
    ts=time_sec if time_sec is not None else t*120.0
    return SCENE_DRAWERS.get(scene_name,draw_hook)(_clamp01(t),width,height,ts)
