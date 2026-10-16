"""电磁炉分集 · 纪录片手绘风 2D。"""

from __future__ import annotations

import math
import random
from typing import Callable

from PIL import Image, ImageDraw

from pipeline.fonts import load_cjk_font as _font

PAPER=(248,245,238); WALL=(242,238,230); FLOOR=(218,214,206); INK=(38,36,34); MUTED=(110,105,98)
ACCENT=(180,75,45); HOT=(195,90,55); HOT_LT=(240,190,150); FIELD=(90,120,185); FIELD_LT=(170,195,230)
LINE=(180,175,168); WHITE=(252,250,246); METAL=(168,172,178); METAL_DK=(105,110,118)
BODY=(40,42,48); BODY_LT=(70,74,82); POT=(70,75,85); GREEN=(80,160,110)


FONT_HERO,FONT_L,FONT_M,FONT_S,FONT_XS=_font(62,True),_font(44,True),_font(34),_font(28),_font(24)
def _clamp01(t): return max(0.0,min(1.0,t))
def _ease(t): t=_clamp01(t); return t*t*(3-2*t)
def _spring(t,s=0.0,d=0.3):
    if t<s: return 0.0
    p=_clamp01((t-s)/d); return 1-math.exp(-6*p)*math.cos(p*math.pi*2.5)
def _lerp(a,b,t): return a+(b-a)*_clamp01(t)
def _scene_t(t,a,b):
    if t<=a: return 0.0
    if t>=b: return 1.0
    return (t-a)/(b-a)
def _pulse(ts,sp=2.5,lo=0.85,hi=1.0): return lo+(hi-lo)*(0.5+0.5*math.sin(ts*sp*math.tau))
def _wobble(x,y,seed,amp=1.2): return x+math.sin(seed*1.7)*amp, y+math.cos(seed*2.3)*amp
def _cam_drift(ts,ax=5.0,ay=3.0): return math.sin(ts*0.7)*ax, math.cos(ts*0.55)*ay

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
        f=i/steps; pts.append(_wobble(_lerp(x1,x2,f),_lerp(y1,y2,f),seed+i,0.8))
    for i in range(len(pts)-1): d.line((pts[i],pts[i+1]),fill=color,width=width)

def _callout(d,tip,label,text,color=INK,alpha=1.0):
    if alpha<=0.01: return
    _sketch_line(d,tip,label,color,2,int(tip[0]+tip[1]))
    d.ellipse((tip[0]-5,tip[1]-5,tip[0]+5,tip[1]+5),fill=color)
    d.text(label,text,font=FONT_S,fill=(*color,int(255*_clamp01(alpha))),anchor="lm")

def _fade_text(d,xy,text,font,color,alpha,anchor="mm",dy=0.0):
    if alpha<=0.01: return
    d.text((xy[0],xy[1]+dy),text,font=font,fill=(*color,int(255*_clamp01(alpha))),anchor=anchor)

def _ken_badge(d,y,alpha=1.0,scale=1.0):
    if alpha<=0: return
    a=int(255*_clamp01(alpha)); bw=int(400*scale)
    d.rounded_rectangle((540-bw//2,y-36,540+bw//2,y+36),radius=18,fill=(255,253,248,a),outline=ACCENT,width=2)
    d.text((540,y),"身边原理 · Ken",font=FONT_S,fill=(*ACCENT,a),anchor="mm")

def _field_arcs(d,cx,cy,ts,power=1.0):
    for i in range(4):
        r=30+i*22+(ts*40)%22
        d.arc((cx-r,cy-r*0.45,cx+r,cy+r*0.45),200,340,fill=(*FIELD,int(140*power*(1-i/5))),width=3)

def _induction(d,cx,cy,*,scale=1.0,ts=0.0,power=1.0,pot_ok=True,lift=0.0,cutaway=False):
    s=scale; w,h=360*s,80*s; x0,y0=cx-w/2,cy-h/2
    d.rounded_rectangle((x0+3,y0+5,x0+w+3,y0+h+5),radius=12*s,fill=(30,32,36))
    d.rounded_rectangle((x0,y0,x0+w,y0+h),radius=12*s,fill=BODY,outline=INK,width=2)
    # glass panel ring
    d.ellipse((cx-70*s,y0-10*s,cx+70*s,y0+h+10*s),outline=FIELD_LT,width=3)
    # coil under
    if cutaway or power>0:
        for i in range(5):
            rr=20*s+i*10*s
            d.ellipse((cx-rr,cy-rr*0.35,cx+rr,cy+rr*0.35),outline=FIELD if power>0 else METAL,width=2)
    # controls
    for i in range(3):
        bx=x0+30*s+i*40*s
        d.rounded_rectangle((bx,y0+h*0.35,bx+28*s,y0+h*0.7),radius=4,fill=BODY_LT)
    d.ellipse((x0+w-50*s,y0+h*0.3,x0+w-25*s,y0+h*0.7),fill=GREEN if power>0.3 else METAL)
    # pot
    py=y0-55*s-lift*40*s
    pot_col=POT if pot_ok else (200,200,205)
    d.rounded_rectangle((cx-55*s,py,cx+55*s,py+50*s),radius=8*s,fill=pot_col,outline=INK,width=2)
    d.ellipse((cx-55*s,py-8*s,cx+55*s,py+12*s),fill=pot_col,outline=INK,width=1)
    if pot_ok and power>0.3 and lift<0.5:
        _field_arcs(d,cx,cy-10*s,ts,power)
        # eddy heat on pot bottom
        for i in range(6):
            a=ts*6+i
            px=cx+math.cos(a)*30*s; py2=py+40*s+math.sin(a*2)*3
            d.ellipse((px-4,py2-4,px+4,py2+4),fill=HOT_LT)
        d.text((cx,py+25*s),"涡流发热",font=FONT_XS,fill=HOT,anchor="mm")
    elif not pot_ok:
        d.text((cx,py+25*s),"不匹配",font=FONT_XS,fill=ACCENT,anchor="mm")
    if cutaway:
        d.text((cx,cy+35*s),"线圈盘",font=FONT_XS,fill=FIELD_LT,anchor="mm")
    return {"coil":(cx,cy),"pot":(cx,py+25*s),"panel":(cx,y0)}

def _step_ring(d,x,y,num,name,active,ts):
    r=(34 if active else 26)*(_pulse(ts,5,0.92,1.08) if active else 1)
    d.ellipse((x-r,y-r,x+r,y+r),fill=FIELD if active else WHITE,outline=FIELD,width=3)
    d.text((x,y),str(num),font=FONT_M,fill=WHITE if active else FIELD,anchor="mm")
    if active: d.text((x,y+r+26),name,font=FONT_S,fill=FIELD,anchor="mm")

def draw_hook(t,w,h,time_sec=0.0):
    dx,_=_cam_drift(time_sec); img=_paper_bg(w,h,191).convert("RGBA"); d=ImageDraw.Draw(img)
    intro=_spring(t,0,0.3)
    if intro>0:
        _ken_badge(d,170,intro,0.85+0.15*intro)
        _fade_text(d,(540+dx,300),"我是 Ken",FONT_HERO,INK,intro,dy=(1-intro)*36)
        _fade_text(d,(540,390),"挑战每天用 3 分钟",FONT_L,INK,_spring(t,0.05,0.28))
        _fade_text(d,(540,460),"带你了解一个身边原理",FONT_M,MUTED,_spring(t,0.1,0.28))
        _fade_text(d,(540,550),"今天：电磁炉怎么让锅自己热",FONT_L,ACCENT,_spring(t,0.16,0.3))
    show=_ease(_scene_t(t,0.28,0.45))
    if show>0:
        _induction(d,540+dx,int(920+(1-show)*40),scale=1.15,ts=time_sec,power=0.9 if t>0.5 else 0.3,cutaway=t>0.55)
    if t>0.5:
        wrong=_ease(_scene_t(t,0.5,0.64)); right=_spring(t,0.66,0.28)
        if wrong>0 and right<0.35:
            d.rounded_rectangle((120,1280,960,1380),radius=12,fill=(255,240,235))
            d.text((540,1330),"❌ 不是电热丝先烤热面板",font=FONT_M,fill=ACCENT,anchor="mm")
        if right>0:
            d.rounded_rectangle((100,1260,980,1440),radius=14,fill=(235,242,252))
            d.text((540,1320),"✓  磁场在锅底感应涡流发热",font=FONT_L,fill=FIELD,anchor="mm")
            d.text((540,1395),"面板几乎不热，锅自己热",font=FONT_S,fill=MUTED,anchor="mm")
    return img.convert("RGB")

def draw_cutaway(t,w,h,time_sec=0.0):
    img=_paper_bg(w,h,193).convert("RGBA"); d=ImageDraw.Draw(img)
    _fade_text(d,(540,95),"拆开看：磁场如何耦合到锅",FONT_L,INK,_spring(t,0,0.2))
    show=_spring(t,0.05,0.28)
    if show>0:
        p=_induction(d,500,560,scale=1.25,ts=time_sec,power=0.95,cutaway=True)
        if t>0.25: _callout(d,p["coil"],(760,620),"线圈盘",FIELD,_spring(t,0.22,0.25))
        if t>0.4: _callout(d,p["pot"],(760,400),"铁磁性锅底",HOT,_spring(t,0.4,0.25))
        if t>0.55: _callout(d,(500,650),(120,700),"散热风扇",MUTED,_spring(t,0.55,0.25))
    if t>0.65:
        d.rounded_rectangle((100,1050,980,1280),radius=14,fill=(255,253,248))
        d.text((540,1120),"高频交变电流 → 交变磁场",font=FONT_M,fill=INK,anchor="mm")
        d.text((540,1200),"功率管调功率，风扇给电子元件降温",font=FONT_S,fill=MUTED,anchor="mm")
    return img.convert("RGB")

def draw_cycle(t,w,h,time_sec=0.0):
    img=_paper_bg(w,h,197).convert("RGBA"); d=ImageDraw.Draw(img)
    d.text((540,90),"涡流发热四步",font=FONT_L,fill=INK,anchor="mm")
    active=-1 if t<0.06 else min(3,int((t-0.06)/0.2))
    _induction(d,540,400,scale=1.15,ts=time_sec,power=0.3 if active<0 else 1.0,cutaway=True)
    steps=["交变电流","交变磁场","感应涡流","电阻发热"]
    tips=["① 线圈电流方向快速变化","② 磁场快速变化并穿过锅底","③ 锅底感应出涡流","④ 涡流遇电阻 → 锅底发热煮食物"]
    for i,name in enumerate(steps): _step_ring(d,160+i*250,880,i+1,name,i==active,time_sec)
    if active>=0:
        d.rounded_rectangle((80,1050,1000,1170),radius=14,fill=(255,253,248))
        d.text((540,1110),tips[active],font=FONT_M,fill=INK,anchor="mm")
    if t>0.82: d.text((540,1400),"微晶面板主要是支撑和隔热，不是热源",font=FONT_S,fill=MUTED,anchor="mm")
    return img.convert("RGB")

def draw_analogy(t,w,h,time_sec=0.0):
    img=_paper_bg(w,h,199).convert("RGBA"); d=ImageDraw.Draw(img)
    d.text((540,95),"几个现象，一次说清",font=FONT_L,fill=INK,anchor="mm")
    cards=[(0.08,"铝锅铜锅为啥不行？","磁耦合弱，涡流加热效率低"),(0.32,"锅离板太远？","磁场耦合变弱，几乎不加热"),(0.55,"空烧为什么关机？","温度异常升高，保护切断功率")]
    for idx,(start,title,sub) in enumerate(cards):
        a=_spring(t,start,0.25)
        if a<=0: continue
        y=250+idx*310+(1-a)*40
        d.rounded_rectangle((90,y,990,y+270),radius=16,fill=(255,253,248),outline=LINE,width=2)
        d.text((540,y+40),title,font=FONT_M,fill=INK,anchor="mm")
        d.text((540,y+95),sub,font=FONT_S,fill=MUTED,anchor="mm")
        if idx==0:
            _induction(d,320,y+185,scale=0.55,ts=time_sec,power=0.8,pot_ok=False)
            d.text((320,y+245),"不匹配 ✗",font=FONT_XS,fill=HOT,anchor="mm")
            _induction(d,780,y+185,scale=0.55,ts=time_sec,power=0.9,pot_ok=True)
            d.text((780,y+245),"铁锅 ✓",font=FONT_XS,fill=GREEN,anchor="mm")
        elif idx==1:
            _induction(d,540,y+185,scale=0.6,ts=time_sec,power=0.9,lift=1.0,pot_ok=True)
            d.text((540,y+245),"离太远",font=FONT_XS,fill=ACCENT,anchor="mm")
        else:
            _induction(d,540,y+185,scale=0.6,ts=time_sec,power=0.2,pot_ok=True)
            pulse=_pulse(time_sec,4,0.8,1.0)
            d.text((540,y+140),"保护",font=FONT_S,fill=(*HOT,int(255*pulse)),anchor="mm")
            d.text((540,y+245),"过热断电",font=FONT_XS,fill=HOT,anchor="mm")
    if t>0.78:
        d.text((540,1250),"加热的是合格的锅",font=FONT_L,fill=INK,anchor="mm")
        d.text((540,1320),"不是烤热一块板",font=FONT_M,fill=FIELD,anchor="mm")
    return img.convert("RGB")

def draw_outro(t,w,h,time_sec=0.0):
    img=_paper_bg(w,h,201).convert("RGBA"); d=ImageDraw.Draw(img)
    a=_spring(t,0,0.35)
    _induction(d,540,int(450+(1-a)*30),scale=1.2,ts=time_sec,power=0.95,cutaway=True)
    if t>0.2:
        d.rounded_rectangle((70,780,1010,1000),radius=16,fill=(255,253,248),outline=ACCENT,width=2)
        d.text((540,840),"口诀记住",font=FONT_S,fill=MUTED,anchor="mm")
        d.text((540,910),"线圈造交变磁场",font=FONT_L,fill=INK,anchor="mm")
        d.text((540,970),"锅里起涡流 · 涡流变热",font=FONT_L,fill=FIELD,anchor="mm")
    if t>0.5:
        b=_spring(t,0.5,0.25); _ken_badge(d,1120,b,0.9+0.1*b)
        _fade_text(d,(540,1210),"关注身边原理 · 我是 Ken",FONT_L,INK,b)
        _fade_text(d,(540,1280),"明天继续 3 分钟了解下一个原理",FONT_M,ACCENT,_spring(t,0.56,0.25))
    if t>0.75:
        d.text((540,1460),"评论区：空气炸锅 / 电烤箱 / 对比微波炉？",font=FONT_S,fill=(*MUTED,int(255*(0.6+0.4*_pulse(time_sec,2)))),anchor="mm")
    return img.convert("RGB")

SCENE_DRAWERS={"hook":draw_hook,"cutaway":draw_cutaway,"cycle":draw_cycle,"analogy":draw_analogy,"outro":draw_outro}
def draw_scene(scene_name,t,width=1080,height=1920,*,time_sec=None):
    ts=time_sec if time_sec is not None else t*120.0
    return SCENE_DRAWERS.get(scene_name,draw_hook)(_clamp01(t),width,height,ts)
