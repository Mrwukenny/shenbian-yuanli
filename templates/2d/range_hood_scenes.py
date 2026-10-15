"""抽油烟机分集 · 纪录片手绘风 2D。"""

from __future__ import annotations

import math
import random
from typing import Callable

from PIL import Image, ImageDraw

from pipeline.fonts import load_cjk_font as _font

PAPER=(248,245,238); WALL=(242,238,230); FLOOR=(218,214,206); INK=(38,36,34); MUTED=(110,105,98)
ACCENT=(180,75,45); AIR=(70,130,175); AIR_LT=(170,205,230); HOT=(195,90,55); LINE=(180,175,168)
WHITE=(252,250,246); METAL=(168,172,178); METAL_DK=(105,110,118); BODY=(55,58,64); BODY_LT=(90,95,105)
OIL=(140,110,60); OIL_LT=(190,160,100); GREEN=(80,160,110); HOT_LT=(240,190,150)


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
def _wobble(x,y,seed,amp=1.2): return x+math.sin(seed*1.7)*amp,y+math.cos(seed*2.3)*amp
def _cam_drift(ts,ax=5.0,ay=3.0): return math.sin(ts*0.7)*ax,math.cos(ts*0.55)*ay

def _paper_bg(w,h,seed=7):
    img=Image.new("RGB",(w,h),PAPER); d=ImageDraw.Draw(img)
    d.rectangle((0,0,w,int(h*0.55)),fill=WALL); d.rectangle((0,int(h*0.55),w,h),fill=FLOOR)
    d.line((0,int(h*0.55),w,int(h*0.55)),fill=LINE,width=2)
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
    _sketch_line(d,tip,label,color,2,int(tip[0]+tip[1])); d.ellipse((tip[0]-5,tip[1]-5,tip[0]+5,tip[1]+5),fill=color)
    d.text(label,text,font=FONT_S,fill=(*color,int(255*_clamp01(alpha))),anchor="lm")

def _fade_text(d,xy,text,font,color,alpha,anchor="mm",dy=0.0):
    if alpha<=0.01: return
    d.text((xy[0],xy[1]+dy),text,font=font,fill=(*color,int(255*_clamp01(alpha))),anchor=anchor)

def _ken_badge(d,y,alpha=1.0,scale=1.0):
    if alpha<=0: return
    a=int(255*_clamp01(alpha)); bw=int(400*scale)
    d.rounded_rectangle((540-bw//2,y-36,540+bw//2,y+36),radius=18,fill=(255,253,248,a),outline=ACCENT,width=2)
    d.text((540,y),"身边原理 · Ken",font=FONT_S,fill=(*ACCENT,a),anchor="mm")

def _smoke(d,cx,cy,time_sec,count=10,strength=1.0):
    for i in range(count):
        u=(time_sec*0.4+i/count)%1.0
        x=cx+math.sin(time_sec*2+i)*20*(1-u)
        y=cy-u*120*strength
        r=6+10*u
        d.ellipse((x-r,y-r,x+r,y+r),fill=(*OIL_LT,int(100*strength*(1-u))))

def _range_hood(d,cx,cy,*,scale=1.0,time_sec=0.0,suction=1.0,dirty=0.0,show_fan=False):
    s=scale; w,h=420*s,160*s; x0,y0=cx-w/2,cy-h/2
    # chimney
    d.rounded_rectangle((cx-40*s,y0-120*s,cx+40*s,y0+10),radius=6,fill=BODY_LT,outline=INK,width=2)
    # canopy
    d.polygon([(x0,y0+h*0.35),(x0+w,y0+h*0.35),(x0+w*0.85,y0+h),(x0+w*0.15,y0+h)],fill=BODY,outline=INK)
    d.rounded_rectangle((x0,y0,x0+w,y0+h*0.4),radius=10*s,fill=BODY,outline=INK,width=2)
    # oil mesh
    mesh=(x0+w*0.2,y0+h*0.45,x0+w*0.8,y0+h*0.85)
    d.rounded_rectangle(mesh,radius=4,fill=METAL_DK if dirty<0.5 else OIL,outline=METAL,width=1)
    step=max(8,int(14*s))
    for i in range(int((mesh[2]-mesh[0])/step)):
        for j in range(int((mesh[3]-mesh[1])/step)):
            px,py=mesh[0]+8+i*step,mesh[1]+6+j*step
            if px<mesh[2]-6 and py<mesh[3]-6:
                d.rectangle((px,py,px+5,py+4),outline=OIL if dirty>0.4 else METAL,width=1)
    if show_fan:
        fx,fy=cx,y0+h*0.15
        ang=time_sec*8*suction
        for k in range(3):
            a=ang+k*2.094
            d.line((fx,fy,fx+math.cos(a)*28*s,fy+math.sin(a)*14*s),fill=METAL,width=4)
        d.ellipse((fx-8*s,fy-8*s,fx+8*s,fy+8*s),fill=METAL_DK)
    # rising smoke sucked in
    if suction>0.2:
        for i in range(8):
            u=(time_sec*0.7+i/8)%1.0
            x=_lerp(cx-60+i*15,cx,u)+math.sin(time_sec*3+i)*8
            y=_lerp(cy+180,y0+h,u)
            d.ellipse((x-5,y-5,x+5,y+5),fill=OIL if u<0.6 else AIR_LT)
    # stove
    d.rounded_rectangle((cx-90*s,cy+200*s,cx+90*s,cy+260*s),radius=8,fill=METAL_DK,outline=INK,width=2)
    d.ellipse((cx-35*s,cy+210*s,cx+35*s,cy+245*s),fill=(60,60,65),outline=HOT,width=2)
    _smoke(d,cx,cy+200*s,time_sec,count=8,strength=0.8*suction)
    return {"mesh":((mesh[0]+mesh[2])/2,(mesh[1]+mesh[3])/2),"fan":(cx,y0+h*0.15),"canopy":(cx,y0+h)}

def _step_ring(d,x,y,num,name,active,ts):
    r=(34 if active else 26)*(_pulse(ts,5,0.92,1.08) if active else 1)
    d.ellipse((x-r,y-r,x+r,y+r),fill=AIR if active else WHITE,outline=AIR,width=3)
    d.text((x,y),str(num),font=FONT_M,fill=WHITE if active else AIR,anchor="mm")
    if active: d.text((x,y+r+26),name,font=FONT_S,fill=AIR,anchor="mm")

def draw_hook(t,w,h,time_sec=0.0):
    dx,_=_cam_drift(time_sec); img=_paper_bg(w,h,111).convert("RGBA"); d=ImageDraw.Draw(img)
    intro=_spring(t,0,0.3)
    if intro>0:
        _ken_badge(d,170,intro,0.85+0.15*intro)
        _fade_text(d,(540+dx,300),"我是 Ken",FONT_HERO,INK,intro,dy=(1-intro)*36)
        _fade_text(d,(540,390),"挑战每天用 3 分钟",FONT_L,INK,_spring(t,0.05,0.28))
        _fade_text(d,(540,460),"带你了解一个身边原理",FONT_M,MUTED,_spring(t,0.1,0.28))
        _fade_text(d,(540,550),"今天：抽油烟机怎么吸走油烟",FONT_L,ACCENT,_spring(t,0.16,0.3))
    show=_ease(_scene_t(t,0.28,0.45))
    if show>0: _range_hood(d,540+dx,int(780+(1-show)*40),scale=1.05,time_sec=time_sec,suction=0.9 if t>0.5 else 0.4,show_fan=t>0.55)
    if t>0.5:
        wrong=_ease(_scene_t(t,0.5,0.64)); right=_spring(t,0.66,0.28)
        if wrong>0 and right<0.35:
            d.rounded_rectangle((120,1280,960,1380),radius=12,fill=(255,240,235))
            d.text((540,1330),"❌ 不只是头顶大风扇乱吹",font=FONT_M,fill=ACCENT,anchor="mm")
        if right>0:
            d.rounded_rectangle((100,1260,980,1440),radius=14,fill=(235,245,252))
            d.text((540,1320),"✓  造负压，油烟跟着气流走",font=FONT_L,fill=AIR,anchor="mm")
            d.text((540,1395),"方向对了，才不扑脸",font=FONT_S,fill=MUTED,anchor="mm")
    return img.convert("RGB")

def draw_cutaway(t,w,h,time_sec=0.0):
    img=_paper_bg(w,h,113).convert("RGBA"); d=ImageDraw.Draw(img)
    _fade_text(d,(540,95),"拆开看：油烟走哪条路",FONT_L,INK,_spring(t,0,0.2))
    show=_spring(t,0.05,0.28)
    if show>0:
        p=_range_hood(d,540,520,scale=1.15,time_sec=time_sec,suction=0.9,show_fan=True,dirty=0.2)
        if t>0.25: _callout(d,p["fan"],(760,360),"离心叶轮",AIR,_spring(t,0.22,0.25))
        if t>0.4: _callout(d,p["mesh"],(760,560),"油网拦油滴",OIL,_spring(t,0.4,0.25))
        if t>0.55: _callout(d,(540,400),(120,320),"烟道排出",MUTED,_spring(t,0.55,0.25))
    if t>0.65:
        d.rounded_rectangle((100,1050,980,1280),radius=14,fill=(255,253,248))
        d.text((540,1120),"集烟罩像漏斗：先拢住，再抽走",font=FONT_M,fill=INK,anchor="mm")
        d.text((540,1200),"止回阀防止外面味道倒灌",font=FONT_S,fill=MUTED,anchor="mm")
    return img.convert("RGB")

def draw_cycle(t,w,h,time_sec=0.0):
    img=_paper_bg(w,h,117).convert("RGBA"); d=ImageDraw.Draw(img)
    d.text((540,90),"油烟四步走",font=FONT_L,fill=INK,anchor="mm")
    active=-1 if t<0.06 else min(3,int((t-0.06)/0.2))
    _range_hood(d,540,420,scale=1.0,time_sec=time_sec,suction=0.3 if active<0 else 1.0,show_fan=True)
    steps=["上升","吸入","拦油","排出"]; tips=["① 热油气向上升","② 罩口负压，气流带着油烟涌入","③ 大油滴撞在油网上凝结","④ 细雾随烟道排出室外"]
    for i,name in enumerate(steps): _step_ring(d,180+i*240,880,i+1,name,i==active,time_sec)
    if active>=0:
        d.rounded_rectangle((80,1050,1000,1170),radius=14,fill=(255,253,248))
        d.text((540,1110),tips[active],font=FONT_M,fill=INK,anchor="mm")
    if t>0.8: d.text((540,1400),"锅要落在有效吸烟区里，离太远吸不住",font=FONT_S,fill=MUTED,anchor="mm")
    return img.convert("RGB")

def draw_analogy(t,w,h,time_sec=0.0):
    img=_paper_bg(w,h,119).convert("RGBA"); d=ImageDraw.Draw(img)
    d.text((540,95),"几个现象，一次说清",font=FONT_L,fill=INK,anchor="mm")
    cards=[(0.08,"油网很脏为什么变弱？","进风阻力大，负压不够"),(0.32,"烟道太长弯太多？","排气不畅，风机更吃力"),(0.55,"为什么有时会倒烟？","外压变化 + 止回/密封不好")]
    for idx,(start,title,sub) in enumerate(cards):
        a=_spring(t,start,0.25)
        if a<=0: continue
        y=250+idx*310+(1-a)*40
        d.rounded_rectangle((90,y,990,y+270),radius=16,fill=(255,253,248),outline=LINE,width=2)
        d.text((540,y+40),title,font=FONT_M,fill=INK,anchor="mm")
        d.text((540,y+95),sub,font=FONT_S,fill=MUTED,anchor="mm")
        if idx==0:
            _range_hood(d,300,y+185,scale=0.55,time_sec=time_sec,suction=0.25,dirty=0.9,show_fan=True)
            d.text((300,y+245),"油腻 ✗",font=FONT_XS,fill=HOT,anchor="mm")
            _range_hood(d,780,y+185,scale=0.55,time_sec=time_sec,suction=1.0,dirty=0.1,show_fan=True)
            d.text((780,y+245),"干净 ✓",font=FONT_XS,fill=GREEN,anchor="mm")
        elif idx==1:
            for i in range(4):
                _sketch_line(d,(250+i*50,y+200),(300+i*50,y+160),AIR if i<2 else MUTED,3,i)
            d.text((540,y+230),"弯头越多 → 风阻越大",font=FONT_XS,fill=ACCENT,anchor="mm")
        else:
            for i in range(5):
                u=(time_sec*0.5+i/5)%1.0; y2=_lerp(y+140,y+230,u)
                d.ellipse((520+math.sin(i)*30-5,y2-5,520+math.sin(i)*30+5,y2+5),fill=OIL_LT)
            d.text((540,y+245),"气味倒灌",font=FONT_XS,fill=HOT,anchor="mm")
    if t>0.78:
        d.text((540,1250),"靠气流路径和压差吃饭",font=FONT_L,fill=INK,anchor="mm")
        d.text((540,1320),"清洁维护决定它有没有劲",font=FONT_M,fill=AIR,anchor="mm")
    return img.convert("RGB")

def draw_outro(t,w,h,time_sec=0.0):
    img=_paper_bg(w,h,121).convert("RGBA"); d=ImageDraw.Draw(img)
    a=_spring(t,0,0.35)
    _range_hood(d,540,int(420+(1-a)*30),scale=1.1,time_sec=time_sec,suction=0.95,show_fan=True)
    if t>0.2:
        d.rounded_rectangle((80,820,1000,1020),radius=16,fill=(255,253,248),outline=ACCENT,width=2)
        d.text((540,880),"口诀记住",font=FONT_S,fill=MUTED,anchor="mm")
        d.text((540,950),"叶轮造负压 · 油网拦油滴 · 烟道送出屋",font=FONT_L,fill=INK,anchor="mm")
    if t>0.5:
        b=_spring(t,0.5,0.25); _ken_badge(d,1140,b,0.9+0.1*b)
        _fade_text(d,(540,1230),"关注身边原理 · 我是 Ken",FONT_L,INK,b)
        _fade_text(d,(540,1300),"明天继续 3 分钟了解下一个原理",FONT_M,ACCENT,_spring(t,0.56,0.25))
    if t>0.75:
        d.text((540,1480),"评论区：燃气灶 / 热水器 / 空气净化器？",font=FONT_S,fill=(*MUTED,int(255*(0.6+0.4*_pulse(time_sec,2)))),anchor="mm")
    return img.convert("RGB")

SCENE_DRAWERS={"hook":draw_hook,"cutaway":draw_cutaway,"cycle":draw_cycle,"analogy":draw_analogy,"outro":draw_outro}
def draw_scene(scene_name,t,width=1080,height=1920,*,time_sec=None):
    ts=time_sec if time_sec is not None else t*120.0
    return SCENE_DRAWERS.get(scene_name,draw_hook)(_clamp01(t),width,height,ts)
