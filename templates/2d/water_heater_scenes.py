"""电热水器分集 · 纪录片手绘风 2D。"""

from __future__ import annotations

import math
import random
from typing import Callable

from PIL import Image, ImageDraw

from pipeline.fonts import load_cjk_font as _font

PAPER=(248,245,238); WALL=(242,238,230); FLOOR=(218,214,206); INK=(38,36,34); MUTED=(110,105,98)
ACCENT=(180,75,45); HOT=(195,90,55); HOT_LT=(240,190,150); COLD=(70,140,185); COLD_LT=(180,215,235)
LINE=(180,175,168); WHITE=(252,250,246); METAL=(168,172,178); METAL_DK=(105,110,118)
BODY=(235,238,242); BODY_DK=(190,195,200); GREEN=(80,160,110); MG=(180,190,170)


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

def _heater(d,cx,cy,*,scale=1.0,ts=0.0,hot_level=0.6,heating=True,cutaway=False,scale_dirty=0.0):
    s=scale; w,h=200*s,360*s; x0,y0=cx-w/2,cy-h/2
    # insulation shell
    d.rounded_rectangle((x0-8,y0-4,x0+w+8,y0+h+4),radius=18*s,fill=BODY_DK,outline=INK,width=1)
    d.rounded_rectangle((x0,y0,x0+w,y0+h),radius=16*s,fill=BODY,outline=INK,width=2)
    # water layers
    split=y0+h*(1-0.35-0.4*hot_level)
    d.rounded_rectangle((x0+10,y0+10,x0+w-10,split),radius=8,fill=(*HOT_LT,200))
    d.rounded_rectangle((x0+10,split,x0+w-10,y0+h-10),radius=8,fill=(*COLD_LT,200))
    d.text((cx,(y0+10+split)/2),"热水",font=FONT_XS,fill=HOT,anchor="mm")
    d.text((cx,(split+y0+h-10)/2),"冷水",font=FONT_XS,fill=COLD,anchor="mm")
    # heating element
    hx,hy=cx,y0+h*0.72
    col=HOT if heating else METAL_DK
    d.rounded_rectangle((hx-50*s,hy-8*s,hx+50*s,hy+8*s),radius=4,fill=col,outline=INK,width=1)
    if heating:
        for i in range(4):
            _sketch_line(d,(hx-40*s+i*20*s,hy-20*s),(hx-35*s+i*20*s,hy-35*s-math.sin(ts*5+i)*4),HOT,2,i)
    # magnesium rod
    d.rounded_rectangle((x0+w*0.7,y0+h*0.35,x0+w*0.82,y0+h*0.75),radius=3,fill=MG,outline=INK,width=1)
    if scale_dirty>0.3:
        for i in range(5):
            d.ellipse((hx-45*s+i*18*s,hy-6,hx-35*s+i*18*s,hy+10),fill=(160,150,130))
    # pipes
    _sketch_line(d,(x0+w*0.25,y0+h),(x0+w*0.25,y0+h+40*s),COLD,5,1)
    _sketch_line(d,(x0+w*0.75,y0),(x0+w*0.75,y0-40*s),HOT,5,2)
    if cutaway:
        d.text((hx,hy+22*s),"加热管",font=FONT_XS,fill=HOT if heating else MUTED,anchor="mm")
        d.text((x0+w*0.76,y0+h*0.55),"镁棒",font=FONT_XS,fill=MUTED,anchor="mm")
    # thermostat light
    d.ellipse((x0+w-35*s,y0+20*s,x0+w-15*s,y0+40*s),fill=GREEN if heating else METAL)
    return {"element":(hx,hy),"out":(x0+w*0.75,y0),"in":(x0+w*0.25,y0+h),"mg":(x0+w*0.76,y0+h*0.55)}

def _step_ring(d,x,y,num,name,active,ts):
    r=(34 if active else 26)*(_pulse(ts,5,0.92,1.08) if active else 1)
    d.ellipse((x-r,y-r,x+r,y+r),fill=HOT if active else WHITE,outline=HOT,width=3)
    d.text((x,y),str(num),font=FONT_M,fill=WHITE if active else HOT,anchor="mm")
    if active: d.text((x,y+r+26),name,font=FONT_S,fill=HOT,anchor="mm")

def draw_hook(t,w,h,time_sec=0.0):
    dx,_=_cam_drift(time_sec); img=_paper_bg(w,h,171).convert("RGBA"); d=ImageDraw.Draw(img)
    intro=_spring(t,0,0.3)
    if intro>0:
        _ken_badge(d,170,intro,0.85+0.15*intro)
        _fade_text(d,(540+dx,300),"我是 Ken",FONT_HERO,INK,intro,dy=(1-intro)*36)
        _fade_text(d,(540,390),"挑战每天用 3 分钟",FONT_L,INK,_spring(t,0.05,0.28))
        _fade_text(d,(540,460),"带你了解一个身边原理",FONT_M,MUTED,_spring(t,0.1,0.28))
        _fade_text(d,(540,550),"今天：电热水器怎么供应热水",FONT_L,ACCENT,_spring(t,0.16,0.3))
    show=_ease(_scene_t(t,0.28,0.45))
    if show>0:
        _heater(d,540+dx,int(900+(1-show)*40),scale=1.1,ts=time_sec,hot_level=0.65,heating=t>0.45,cutaway=t>0.55)
    if t>0.5:
        wrong=_ease(_scene_t(t,0.5,0.64)); right=_spring(t,0.66,0.28)
        if wrong>0 and right<0.35:
            d.rounded_rectangle((120,1280,960,1380),radius=12,fill=(255,240,235))
            d.text((540,1330),"❌ 不是一直开着大火猛烧",font=FONT_M,fill=ACCENT,anchor="mm")
        if right>0:
            d.rounded_rectangle((100,1260,980,1440),radius=14,fill=(255,245,240))
            d.text((540,1320),"✓  加热 + 保温 + 温控 三件套",font=FONT_L,fill=HOT,anchor="mm")
            d.text((540,1395),"到温停，降温再补热",font=FONT_S,fill=MUTED,anchor="mm")
    return img.convert("RGB")

def draw_cutaway(t,w,h,time_sec=0.0):
    img=_paper_bg(w,h,173).convert("RGBA"); d=ImageDraw.Draw(img)
    _fade_text(d,(540,95),"拆开看：罐里有谁",FONT_L,INK,_spring(t,0,0.2))
    show=_spring(t,0.05,0.28)
    if show>0:
        p=_heater(d,480,560,scale=1.2,ts=time_sec,hot_level=0.55,heating=True,cutaway=True)
        if t>0.25: _callout(d,p["element"],(760,700),"加热管",HOT,_spring(t,0.22,0.25))
        if t>0.4: _callout(d,p["mg"],(760,520),"镁棒护胆",MG,_spring(t,0.4,0.25))
        if t>0.55: _callout(d,(480,380),(120,320),"保温层",MUTED,_spring(t,0.55,0.25))
    if t>0.65:
        d.rounded_rectangle((100,1050,980,1280),radius=14,fill=(255,253,248))
        d.text((540,1120),"温控器：到温断电，降温再接通",font=FONT_M,fill=INK,anchor="mm")
        d.text((540,1200),"安全阀：压力过高就泄压",font=FONT_S,fill=MUTED,anchor="mm")
    return img.convert("RGB")

def draw_cycle(t,w,h,time_sec=0.0):
    img=_paper_bg(w,h,177).convert("RGBA"); d=ImageDraw.Draw(img)
    d.text((540,90),"热水怎么循环补给",font=FONT_L,fill=INK,anchor="mm")
    active=-1 if t<0.06 else min(3,int((t-0.06)/0.2))
    hot=0.3+0.2*max(0,active)
    _heater(d,300,480,scale=1.0,ts=time_sec,hot_level=hot,heating=active in (1,3),cutaway=True)
    # flow arrows panel
    d.rounded_rectangle((520,260,1000,700),radius=16,fill=WHITE,outline=LINE,width=2)
    tips_side=["冷水从下部进入","加热管加热，热水上浮","上部出口放出热水","降温后再启动补热"]
    if active>=0:
        d.text((760,360),tips_side[active],font=FONT_M,fill=INK,anchor="mm")
        for i in range(6):
            u=(time_sec*0.6+i/6)%1.0
            if active<=1:
                x,y=760,500+_lerp(80,-80,u)
            else:
                x,y=_lerp(650,900,u),400
            d.ellipse((x-6,y-6,x+6,y+6),fill=HOT if active>=1 else COLD)
    steps=["进冷水","加热分层","放出热水","温控补热"]
    tips=["① 冷水从进水管进入内胆","② 加热管工作，热水上浮形成分层","③ 混水阀打开，上部热水流出","④ 水温偏低，温控再次启动"]
    for i,name in enumerate(steps): _step_ring(d,160+i*250,920,i+1,name,i==active,time_sec)
    if active>=0:
        d.rounded_rectangle((80,1100,1000,1220),radius=14,fill=(255,253,248))
        d.text((540,1160),tips[active],font=FONT_M,fill=INK,anchor="mm")
    if t>0.85: d.text((540,1420),"是蓄热的水库，不是无限即热魔法",font=FONT_S,fill=MUTED,anchor="mm")
    return img.convert("RGB")

def draw_analogy(t,w,h,time_sec=0.0):
    img=_paper_bg(w,h,179).convert("RGBA"); d=ImageDraw.Draw(img)
    d.text((540,95),"几个现象，一次说清",font=FONT_L,fill=INK,anchor="mm")
    cards=[(0.08,"为什么先热后凉？","上层热水用完，下层冷水上来"),(0.32,"为什么要除水垢？","垢裹加热管，更费电还易局部过热"),(0.55,"为什么要换镁棒？","耗尽后内胆更易被腐蚀")]
    for idx,(start,title,sub) in enumerate(cards):
        a=_spring(t,start,0.25)
        if a<=0: continue
        y=250+idx*310+(1-a)*40
        d.rounded_rectangle((90,y,990,y+270),radius=16,fill=(255,253,248),outline=LINE,width=2)
        d.text((540,y+40),title,font=FONT_M,fill=INK,anchor="mm")
        d.text((540,y+95),sub,font=FONT_S,fill=MUTED,anchor="mm")
        if idx==0:
            _heater(d,400,y+185,scale=0.5,ts=time_sec,hot_level=0.85,heating=False)
            d.text((400,y+245),"刚打开",font=FONT_XS,fill=HOT,anchor="mm")
            _heater(d,760,y+185,scale=0.5,ts=time_sec,hot_level=0.2,heating=True)
            d.text((760,y+245),"用一阵子",font=FONT_XS,fill=COLD,anchor="mm")
        elif idx==1:
            _heater(d,540,y+185,scale=0.55,ts=time_sec,hot_level=0.5,heating=True,scale_dirty=0.8,cutaway=True)
            d.text((540,y+245),"水垢包裹",font=FONT_XS,fill=ACCENT,anchor="mm")
        else:
            d.rounded_rectangle((480,y+140,600,y+230),radius=6,fill=MG,outline=INK,width=2)
            d.text((540,y+185),"镁棒",font=FONT_S,fill=INK,anchor="mm")
            d.text((540,y+245),"牺牲自己，保护内胆",font=FONT_XS,fill=MUTED,anchor="mm")
    if t>0.78:
        d.text((540,1250),"带温控的储热罐",font=FONT_L,fill=INK,anchor="mm")
        d.text((540,1320),"维护决定寿命和效率",font=FONT_M,fill=HOT,anchor="mm")
    return img.convert("RGB")

def draw_outro(t,w,h,time_sec=0.0):
    img=_paper_bg(w,h,181).convert("RGBA"); d=ImageDraw.Draw(img)
    a=_spring(t,0,0.35)
    _heater(d,540,int(460+(1-a)*30),scale=1.15,ts=time_sec,hot_level=0.6,heating=True,cutaway=True)
    if t>0.2:
        d.rounded_rectangle((70,820,1010,1030),radius=16,fill=(255,253,248),outline=ACCENT,width=2)
        d.text((540,880),"口诀记住",font=FONT_S,fill=MUTED,anchor="mm")
        d.text((540,950),"加热管烧水 · 温控管开关",font=FONT_L,fill=INK,anchor="mm")
        d.text((540,1005),"保温锁热 · 镁棒护胆",font=FONT_L,fill=HOT,anchor="mm")
    if t>0.5:
        b=_spring(t,0.5,0.25); _ken_badge(d,1140,b,0.9+0.1*b)
        _fade_text(d,(540,1230),"关注身边原理 · 我是 Ken",FONT_L,INK,b)
        _fade_text(d,(540,1300),"明天继续 3 分钟了解下一个原理",FONT_M,ACCENT,_spring(t,0.56,0.25))
    if t>0.75:
        d.text((540,1480),"评论区：燃气热水器 / 净水器 / 马桶水箱？",font=FONT_S,fill=(*MUTED,int(255*(0.6+0.4*_pulse(time_sec,2)))),anchor="mm")
    return img.convert("RGB")

SCENE_DRAWERS={"hook":draw_hook,"cutaway":draw_cutaway,"cycle":draw_cycle,"analogy":draw_analogy,"outro":draw_outro}
def draw_scene(scene_name,t,width=1080,height=1920,*,time_sec=None):
    ts=time_sec if time_sec is not None else t*120.0
    return SCENE_DRAWERS.get(scene_name,draw_hook)(_clamp01(t),width,height,ts)
