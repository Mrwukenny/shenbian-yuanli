"""吹风机分集 · 纪录片手绘风 2D。"""

from __future__ import annotations

import math
import random
from typing import Callable

from PIL import Image, ImageDraw, ImageFont

PAPER=(248,245,238); WALL=(242,238,230); FLOOR=(218,214,206); INK=(38,36,34); MUTED=(110,105,98)
ACCENT=(180,75,45); AIR=(70,130,175); AIR_LT=(180,210,235); HOT=(195,90,55); HOT_LT=(240,190,150)
LINE=(180,175,168); WHITE=(252,250,246); METAL=(168,172,178); METAL_DK=(105,110,118)
BODY=(240,120,90); BODY_DK=(200,90,70); WIRE=(60,60,65); GREEN=(80,160,110)


def _font(size, bold=False):
    paths=[r"C:\Windows\Fonts\msyhbd.ttc",r"C:\Windows\Fonts\msyh.ttc"] if bold else [r"C:\Windows\Fonts\msyh.ttc",r"C:\Windows\Fonts\msyhbd.ttc"]
    for p in paths:
        try: return ImageFont.truetype(p,size=size)
        except OSError: continue
    return ImageFont.load_default()

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

def _hair_dryer(d,cx,cy,*,scale=1.0,time_sec=0.0,heat=1.0,flow=1.0,blocked=False,cutaway=False):
    s=scale
    # body barrel horizontal-ish
    bw,bh=260*s,110*s; x0,y0=cx-bw/2,cy-bh/2
    d.rounded_rectangle((x0+3,y0+4,x0+bw+3,y0+bh+4),radius=28*s,fill=(200,100,80))
    d.rounded_rectangle((x0,y0,x0+bw,y0+bh),radius=28*s,fill=BODY,outline=INK,width=2)
    # nozzle
    d.polygon([(x0+bw-10,y0+20*s),(x0+bw+50*s,y0+35*s),(x0+bw+50*s,y0+bh-35*s),(x0+bw-10,y0+bh-20*s)],fill=BODY_DK,outline=INK)
    # handle
    d.rounded_rectangle((cx-25*s,y0+bh-10,cx+25*s,y0+bh+90*s),radius=12*s,fill=BODY_DK,outline=INK,width=2)
    # switch
    d.rounded_rectangle((cx-12*s,y0+bh+25*s,cx+12*s,y0+bh+55*s),radius=4,fill=GREEN if flow>0.3 else METAL)
    # inlet grill
    for i in range(5):
        d.line((x0+18*s+i*6,y0+25*s,x0+18*s+i*6,y0+bh-25*s),fill=METAL_DK,width=2)
    if cutaway:
        # heater coils
        for i in range(4):
            yy=y0+28*s+i*16*s
            col=HOT if heat>0.3 else METAL
            _sketch_line(d,(x0+80*s,yy),(x0+bw-40*s,yy),col,3,i)
        # fan
        fx,fy=x0+50*s,cy; ang=time_sec*10*flow
        for k in range(3):
            a=ang+k*2.094
            d.line((fx,fy,fx+math.cos(a)*18*s,fy+math.sin(a)*18*s),fill=METAL_DK,width=3)
    # airflow out
    if flow>0.2 and not blocked:
        for i in range(8):
            u=(time_sec*1.2+i/8)%1.0
            x=_lerp(x0+bw+50*s,x0+bw+50*s+90*s,u)
            y=cy+math.sin(time_sec*6+i)*12*(1 if heat>0.3 else 0.5)
            col=HOT_LT if heat>0.3 else AIR_LT
            d.ellipse((x-5,y-5,x+5,y+5),fill=col)
    elif blocked:
        # heat buildup
        pulse=_pulse(time_sec,6,0.7,1.0)
        d.ellipse((cx-40*s*pulse,cy-40*s*pulse,cx+40*s*pulse,cy+40*s*pulse),outline=HOT,width=3)
    return {"nozzle":(x0+bw+40*s,cy),"heater":(cx,cy),"inlet":(x0+20*s,cy)}

def _step_ring(d,x,y,num,name,active,ts):
    r=(34 if active else 26)*(_pulse(ts,5,0.92,1.08) if active else 1)
    d.ellipse((x-r,y-r,x+r,y+r),fill=HOT if active else WHITE,outline=HOT if active else AIR,width=3)
    d.text((x,y),str(num),font=FONT_M,fill=WHITE if active else AIR,anchor="mm")
    if active: d.text((x,y+r+26),name,font=FONT_S,fill=HOT,anchor="mm")

def draw_hook(t,w,h,time_sec=0.0):
    dx,_=_cam_drift(time_sec); img=_paper_bg(w,h,131).convert("RGBA"); d=ImageDraw.Draw(img)
    intro=_spring(t,0,0.3)
    if intro>0:
        _ken_badge(d,170,intro,0.85+0.15*intro)
        _fade_text(d,(540+dx,300),"我是 Ken",FONT_HERO,INK,intro,dy=(1-intro)*36)
        _fade_text(d,(540,390),"挑战每天用 3 分钟",FONT_L,INK,_spring(t,0.05,0.28))
        _fade_text(d,(540,460),"带你了解一个身边原理",FONT_M,MUTED,_spring(t,0.1,0.28))
        _fade_text(d,(540,550),"今天：吹风机怎么又吹又热",FONT_L,ACCENT,_spring(t,0.16,0.3))
    show=_ease(_scene_t(t,0.28,0.45))
    if show>0: _hair_dryer(d,540+dx,int(880+(1-show)*40),scale=1.2,time_sec=time_sec,heat=1 if t>0.55 else 0,flow=0.9,cutaway=t>0.55)
    if t>0.5:
        wrong=_ease(_scene_t(t,0.5,0.64)); right=_spring(t,0.66,0.28)
        if wrong>0 and right<0.35:
            d.rounded_rectangle((120,1280,960,1380),radius=12,fill=(255,240,235))
            d.text((540,1330),"❌ 不是一个「热风扇」包办",font=FONT_M,fill=ACCENT,anchor="mm")
        if right>0:
            d.rounded_rectangle((100,1260,980,1440),radius=14,fill=(255,245,240))
            d.text((540,1320),"✓  风扇造风 · 电热丝加热",font=FONT_L,fill=HOT,anchor="mm")
            d.text((540,1395),"风是搬运工，热是路上加的料",font=FONT_S,fill=MUTED,anchor="mm")
    return img.convert("RGB")

def draw_cutaway(t,w,h,time_sec=0.0):
    img=_paper_bg(w,h,133).convert("RGBA"); d=ImageDraw.Draw(img)
    _fade_text(d,(540,95),"拆开看：风和热怎么分工",FONT_L,INK,_spring(t,0,0.2))
    show=_spring(t,0.05,0.28)
    if show>0:
        p=_hair_dryer(d,500,520,scale=1.35,time_sec=time_sec,heat=0.8,flow=1.0,cutaway=True)
        if t>0.25: _callout(d,p["inlet"],(120,400),"进风滤网",MUTED,_spring(t,0.22,0.25))
        if t>0.4: _callout(d,p["heater"],(760,420),"电热丝",HOT,_spring(t,0.4,0.25))
        if t>0.55: _callout(d,p["nozzle"],(760,600),"热风喷出",AIR,_spring(t,0.55,0.25))
    if t>0.65:
        d.rounded_rectangle((100,1000,980,1280),radius=14,fill=(255,253,248))
        d.text((540,1080),"温控 + 保险丝 = 过热就断电",font=FONT_M,fill=INK,anchor="mm")
        d.text((540,1160),"档位：控制风速，以及热丝通不通电",font=FONT_S,fill=MUTED,anchor="mm")
        d.text((540,1225),"所以有冷风 / 热风 / 强弱风",font=FONT_S,fill=ACCENT,anchor="mm")
    return img.convert("RGB")

def draw_cycle(t,w,h,time_sec=0.0):
    img=_paper_bg(w,h,137).convert("RGBA"); d=ImageDraw.Draw(img)
    d.text((540,90),"热风怎么来的",font=FONT_L,fill=INK,anchor="mm")
    active=-1 if t<0.06 else min(3,int((t-0.06)/0.2))
    heat=0 if active==3 and t>0.7 else (1.0 if active>=1 else 0.0)
    # for step 3 cold wind demo near end - actually steps: 气流,发热,掠过加热,蒸发/冷风
    _hair_dryer(d,540,420,scale=1.15,time_sec=time_sec,heat=0 if active>=3 else (1 if active>=1 else 0),flow=1 if active>=0 else 0.2,cutaway=True)
    steps=["造风","发热","加热空气","吹干/冷风"]
    tips=["① 叶轮旋转，形成进出气流","② 电热丝电阻发热，温度迅速升高","③ 空气掠过热丝，带走热量喷出","④ 热风加速水分蒸发；关加热=冷风档"]
    for i,name in enumerate(steps): _step_ring(d,160+i*250,880,i+1,name,i==active,time_sec)
    if active>=0:
        d.rounded_rectangle((80,1050,1000,1170),radius=14,fill=(255,253,248))
        d.text((540,1110),tips[active],font=FONT_M,fill=INK,anchor="mm")
    if t>0.82: d.text((540,1400),"关掉加热只留风扇，就是冷风档",font=FONT_S,fill=MUTED,anchor="mm")
    return img.convert("RGB")

def draw_analogy(t,w,h,time_sec=0.0):
    img=_paper_bg(w,h,139).convert("RGBA"); d=ImageDraw.Draw(img)
    d.text((540,95),"使用注意背后的原理",font=FONT_L,fill=INK,anchor="mm")
    cards=[(0.08,"为什么不能堵出风口？","气流一停，热散不出去，极易过热"),(0.32,"滤网为什么要清理？","进风不足 → 风量掉 → 积热"),(0.55,"为什么离头皮太近易烫？","出风口温度高，距离近热通量更大")]
    for idx,(start,title,sub) in enumerate(cards):
        a=_spring(t,start,0.25)
        if a<=0: continue
        y=250+idx*310+(1-a)*40
        d.rounded_rectangle((90,y,990,y+270),radius=16,fill=(255,253,248),outline=LINE,width=2)
        d.text((540,y+40),title,font=FONT_M,fill=INK,anchor="mm")
        d.text((540,y+95),sub,font=FONT_S,fill=MUTED,anchor="mm")
        if idx==0:
            _hair_dryer(d,540,y+185,scale=0.7,time_sec=time_sec,heat=1,flow=0.5,blocked=True,cutaway=True)
            d.text((540,y+245),"危险：堵口积热",font=FONT_XS,fill=HOT,anchor="mm")
        elif idx==1:
            for i in range(6):
                d.line((400+i*20,y+150,400+i*20,y+220),fill=METAL_DK,width=3)
                d.ellipse((395+i*20,y+160+i*3,410+i*20,y+175+i*3),fill=(80,70,60))
            d.text((540,y+245),"滤网堵住了",font=FONT_XS,fill=ACCENT,anchor="mm")
        else:
            _hair_dryer(d,400,y+185,scale=0.55,time_sec=time_sec,heat=1,flow=1,cutaway=False)
            # head silhouette
            d.ellipse((700,y+140,820,y+260),fill=(235,200,170),outline=INK,width=1)
            d.text((760,y+245),"太近 ✗",font=FONT_XS,fill=HOT,anchor="mm")
    if t>0.78:
        d.text((540,1250),"风 + 热 组合拳",font=FONT_L,fill=INK,anchor="mm")
        d.text((540,1320),"通风永远比加热优先",font=FONT_M,fill=HOT,anchor="mm")
    return img.convert("RGB")

def draw_outro(t,w,h,time_sec=0.0):
    img=_paper_bg(w,h,141).convert("RGBA"); d=ImageDraw.Draw(img)
    a=_spring(t,0,0.35)
    _hair_dryer(d,540,int(450+(1-a)*30),scale=1.25,time_sec=time_sec,heat=0.9,flow=1.0,cutaway=True)
    if t>0.2:
        d.rounded_rectangle((80,780,1000,1000),radius=16,fill=(255,253,248),outline=ACCENT,width=2)
        d.text((540,840),"口诀记住",font=FONT_S,fill=MUTED,anchor="mm")
        d.text((540,910),"风扇造风 · 电热丝加热",font=FONT_L,fill=INK,anchor="mm")
        d.text((540,970),"过热保护守底线",font=FONT_L,fill=HOT,anchor="mm")
    if t>0.5:
        b=_spring(t,0.5,0.25); _ken_badge(d,1120,b,0.9+0.1*b)
        _fade_text(d,(540,1210),"关注身边原理 · 我是 Ken",FONT_L,INK,b)
        _fade_text(d,(540,1280),"明天继续 3 分钟了解下一个原理",FONT_M,ACCENT,_spring(t,0.56,0.25))
    if t>0.75:
        d.text((540,1460),"评论区：电动牙刷 / 剃须刀 / 加湿器？",font=FONT_S,fill=(*MUTED,int(255*(0.6+0.4*_pulse(time_sec,2)))),anchor="mm")
    return img.convert("RGB")

SCENE_DRAWERS={"hook":draw_hook,"cutaway":draw_cutaway,"cycle":draw_cycle,"analogy":draw_analogy,"outro":draw_outro}
def draw_scene(scene_name,t,width=1080,height=1920,*,time_sec=None):
    ts=time_sec if time_sec is not None else t*120.0
    return SCENE_DRAWERS.get(scene_name,draw_hook)(_clamp01(t),width,height,ts)
