"""电饭煲分集 · 纪录片手绘风 2D。"""

from __future__ import annotations

import math
import random
from typing import Callable

from PIL import Image, ImageDraw

from pipeline.fonts import load_cjk_font as _font

PAPER=(248,245,238); WALL=(242,238,230); FLOOR=(218,214,206); INK=(38,36,34); MUTED=(110,105,98)
ACCENT=(180,75,45); HOT=(195,90,55); HOT_LT=(240,190,150); LINE=(180,175,168)
WHITE=(252,250,246); METAL=(168,172,178); METAL_DK=(105,110,118); BODY=(240,242,245)
BODY_DK=(200,205,210); RICE=(230,210,160); WATER=(120,175,210); GREEN=(80,160,110)


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

def _steam(d,cx,cy,ts,n=6,s=1.0):
    for i in range(n):
        u=(ts*0.5+i/n)%1.0
        x=cx+math.sin(ts*2+i)*12; y=cy-u*70*s; r=4+8*u
        d.ellipse((x-r,y-r,x+r,y+r),fill=(*MUTED,int(110*(1-u)*s)))

def _cooker(d,cx,cy,*,scale=1.0,ts=0.0,lid=0.2,heat=0.6,cook=0.5,keep=False,cutaway=False):
    s=scale; w,h=260*s,280*s; x0,y0=cx-w/2,cy-h/2
    d.rounded_rectangle((x0+4,y0+6,x0+w+4,y0+h+6),radius=20*s,fill=(200,196,190))
    d.rounded_rectangle((x0,y0,x0+w,y0+h),radius=20*s,fill=BODY,outline=INK,width=2)
    # lid
    lid_h=max(8,50*s*(1-lid*0.7))
    d.ellipse((x0+20*s,y0-10*s,x0+w-20*s,y0+lid_h),fill=BODY_DK,outline=INK,width=2)
    d.ellipse((cx-12*s,y0-18*s,cx+12*s,y0-2*s),fill=METAL)  # valve
    if heat>0.3: _steam(d,cx,y0-20*s,ts,n=6,s=heat)
    # pot inside
    pot=(x0+30*s,y0+50*s,x0+w-30*s,y0+h-50*s)
    d.rounded_rectangle(pot,radius=10*s,fill=METAL,outline=METAL_DK,width=2)
    water_y=_lerp(pot[3]-8,pot[1]+20,_clamp01(0.55-cook*0.25))
    if water_y < pot[3]-6:
        d.rounded_rectangle((pot[0]+6,water_y,pot[2]-6,pot[3]-6),radius=6,fill=(*WATER,150))
    # rice grains
    for i in range(12):
        px=pot[0]+20+(i%6)*28*s; py=water_y+10+(i//6)*16*s+math.sin(ts*2+i)*2
        d.ellipse((px-5,py-4,px+5,py+4),fill=RICE,outline=INK,width=1)
    # heater plate
    hx0,hy0=x0+40*s,y0+h-45*s
    d.rounded_rectangle((hx0,hy0,x0+w-40*s,y0+h-12*s),radius=6,fill=HOT if heat>0.4 else METAL_DK,outline=INK,width=1)
    # magnet sensor
    d.ellipse((cx-18*s,hy0-8*s,cx+18*s,hy0+28*s),fill=(80,84,90),outline=INK,width=2)
    if keep:
        d.text((cx,y0+h+18*s),"保温",font=FONT_XS,fill=GREEN,anchor="mm")
    elif heat>0.4:
        d.text((cx,y0+h+18*s),"加热中",font=FONT_XS,fill=HOT,anchor="mm")
    if cutaway:
        d.text((cx,hy0+10*s),"磁钢",font=FONT_XS,fill=WHITE,anchor="mm")
    return {"heater":(cx,hy0+10*s),"pot":(cx,(pot[1]+pot[3])/2),"valve":(cx,y0-10*s)}

def _step_ring(d,x,y,num,name,active,ts):
    r=(34 if active else 26)*(_pulse(ts,5,0.92,1.08) if active else 1)
    d.ellipse((x-r,y-r,x+r,y+r),fill=HOT if active else WHITE,outline=HOT,width=3)
    d.text((x,y),str(num),font=FONT_M,fill=WHITE if active else HOT,anchor="mm")
    if active: d.text((x,y+r+26),name,font=FONT_S,fill=HOT,anchor="mm")

def draw_hook(t,w,h,time_sec=0.0):
    dx,_=_cam_drift(time_sec); img=_paper_bg(w,h,151).convert("RGBA"); d=ImageDraw.Draw(img)
    intro=_spring(t,0,0.3)
    if intro>0:
        _ken_badge(d,170,intro,0.85+0.15*intro)
        _fade_text(d,(540+dx,300),"我是 Ken",FONT_HERO,INK,intro,dy=(1-intro)*36)
        _fade_text(d,(540,390),"挑战每天用 3 分钟",FONT_L,INK,_spring(t,0.05,0.28))
        _fade_text(d,(540,460),"带你了解一个身边原理",FONT_M,MUTED,_spring(t,0.1,0.28))
        _fade_text(d,(540,550),"今天：电饭煲怎么煮熟又保温",FONT_L,ACCENT,_spring(t,0.16,0.3))
    show=_ease(_scene_t(t,0.28,0.45))
    if show>0:
        _cooker(d,540+dx,int(880+(1-show)*40),scale=1.15,ts=time_sec,lid=0.4,heat=0.8 if t>0.5 else 0.3,cook=0.4,cutaway=t>0.55)
    if t>0.5:
        wrong=_ease(_scene_t(t,0.5,0.64)); right=_spring(t,0.66,0.28)
        if wrong>0 and right<0.35:
            d.rounded_rectangle((120,1280,960,1380),radius=12,fill=(255,240,235))
            d.text((540,1330),"❌ 不只是定时关火的电锅",font=FONT_M,fill=ACCENT,anchor="mm")
        if right>0:
            d.rounded_rectangle((100,1260,980,1440),radius=14,fill=(255,245,240))
            d.text((540,1320),"✓  用水干升温当信号，自动跳保温",font=FONT_L,fill=HOT,anchor="mm")
            d.text((540,1395),"感知温度，不是瞎猜时间",font=FONT_S,fill=MUTED,anchor="mm")
    return img.convert("RGB")

def draw_cutaway(t,w,h,time_sec=0.0):
    img=_paper_bg(w,h,153).convert("RGBA"); d=ImageDraw.Draw(img)
    _fade_text(d,(540,95),"拆开看：谁在控制火候",FONT_L,INK,_spring(t,0,0.2))
    show=_spring(t,0.05,0.28)
    if show>0:
        p=_cooker(d,500,560,scale=1.25,ts=time_sec,lid=0.5,heat=0.7,cook=0.45,cutaway=True)
        if t>0.25: _callout(d,p["heater"],(760,700),"加热盘",HOT,_spring(t,0.22,0.25))
        if t>0.4: _callout(d,p["heater"],(120,720),"磁钢限温器",MUTED,_spring(t,0.4,0.25))
        if t>0.55: _callout(d,p["valve"],(760,360),"蒸汽阀",MUTED,_spring(t,0.55,0.25))
    if t>0.65:
        d.rounded_rectangle((100,1050,980,1280),radius=14,fill=(255,253,248))
        d.text((540,1120),"约 103°C：磁钢失磁 → 跳到保温",font=FONT_M,fill=INK,anchor="mm")
        d.text((540,1200),"保温用小功率，维持温度不再猛烧",font=FONT_S,fill=MUTED,anchor="mm")
    return img.convert("RGB")

def draw_cycle(t,w,h,time_sec=0.0):
    img=_paper_bg(w,h,157).convert("RGBA"); d=ImageDraw.Draw(img)
    d.text((540,90),"一锅饭的四步",font=FONT_L,fill=INK,anchor="mm")
    active=-1 if t<0.06 else min(3,int((t-0.06)/0.2))
    heat=1.0 if active in (0,1,2) else 0.2
    keep=active>=3
    cook=0.2+0.25*max(0,active)
    _cooker(d,540,420,scale=1.1,ts=time_sec,lid=0.35,heat=heat,cook=cook,keep=keep,cutaway=True)
    steps=["升温沸腾","吸水糊化","水干升温","跳闸保温"]
    tips=["① 加热盘加热，水升到沸腾","② 米吸水膨胀，淀粉糊化变熟","③ 水快干，锅底温度迅速升高","④ 磁钢失磁跳闸，转入保温"]
    for i,name in enumerate(steps): _step_ring(d,160+i*250,900,i+1,name,i==active,time_sec)
    if active>=0:
        d.rounded_rectangle((80,1080,1000,1200),radius=14,fill=(255,253,248))
        d.text((540,1140),tips[active],font=FONT_M,fill=INK,anchor="mm")
    if t>0.85: d.text((540,1420),"水在时顶在沸点；水干了，温度信号才出现",font=FONT_S,fill=MUTED,anchor="mm")
    return img.convert("RGB")

def draw_analogy(t,w,h,time_sec=0.0):
    img=_paper_bg(w,h,159).convert("RGBA"); d=ImageDraw.Draw(img)
    d.text((540,95),"几个现象，一次说清",font=FONT_L,fill=INK,anchor="mm")
    cards=[(0.08,"水放太多会怎样？","变稀、易溢锅，节奏被打乱"),(0.32,"内胆没放正？","接触不良，热传不上，限温失准"),(0.55,"保温太久饭发黄？","低温仍在失水，缓慢发生反应")]
    for idx,(start,title,sub) in enumerate(cards):
        a=_spring(t,start,0.25)
        if a<=0: continue
        y=250+idx*310+(1-a)*40
        d.rounded_rectangle((90,y,990,y+270),radius=16,fill=(255,253,248),outline=LINE,width=2)
        d.text((540,y+40),title,font=FONT_M,fill=INK,anchor="mm")
        d.text((540,y+95),sub,font=FONT_S,fill=MUTED,anchor="mm")
        if idx==0:
            _cooker(d,540,y+185,scale=0.55,ts=time_sec,heat=0.9,cook=0.1,lid=0.6)
            for i in range(5): _steam(d,540+(i-2)*20,y+120,time_sec+i,n=2,s=1.2)
        elif idx==1:
            _cooker(d,400,y+185,scale=0.5,ts=time_sec,heat=0.3,cook=0.5)
            d.text((400,y+245),"歪了 ✗",font=FONT_XS,fill=HOT,anchor="mm")
            _cooker(d,760,y+185,scale=0.5,ts=time_sec,heat=0.8,cook=0.5)
            d.text((760,y+245),"放正 ✓",font=FONT_XS,fill=GREEN,anchor="mm")
        else:
            _cooker(d,540,y+185,scale=0.55,ts=time_sec,heat=0.15,cook=0.9,keep=True)
            d.text((540,y+245),"保温过久",font=FONT_XS,fill=ACCENT,anchor="mm")
    if t>0.78:
        d.text((540,1250),"温度触发的自动厨师",font=FONT_L,fill=INK,anchor="mm")
        d.text((540,1320),"核心是限温，不只是计时",font=FONT_M,fill=HOT,anchor="mm")
    return img.convert("RGB")

def draw_outro(t,w,h,time_sec=0.0):
    img=_paper_bg(w,h,161).convert("RGBA"); d=ImageDraw.Draw(img)
    a=_spring(t,0,0.35)
    _cooker(d,540,int(460+(1-a)*30),scale=1.2,ts=time_sec,lid=0.3,heat=0.5,cook=0.7,keep=True,cutaway=True)
    if t>0.2:
        d.rounded_rectangle((80,820,1000,1020),radius=16,fill=(255,253,248),outline=ACCENT,width=2)
        d.text((540,880),"口诀记住",font=FONT_S,fill=MUTED,anchor="mm")
        d.text((540,950),"加热盘煮水 · 水干升温 · 磁钢跳保温",font=FONT_L,fill=INK,anchor="mm")
    if t>0.5:
        b=_spring(t,0.5,0.25); _ken_badge(d,1140,b,0.9+0.1*b)
        _fade_text(d,(540,1230),"关注身边原理 · 我是 Ken",FONT_L,INK,b)
        _fade_text(d,(540,1300),"明天继续 3 分钟了解下一个原理",FONT_M,ACCENT,_spring(t,0.56,0.25))
    if t>0.75:
        d.text((540,1480),"评论区：豆浆机 / 空气炸锅 / 电热水壶？",font=FONT_S,fill=(*MUTED,int(255*(0.6+0.4*_pulse(time_sec,2)))),anchor="mm")
    return img.convert("RGB")

SCENE_DRAWERS={"hook":draw_hook,"cutaway":draw_cutaway,"cycle":draw_cycle,"analogy":draw_analogy,"outro":draw_outro}
def draw_scene(scene_name,t,width=1080,height=1920,*,time_sec=None):
    ts=time_sec if time_sec is not None else t*120.0
    return SCENE_DRAWERS.get(scene_name,draw_hook)(_clamp01(t),width,height,ts)
