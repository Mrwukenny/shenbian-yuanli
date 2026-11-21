import * as T from 'three';
export const C={water:0x22d3ee,motor:0xf5a85d,motion:0x9b78fa,valve:0xfbd66b,white:0xe7eff6,dark:0x263650};
export const mat=(c,o={})=>new T.MeshPhongMaterial({color:c,shininess:70,...o});
export function mesh(g,m,p=[0,0,0],parent){let a=new T.Mesh(g,m);a.position.fromArray(p);parent?.add(a);return a}
export function cyl(r,h,m,p,parent){return mesh(new T.CylinderGeometry(r,r,h,48),m,p,parent)}
export function ring(r,s,y,m,parent){let a=mesh(new T.TorusGeometry(r,s,8,64),m,[0,y,0],parent);a.rotation.x=Math.PI/2;return a}
export function tube(p,r,m,parent){return mesh(new T.TubeGeometry(new T.CatmullRomCurve3(p.map(v=>new T.Vector3(...v))),36,r,8,false),m,[0,0,0],parent)}
export function makePump(){
 const root=new T.Group(),motor=new T.Group(),hydraulic=new T.Group();root.add(motor,hydraulic);
 const steel=mat(0xa6b9c8),dark=mat(C.dark),violet=mat(C.motion),gold=mat(C.valve),wm=mat(C.water,{transparent:true,opacity:.48,depthWrite:false});
 const motorCase=cyl(.35,.66,mat(C.motor),[-.65,0,-.08],motor);motorCase.rotation.x=Math.PI/2;
 for(const z of [-.44,.28]){let x=cyl(.36,.055,dark,[-.65,0,z],motor);x.rotation.x=Math.PI/2}
 for(let i=0;i<6;i++){const a=i*Math.PI/3;mesh(new T.BoxGeometry(.04,.09,.46),mat(0x9b633e),[-.65+.355*Math.cos(a),.355*Math.sin(a),-.08],motor).rotation.z=a}
 const shaft=cyl(.07,.25,steel,[-.65,0,.4],motor);shaft.rotation.x=Math.PI/2;
 const gear=new T.Group();root.add(gear);gear.position.set(-.65,0,.55);
 let disk=cyl(.32,.08,violet,[0,0,0],gear);disk.rotation.x=Math.PI/2;
 for(let i=0;i<16;i++){const a=i*Math.PI/8;let tooth=mesh(new T.BoxGeometry(.1,.12,.09),violet,[.345*Math.cos(a),.345*Math.sin(a),0],gear);tooth.rotation.z=a}
 mesh(new T.SphereGeometry(.065,14,8),gold,[.2,0,.075],gear);
 const casing=cyl(.305,1.17,mat(0xa0e7f2,{transparent:true,opacity:.17,depthWrite:false,side:T.DoubleSide}),[.695,0,0],hydraulic);casing.rotation.z=Math.PI/2;
 const cap=cyl(.32,.075,steel,[1.3,0,0],hydraulic);cap.rotation.z=Math.PI/2;
 for(const x of [.1,1.26]){const rim=mesh(new T.TorusGeometry(.305,.018,8,48),steel,[x,0,0],hydraulic);rim.rotation.y=Math.PI/2}
 const fluid=cyl(.265,1,wm,[.8,0,0],hydraulic);fluid.rotation.z=Math.PI/2;
 const piston=cyl(.272,.09,violet,[.3,0,0],hydraulic);piston.rotation.z=Math.PI/2;
 const pistonSeal=mesh(new T.TorusGeometry(.272,.018,8,48),dark,[.3,0,0],hydraulic);pistonSeal.rotation.y=Math.PI/2;
 const pistonPin=cyl(.045,.55,steel,[.3,0,.28],hydraulic);pistonPin.rotation.x=Math.PI/2;
 const rod=mesh(new T.BoxGeometry(.09,1,.065),steel,[0,0,.63],root);
 const inletPath=new T.CatmullRomCurve3([[.98,-1.04,0],[.98,-.7,0],[.98,-.27,0]].map(p=>new T.Vector3(...p)));
 const outletPath=new T.CatmullRomCurve3([[1.16,.27,0],[1.16,.75,0],[1.1,1.32,0],[.6,1.58,0]].map(p=>new T.Vector3(...p)));
 mesh(new T.TubeGeometry(inletPath,24,.07,10,false),mat(0x9eeeff,{transparent:true,opacity:.25,depthWrite:false}),[0,0,0],hydraulic);
 mesh(new T.TubeGeometry(outletPath,36,.062,10,false),mat(0xb4eafa,{transparent:true,opacity:.3,depthWrite:false}),[0,0,0],hydraulic);
 const inletSeat=ring(.075,.018,-.62,gold,hydraulic);inletSeat.position.x=.98;
 const outletSeat=ring(.069,.018,.55,gold,hydraulic);outletSeat.position.x=1.16;
 const inletBall=mesh(new T.SphereGeometry(.068,18,12),gold,[.98,-.57,0],hydraulic);
 const outletBall=mesh(new T.SphereGeometry(.063,18,12),gold,[1.16,.6,0],hydraulic);
 const inDots=new T.InstancedMesh(new T.SphereGeometry(.034,8,6),mat(C.water,{emissive:0x086e83}),8);hydraulic.add(inDots);
 const outDots=new T.InstancedMesh(new T.SphereGeometry(.03,8,6),mat(C.water,{emissive:0x086e83}),10);hydraulic.add(outDots);
 const jet=new T.InstancedMesh(new T.SphereGeometry(.036,8,6),mat(0x9bf1fc,{emissive:0x0a5365}),18);hydraulic.add(jet);
 return {root,motor,hydraulic,gear,rod,fluid,piston,pistonPin,pistonSeal,inletBall,outletBall,inDots,outDots,jet,inletPath,outletPath,casing};
}
export function makeFlosser(){
 const root=new T.Group(),tank=new T.Group(),body=new T.Group(),nozzle=new T.Group(),internals=new T.Group();root.add(tank,body,nozzle,internals);
 const dark=mat(C.dark),white=mat(C.white),purple=mat(C.motion),glass=mat(0x6fd9ef,{transparent:true,opacity:.22,depthWrite:false,side:T.DoubleSide,shininess:110});
 const prof=[[.57,.08],[.7,.14],[.74,.32],[.74,.93],[.66,1.23]].map(p=>new T.Vector2(...p));
 const tankShell=mesh(new T.LatheGeometry(prof,64),glass,[0,0,0],tank);
 cyl(.59,.11,dark,[0,.06,0],tank);ring(.7,.027,.19,purple,tank);ring(.66,.025,1.23,white,tank);
 const water=cyl(.68,.8,mat(C.water,{transparent:true,opacity:.46,depthWrite:false}),[0,.6,0],tank);
 let top=mesh(new T.CircleGeometry(.68,64),mat(0x8ae5f7,{transparent:true,opacity:.28,depthWrite:false,side:T.DoubleSide}),[0,1.0,0],tank);top.rotation.x=-Math.PI/2;
 for(let i=0;i<4;i++){const l=ring(.2+i*.12,.007,1.006,mat(0xa5f3fc,{transparent:true,opacity:.35}),tank);}
 const intake=tube([[.3,.19,.1],[.3,.9,.1],[.33,1.4,.1],[.3532,1.6364,.1]],.043,mat(0x81b7c7,{transparent:true,opacity:.6}),internals);
 const shellpts=[[.66,1.22],[.66,1.45],[.61,2.48],[.52,2.73],[.36,2.8]].map(p=>new T.Vector2(...p));
 const housing=mesh(new T.LatheGeometry(shellpts,64),white,[0,0,0],body);housing.material=white.clone();
 ring(.655,.035,1.3,dark,body);cyl(.4,.08,dark,[0,2.8,0],body);
 const panel=mesh(new T.CapsuleGeometry(.16,.55,4,16),dark,[0,2.03,.61],body);panel.scale.z=.22;
 const btn=cyl(.09,.04,mat(C.water,{emissive:0x124952}),[0,2.22,.67],body);btn.rotation.x=Math.PI/2;
 for(let i=0;i<3;i++){let l=mesh(new T.BoxGeometry(.12,.018,.022),mat(i?0x566181:C.water,{emissive:i?0:0x0a5266}),[0,1.98-i*.1,.655],body)}
 for(const s of [-1,1]){tube([[s*.53,1.45,.27],[s*.5,2.2,.29],[s*.42,2.6,.27]],.013,purple,body)}
 const battery=cyl(.16,.7,mat(0x2b3c59),[-.29,1.72,-.05],internals);cyl(.12,.04,white,[-.29,2.09,-.05],internals);
 const board=mesh(new T.BoxGeometry(.25,.65,.055),mat(0x14604a),[-.35,2.3,.22],internals);
 for(let i=0;i<3;i++)mesh(new T.BoxGeometry(.13,.1,.04),dark,[-.35,2.14+i*.16,.27],internals);
 const pump=makePump();pump.root.position.set(.02,1.99,.1);pump.root.scale.setScalar(.34);internals.add(pump.root);
 const outlet=tube([[.224,2.5272,.1],[.15,2.72,.06],[0,2.83,0]],.04,mat(C.water,{transparent:true,opacity:.65}),internals);
 cyl(.21,.19,white,[0,2.89,0],nozzle);ring(.2,.022,2.98,purple,nozzle);
 const nozzlePoints=[[0,2.98,0],[0,3.52,0],[-.12,3.77,0],[-.55,3.91,0],[-.86,3.91,0]];
 tube(nozzlePoints,.063,mat(0xd6f6fa,{transparent:true,opacity:.65,depthWrite:false}),nozzle);
 tube(nozzlePoints,.023,mat(C.water,{emissive:0x075466}),nozzle);
 let mouth=mesh(new T.TorusGeometry(.05,.012,8,24),dark,[-.86,3.91,0],nozzle);mouth.rotation.y=Math.PI/2;
 const jet=new T.InstancedMesh(new T.SphereGeometry(.035,8,6),mat(0xa5f3fc,{emissive:0x0b5a6a}),20);root.add(jet);
 const intakeDots=new T.InstancedMesh(new T.SphereGeometry(.028,8,6),mat(C.water),10);root.add(intakeDots);
 return {root,tank,body,nozzle,internals,housing,tankShell,water,intake,battery,board,pump,jet,intakeDots,outlet};
}
export function makeTeeth(){
 const root=new T.Group(),teeth=new T.Group(),spray=new T.Group();root.add(teeth,spray);
 const gum=mesh(new T.CapsuleGeometry(.43,1.2,6,24),mat(0x9c627e,{shininess:25}),[0,-.65,0],teeth);gum.rotation.z=Math.PI/2;gum.scale.z=.85;
 const toothmat=mat(0xf2eee5,{shininess:90}),shape=new T.Shape();shape.moveTo(-.31,-.48);shape.quadraticCurveTo(-.43,.0,-.3,.43);shape.quadraticCurveTo(-.19,.6,0,.45);shape.quadraticCurveTo(.23,.61,.32,.38);shape.quadraticCurveTo(.4,0,.28,-.48);shape.closePath();
 const geo=new T.ExtrudeGeometry(shape,{depth:.44,bevelEnabled:true,bevelSegments:3,steps:1,bevelSize:.08,bevelThickness:.08});geo.translate(0,0,-.22);
 for(const x of [-.47,.47]){mesh(geo,toothmat,[x,0,0],teeth);mesh(new T.SphereGeometry(.22,20,14),toothmat,[x,.32,.06],teeth).scale.set(1,.7,1.2)}
 const nozzlePath=[[-1.9,.55,1.25],[-1.48,.45,1.18],[-1.25,.24,1.08],[-1.0,.14,.95]];tube(nozzlePath,.075,mat(0xd9f5fb,{transparent:true,opacity:.65}),spray);tube(nozzlePath,.027,mat(C.water),spray);
 const jets=new T.InstancedMesh(new T.SphereGeometry(.038,8,6),mat(0x87eaf8,{emissive:0x104f64}),36);spray.add(jets);
 const drain=new T.InstancedMesh(new T.SphereGeometry(.038,8,6),mat(C.water),32);spray.add(drain);
 const debris=new T.InstancedMesh(new T.IcosahedronGeometry(.06,0),mat(0xcaa866),20);root.add(debris);
 const plaque=[];for(let i=0;i<10;i++){let a=mesh(new T.SphereGeometry(.063,12,8),mat(0xbfa982,{transparent:true,opacity:.72}),[(i<5?-.2:.2)+(i%2)*.07,-.25+(i%5)*.09,.3],teeth);a.scale.set(1,.8,.25);plaque.push(a)}
 const tartar=mesh(new T.SphereGeometry(.13,12,8),mat(0xba9b71),[.38,-.34,.33],teeth);tartar.scale.set(1,.6,.3);
 return {root,teeth,spray,jets,drain,debris,plaque,tartar};
}
