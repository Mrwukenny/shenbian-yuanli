import * as T from 'three';import {C,mat,mesh,cyl,ring,tube,makePump,makeFlosser,makeTeeth} from './model.js';
import {pumpKinematics} from './kinematics.mjs';
const renderer=new T.WebGLRenderer({canvas:document.querySelector('canvas'),alpha:true,antialias:true,preserveDrawingBuffer:true});renderer.setSize(1080,930,false);renderer.setPixelRatio(1);renderer.outputColorSpace=T.SRGBColorSpace;renderer.setClearColor(0,0);
const scene=new T.Scene(),camera=new T.PerspectiveCamera(34,1080/930,.1,60);scene.add(new T.HemisphereLight(0xcbeaff,0x211437,2.1));for(const [c,i,p] of [[0xffffff,2.7,[4,6,6]],[0x9b78fa,1.8,[-5,4,-3]],[0x22d3ee,1.3,[2,4,-5]]]){let l=new T.DirectionalLight(c,i);l.position.fromArray(p);scene.add(l)}
const device=makeFlosser(),pump=makePump(),oral=makeTeeth();scene.add(device.root,pump.root,oral.root);
const platform=new T.Group();scene.add(platform);cyl(1.7,.07,mat(0x14283e,{shininess:15}),[0,-.06,0],platform);ring(1.69,.013,-.018,mat(0x7557bd,{emissive:0x261249}),platform);ring(1.4,.007,-.015,mat(0x294e6c),platform);
for(let i=0;i<24;i++){let a=i*Math.PI/12;let tick=mesh(new T.BoxGeometry(.018,.007,.08),mat(0x52728b),[1.53*Math.sin(a),-.012,1.53*Math.cos(a)],platform);tick.rotation.y=a}
const brush=new T.Group();oral.root.add(brush);tube([[-1.35,-.95,.6],[-1.17,-.4,.6],[-.9,.25,.6]],.065,mat(C.motion),brush);let head=mesh(new T.BoxGeometry(.22,.43,.1),mat(C.white),[-.85,.34,.6],brush);for(let i=0;i<24;i++){let br=cyl(.012,.16,mat(0xbbeff1),[-.93+(i%4)*.05,.19+Math.floor(i/4)*.055,.72],brush);br.rotation.x=Math.PI/2}
const $=s=>document.querySelector(s),title=$('#title'),sub=$('#sub'),badge=$('#badge'),chapter=$('#chapter'),legend=[...document.querySelectorAll('#legend div')],valves=$('#valves'),wavebox=$('#wavebox');
const labels=[];const defs=[['nozzle','细喷嘴',[0,3.58,0],'right',480],['body','机身 / 电路',[.4,2.1,.1],'right',680],['motor','电机 / 小水泵',[0,2,.15],'left',840],['intake','吸水管',[.3,.8,.1],'right',1015],['tank','水箱',[-.55,.6,.1],'left',1130]];
for(const [key,text,pos,side,y]of defs){let div=document.createElement('div');div.className='label';div.textContent=text;div.style.top=y+'px';div.style[side]='100px';$('#callouts').append(div);let line=document.createElementNS('http://www.w3.org/2000/svg','polyline');line.setAttribute('fill','none');line.setAttribute('stroke','#647e9f');line.setAttribute('stroke-width','2');$('#leaders').append(line);labels.push({key,div,line,pos,side,y})}
const pumpLabels=[];for(const [key,text,point,side,y] of [['motor','电机',[-.65,0,-.08],'left',640],['crank','偏心轮',[-.65,0,.55],'left',1055],['piston','活塞',[.3,0,0],'right',980],['chamber','泵腔',[.9,0,.1],'left',700],['inlet','进水阀',[.98,-.57,0],'right',1080],['outlet','出水阀',[1.16,.6,0],'right',660]]){const div=document.createElement('div');div.className='label';div.textContent=text;div.style[side]='100px';div.style.top=y+'px';$('#callouts').append(div);const line=document.createElementNS('http://www.w3.org/2000/svg','polyline');line.setAttribute('fill','none');line.setAttribute('stroke','#7d8da7');line.setAttribute('stroke-width','2');$('#leaders').append(line);pumpLabels.push({key,div,line,point,side,y})}
const clamp=(x,a=0,b=1)=>Math.max(a,Math.min(b,x)),smooth=x=>{x=clamp(x);return x*x*(3-2*x)},ramp=(t,a,b)=>smooth((t-a)/(b-a)),mix=(a,b,x)=>a+(b-a)*x;
const dummy=new T.Object3D(),v0=new T.Vector3(),v1=new T.Vector3(),mid=new T.Vector3(),up=new T.Vector3(0,1,0),measure=document.createElement('canvas').getContext('2d');
let lastPumpState=null;
function pumpState(theta){const k=pumpKinematics(theta);return{...k,pin:new T.Vector3(k.pin[0],k.pin[1],k.pin[2])}}
function updatePump(p,s,t){p.gear.rotation.z=s.theta;p.piston.position.x=s.slider;p.pistonSeal.position.x=s.slider;p.pistonPin.position.x=s.slider;v1.set(s.slider,0,.625);p.rod.position.copy(s.pin).add(v1).multiplyScalar(.5);mid.copy(v1).sub(s.pin);p.rod.scale.y=mid.length();p.rod.quaternion.setFromUnitVectors(up,mid.normalize());const length=1.25-s.slider;p.fluid.scale.y=length;p.fluid.position.x=(1.25+s.slider)/2;p.inletBall.position.y=-.57+(s.inletOpen?.08:0);p.outletBall.position.y=.6+(s.outletOpen?.08:0);
 for(const [o,n,path,on]of [[p.inDots,8,p.inletPath,s.intake],[p.outDots,10,p.outletPath,s.compression]]){o.visible=on;for(let i=0;i<n;i++){dummy.position.copy(path.getPoint((t*.6+i/n)%1));dummy.scale.setScalar(1);dummy.rotation.set(0,0,0);dummy.updateMatrix();o.setMatrixAt(i,dummy.matrix)}o.instanceMatrix.needsUpdate=true}
 p.jet.visible=s.compression;for(let i=0;i<18;i++){let u=(t*.8+i/18)%1;dummy.position.set(.6-1.25*u,1.58+.26*u-.16*u*u,0);dummy.scale.setScalar(.4+s.stroke*.7);dummy.rotation.set(0,0,0);dummy.updateMatrix();p.jet.setMatrixAt(i,dummy.matrix)}p.jet.instanceMatrix.needsUpdate=true;
}
function thetaAt(t){if(t>=61.96&&t<75.064)return mix(.1*Math.PI,.9*Math.PI,ramp(t,61.96,75.064));if(t>=75.064&&t<84.048)return mix(1.1*Math.PI,1.9*Math.PI,ramp(t,75.064,84.048));return (t*.43)%(Math.PI*2)}
function setLegend(items,colors=['#f5a85d','#c4b5fd','#67e8f9','#cbd5e1']){legend.forEach((e,i)=>{e.textContent=items[i];e.style.borderColor=colors[i];e.style.color=colors[i]})}
function renderAt(t){
 t=clamp(t,0,191.2);const s=pumpState(thetaAt(t));lastPumpState=s;
 device.root.visible=true;pump.root.visible=false;oral.root.visible=false;brush.visible=false;platform.visible=true;
 device.root.position.set(0,0,0);device.root.scale.setScalar(1);device.root.rotation.set(0,0,0);for(const g of [device.tank,device.body,device.nozzle,device.internals])g.position.set(0,0,0);
 device.housing.material.transparent=true;device.housing.material.opacity=1;device.housing.material.depthWrite=true;
 platform.position.set(0,0,0);platform.scale.setScalar(1);pump.root.position.set(0,0,0);pump.root.scale.setScalar(1);oral.root.position.set(0,0,0);oral.root.scale.setScalar(1);oral.spray.position.set(0,0,0);
 valves.style.opacity=0;wavebox.style.opacity=0;badge.style.opacity=1;for(const l of pumpLabels){l.div.style.opacity=0;l.line.style.opacity=0;}for(const l of labels){l.div.style.opacity=0;l.line.style.opacity=0;l.div.classList.remove('active')}
 let orbit=.35+Math.sin(t*.12)*.32,dist=8.05,camY=4.05,lookY=1.95,active='',split=0,showLabels=false;
 title.textContent='冲牙器，把水变成脉冲';sub.textContent='电机 → 水泵 → 水路 → 喷嘴';badge.textContent='水流要真正接触';chapter.textContent='044 / 冲牙器';setLegend(['动力','水路','脉冲','接触']);
 if(t>=9.896&&t<30.816){title.textContent=t<19.744?'水压更大，就一定更干净？':'真正的主角，是电机和泵';sub.textContent='先看机制，再谈使用边界';badge.textContent=t<25.088?'先别急着加挡':'不是隔空清洁';device.housing.material.opacity=.25;device.housing.material.depthWrite=false;}
 if(t>=30.816&&t<52.4){
   chapter.textContent='01 / 拆开水路';title.textContent='水从哪里来，又往哪里去？';sub.textContent='水箱 → 吸水管 → 水泵 → 导水管 → 喷嘴';badge.textContent='代表性结构';split=ramp(t,30.816,32.8);dist=9.45;lookY=2;camY=4.3;orbit=.25+Math.sin((t-31)*.12)*.2;
   device.tank.position.y=-.43*split;device.nozzle.position.y=.65*split;device.body.position.x=.9*split;device.housing.material.opacity=.17;device.housing.material.depthWrite=false;platform.position.y=-.55;showLabels=true;active=t<39.056?'tank':t<43.152?'motor':t<47.488?'nozzle':'body';
 }
 if(t>=52.4&&t<88.24){
   chapter.textContent='02 / 电机怎样推动水';device.root.visible=false;pump.root.visible=true;platform.visible=false;
   badge.style.opacity=0;pump.root.position.y=.1;dist=5.9;camY=2.1;lookY=.15;orbit=.28+Math.sin((t-52)*.15)*.18;
   title.textContent='把转动，变成活塞往复';sub.textContent='电机转动 → 偏心轮 → 连杆 → 活塞';badge.textContent='机械与阀门动作已放慢';
   if(t>=61.96&&t<75.064){title.textContent='第一步：泵腔变大，吸水';sub.textContent='进水端打开 / 出水端关闭'}
   if(t>=75.064&&t<84.048){title.textContent='第二步：泵腔变小，压水';sub.textContent='进水端关闭 / 出水端打开'}
   if(t>=84.048){title.textContent='单向阀，是水路里的单行门';sub.textContent='配合往复动作，建立单向输送'}
   valves.style.opacity=1;setLegend(['电机转','连杆往复','阀门换向','水向前走']);
 }
 if(t>=88.24&&t<111.336){
   badge.style.opacity=0;chapter.textContent='03 / 脉冲从哪里来';device.root.visible=false;pump.root.visible=true;platform.visible=false;dist=6.1;camY=2.25;lookY=.42;orbit=.16+Math.sin((t-88)*.14)*.2;
   title.textContent=t<93.272?'第三步：细喷嘴集中水流':'脉冲，来自泵的周期工作';sub.textContent='不是细嘴自己振动，也不是超声波';badge.textContent='示意波形 · 非真实频率';wavebox.style.opacity=1;
   setLegend(['吸水','压水','流量变化','脉冲输出']);
 }
 if(t>=111.336&&t<173.808){
   device.root.visible=false;pump.root.visible=false;oral.root.visible=true;platform.visible=false;dist=5.35;camY=1.9;lookY=-.05;orbit=.16+Math.sin((t-111)*.12)*.23;chapter.textContent='04 / 水碰到哪里，才清洁哪里';
   title.textContent='第四步：接触，然后带走';sub.textContent='对可接触部位进行辅助清洁';badge.textContent='牙面与水流为原理示意';setLegend(['水流接触','松散碎屑','随水离开','不是钻牙']);
   if(t>=122.288){title.textContent='辅助清洁，不是包办清洁';sub.textContent='接触范围、使用方法和个体情况都重要'}
   if(t>=133.048){title.textContent='牙结石，不靠调高挡冲掉';sub.textContent='硬化沉积物需要专业清洁'}
   if(t>=137.912){chapter.textContent='05 / 为什么会溅';title.textContent='溅得多，不代表清得全';sub.textContent='水遇到牙面，会转向和飞散';setLegend(['压力','流量','脉冲节奏','不同机型不同'])}
   if(t>=152.384){chapter.textContent='06 / 使用边界';title.textContent='低挡起步，沿牙龈线移动';sub.textContent='以说明书和牙医指导为准';badge.textContent='让水能顺利流出来';oral.spray.position.y=Math.sin((t-152)*.6)*.09;setLegend(['低挡起步','缓慢移动','留出排水','不适停用'])}
   if(t>=162.568){title.textContent='疼痛或持续出血，先停用';sub.textContent='别硬冲，咨询牙医';badge.textContent='不要用疼痛换清洁'}
   if(t>=168.08){brush.visible=true;title.textContent='辅助清洁，不替代刷牙';sub.textContent='专业口腔护理，同样不能省略';badge.textContent='刷牙 + 牙间清洁 + 定期检查'}
 }
 if(t>=173.808){
   chapter.textContent='07 / 记住口诀';title.textContent='电机带泵，单向控流';sub.textContent='细嘴出水，清洁靠接触';badge.textContent='把水送到该到的地方';setLegend(['动力','单向','细嘴','接触']);dist=8.1;camY=4.05;lookY=1.95;orbit=.25+Math.sin((t-174)*.16)*.38;
   const u=1-ramp(t,175.5,179.8);device.body.position.x=.5*u;device.nozzle.position.y=.35*u;device.tank.position.y=-.2*u;device.housing.material.opacity=1-.72*u;device.housing.material.depthWrite=u<.1;
   if(t>=180.64){title.textContent='关注身边原理，我是Ken';sub.textContent='明天继续，了解下一个身边原理'}
   if(t>=186.176){title.textContent='下一个，你还想拆什么？';sub.textContent='评论区告诉我'}
 }
 updatePump(device.pump,s,t);updatePump(pump,s,t);
 // Follow the real body water path only from tank upward to the inlet.
 device.jet.visible=device.root.visible&&split<.2&&s.compression;for(let i=0;i<20;i++){let u=(t*.9+i/20)%1;dummy.position.set(-.86-1.0*u,3.91+device.nozzle.position.y+.06*u-.22*u*u,0);dummy.scale.setScalar(.5+s.stroke*.6);dummy.rotation.set(0,0,0);dummy.updateMatrix();device.jet.setMatrixAt(i,dummy.matrix)}device.jet.instanceMatrix.needsUpdate=true;
 device.intakeDots.visible=s.intake;for(let i=0;i<10;i++){const u=(t*.5+i/10)%1;dummy.position.set(.3+.0532*u,mix(.19,1.6364,u),.1);dummy.scale.setScalar(1);dummy.rotation.set(0,0,0);dummy.updateMatrix();device.intakeDots.setMatrixAt(i,dummy.matrix)}device.intakeDots.instanceMatrix.needsUpdate=true;
 // A separate close-up nozzle sends water OUT toward tooth surfaces; drainage falls down/front.
 const running=t<162.568,pulse=Math.max(.15,s.stroke),impact=111.336;
 oral.jets.visible=running;oral.drain.visible=running;
 for(let i=0;i<36;i++){let u=(t*1.2+i/36)%1;dummy.position.set(mix(-1,0,u),mix(.14,-.1,u),mix(.95,.38,u));dummy.scale.setScalar(t>=152.384?.65:pulse*.65+.3);dummy.rotation.set(0,0,0);dummy.updateMatrix();oral.jets.setMatrixAt(i,dummy.matrix)}oral.jets.instanceMatrix.needsUpdate=true;
 for(let i=0;i<32;i++){let u=(t*.7+i/32)%1,a=i*2.399;const splash=t>=137.912&&t<152.384?1:.45;dummy.position.set(Math.sin(a)*u*splash,-.1-u*u*1.5,.38+u*(.5+Math.cos(a)*.2));dummy.scale.setScalar(.55);dummy.rotation.set(0,0,0);dummy.updateMatrix();oral.drain.setMatrixAt(i,dummy.matrix)}oral.drain.instanceMatrix.needsUpdate=true;
 for(let i=0;i<20;i++){const release=impact+1.8+i*.2,u=clamp((t-release)/2.8),a=i*2.399;dummy.position.set(Math.sin(a)*(.04+u*.65),-.12+(i%5)*.06-u*u*1.2,.37+u*.65);dummy.scale.setScalar(t>release+2.8?.001:1);dummy.rotation.set(u*2,a,u*2);dummy.updateMatrix();oral.debris.setMatrixAt(i,dummy.matrix)}oral.debris.instanceMatrix.needsUpdate=true;
 oral.plaque.forEach((p,i)=>{p.material.opacity=i%3===0?.45:mix(.72,.22,ramp(t,123,128))});oral.tartar.visible=t>=128.28;
 $('#in-state').textContent='进水阀 '+(s.intake?'开':'关');$('#out-state').textContent='出水阀 '+(s.compression?'开':'关');$('#in-state').classList.toggle('open',s.intake);$('#out-state').classList.toggle('open',s.compression);
 let d='';for(let i=0;i<=220;i++){let x=300+i*2.48,y=82-Math.pow(Math.max(0,Math.sin(i*.10-t*2.7)),2)*55;d+=(i?'L':'M')+x.toFixed(1)+' '+y.toFixed(1)}$('#wave').setAttribute('d',d);
 measure.font='700 63px Noto';title.style.fontSize=Math.min(63,63*860/Math.max(860,measure.measureText(title.textContent).width),860/[...title.textContent].length)+'px';
 camera.position.set(Math.sin(orbit)*dist,camY,Math.cos(orbit)*dist);camera.lookAt(0,lookY,0);camera.updateMatrixWorld();scene.updateMatrixWorld(true);
 if(showLabels){for(const l of labels){v0.fromArray(l.pos);const obj=l.key==='motor'?device.internals:l.key==='intake'?device.internals:device[l.key];obj.localToWorld(v0);v0.project(camera);const x=(v0.x*.5+.5)*1080,y=(-v0.y*.5+.5)*930+390;const sx=l.side==='left'?100+l.div.offsetWidth:980-l.div.offsetWidth;const sy=l.y+30,elbow=l.side==='left'?sx+25:sx-25;l.div.style.opacity=1;l.line.style.opacity=.7;l.div.classList.toggle('active',l.key===active);l.line.setAttribute('points',`${sx},${sy} ${elbow},${sy} ${x},${y}`)}}
 if(t>=52.4&&t<88.24){for(const l of pumpLabels){const early=t<61.96;const show=early?['motor','crank','piston'].includes(l.key):['chamber','inlet','outlet'].includes(l.key);if(!show)continue;v0.fromArray(l.point);if(l.key==='piston')v0.x=s.slider;pump.root.localToWorld(v0);v0.project(camera);const x=(v0.x*.5+.5)*1080,y=(-v0.y*.5+.5)*930+390;const sx=l.side==='left'?100+l.div.offsetWidth:980-l.div.offsetWidth,sy=l.y+30;l.div.style.opacity=1;l.line.style.opacity=.65;l.line.setAttribute('points',`${sx},${sy} ${sx+(l.side==='left'?25:-25)},${sy} ${x},${y}`)}}
 renderer.render(scene,camera);let count=0;scene.traverse(o=>{if(o.isMesh)count++});window.__3dMeta={time:t,meshCount:count,triangles:renderer.info.render.triangles,pump:{theta:s.theta,slider:s.slider,inletOpen:s.inletOpen,outletOpen:s.outletOpen,crankPin:s.pin.toArray(),rodLength:s.rodLength,flowDirection:'reservoir -> inlet -> chamber -> outlet -> nozzle'}};
}
window.renderFlosserAt=renderAt;window.__exportFlosserScene=()=>scene.toJSON();window.pumpStateForQA=pumpState;
window.renderCoverAsset=()=>{renderAt(8);device.housing.material.opacity=.23;device.housing.material.depthWrite=false;device.nozzle.position.y=.15;device.body.position.x=.15;device.jet.visible=false;device.intakeDots.visible=false;platform.visible=false;renderer.setSize(1400,1400,false);camera.aspect=1;camera.position.set(4,4.2,7);camera.lookAt(0,2,0);camera.updateProjectionMatrix();renderer.render(scene,camera);const data=renderer.domElement.toDataURL('image/png');renderer.setSize(1080,930,false);camera.aspect=1080/930;camera.updateProjectionMatrix();return data};
window.addEventListener('hf-seek',e=>renderAt(e.detail.time));const raw=new URLSearchParams(location.search).get('t');const boot=raw==null||raw===''?(window.__hfThreeTime||0):Number(raw);renderAt(Number.isFinite(boot)?boot:0);
