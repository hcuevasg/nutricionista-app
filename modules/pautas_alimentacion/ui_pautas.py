"""Pautas de Alimentacion — UI CustomTkinter."""
import os, tkinter as tk
from tkinter import messagebox, filedialog
from typing import Optional
import customtkinter as ctk
from datetime import datetime
import database.db_manager as db
from modules.pautas_alimentacion.grupos_alimentos import (
    GRUPOS_MACROS, GRUPOS_POR_PAUTA, NOMBRES_GRUPOS, NOMBRES_TIPOS_PAUTA, TIEMPOS_COMIDA)
from modules.pautas_alimentacion.calculadora_requerimientos import (
    FACTORES_ACTIVIDAD, calcular_tmb, calcular_get, calcular_macros, get_fa_valor)
from modules.pautas_alimentacion.distribucion_porciones import (
    calcular_aporte_grupo, calcular_adecuacion, validar_porciones_totales, calcular_aporte_total)
from modules.pautas_alimentacion.tablas_equivalencias import (
    TABLAS_EQUIVALENCIAS, NOMBRES_GRUPOS_EQUIV, ABREVIATURAS)

_P="#4b7c60";_PD="#3d6b50";_TC="#c06c52";_SG="#8da399";_BG="#F7F5F2"
_CARD="#FFFFFF";_BD="#E5EAE7";_MU="#6b7280";_AM="#D97706";_RD="#DC2626"
_TIPOS_PAUTA=[("omnivoro","Omnivoro"),("ovolacto","Ovo-lacto Vegetariano"),
    ("vegano","Vegano"),("pescetariano","Pescetariano"),("sin_gluten","Sin Gluten")]
_TK=[t[0] for t in _TIPOS_PAUTA];_TL=[t[1] for t in _TIPOS_PAUTA]
_FK=list(FACTORES_ACTIVIDAD.keys());_FL=[FACTORES_ACTIVIDAD[k]["label"] for k in _FK]

def _lbl(p,text,size=11,bold=False,color=None,**kw):
    kw.setdefault("text_color",color or _MU)
    return ctk.CTkLabel(p,text=text,font=ctk.CTkFont(size=size,weight="bold" if bold else "normal"),**kw)

class PautasFrame(ctk.CTkFrame):
    def __init__(self,master,app,**kw):
        super().__init__(master,corner_radius=0,fg_color=(_BG,"#0d1a12"),**kw)
        self._app=app;self._pauta_id=None;self._paciente_id=None
        self._grupos_activos=list(GRUPOS_POR_PAUTA["omnivoro"]);self._save_job=None
        self._var_peso=tk.StringVar(value="0");self._var_fa=tk.StringVar(value="liviana")
        self._var_prot_gkg=tk.StringVar(value="1.2");self._var_lip_pct=tk.StringVar(value="28.0")
        self._var_tipo=tk.StringVar(value="omnivoro");self._var_nombre=tk.StringVar()
        self._var_obs=tk.StringVar();self._vars_porciones={};self._vars_dist={}
        self._var_search=tk.StringVar();self._tmb=None;self._get=None;self._macros=None
        self._macro_rows={};self._lbl_get=None;self._lbl_tmb=None
        self._porciones_container=None;self._menu_scroll=None;self._tab4_scroll=None
        self._lbl_validacion=None;self._pdf_vars={}
        self.grid_columnconfigure(0,weight=1);self.grid_rowconfigure(1,weight=1)
        self._build_header();self._build_body()

    def _build_header(self):
        hdr=ctk.CTkFrame(self,fg_color=(_CARD,"#1a2620"),corner_radius=0,
            border_width=1,border_color=(_BD,"#2a3d30"))
        hdr.grid(row=0,column=0,sticky="ew");hdr.grid_columnconfigure(2,weight=1)
        ctk.CTkLabel(hdr,text="Pautas de Alimentacion",
            font=ctk.CTkFont(size=16,weight="bold"),text_color=(_P,"#6ec896")
            ).grid(row=0,column=0,padx=20,pady=14,sticky="w")
        sf=ctk.CTkFrame(hdr,fg_color="transparent");sf.grid(row=0,column=1,padx=(0,12),pady=10)
        _lbl(sf,"Pauta:").pack(side="left",padx=(0,6))
        self._combo_pauta=ctk.CTkComboBox(sf,values=["-- ninguna --"],width=280,
            font=ctk.CTkFont(size=11),command=self._on_pauta_selected)
        self._combo_pauta.pack(side="left")
        bf=ctk.CTkFrame(hdr,fg_color="transparent");bf.grid(row=0,column=3,padx=16,pady=10)
        ctk.CTkButton(bf,text="+ Nueva",height=34,width=110,font=ctk.CTkFont(size=12,weight="bold"),
            fg_color=_P,hover_color=_PD,command=self._nueva_pauta).pack(side="left",padx=(0,6))
        ctk.CTkButton(bf,text="Eliminar",height=34,width=90,font=ctk.CTkFont(size=12),
            fg_color="transparent",border_width=1,border_color=_RD,text_color=(_RD,"#f87171"),
            hover_color=("#fee2e2","#3a1515"),command=self._eliminar_pauta).pack(side="left")

    def _build_body(self):
        self._tabs=ctk.CTkTabview(self,fg_color="transparent")
        self._tabs.grid(row=1,column=0,sticky="nsew")
        for n in ["Requerimientos","Porciones","Ejemplos de Menu","Tabla Equiv.","Exportar PDF"]:
            self._tabs.add(n)
        self._build_tab1(self._tabs.tab("Requerimientos"))
        self._build_tab2(self._tabs.tab("Porciones"))
        self._build_tab3(self._tabs.tab("Ejemplos de Menu"))
        self._build_tab4(self._tabs.tab("Tabla Equiv."))
        self._build_tab5(self._tabs.tab("Exportar PDF"))

    def _build_tab1(self,tab):
        tab.grid_columnconfigure(0,weight=1);tab.grid_columnconfigure(1,weight=1);tab.grid_rowconfigure(0,weight=1)
        left=ctk.CTkScrollableFrame(tab,fg_color=(_CARD,"#1a2620"),corner_radius=12,border_width=1,border_color=(_BD,"#2a3d30"))
        left.grid(row=0,column=0,sticky="nsew",padx=(8,6),pady=8);left.grid_columnconfigure(0,weight=1)
        self._build_form_inputs(left)
        right=ctk.CTkFrame(tab,fg_color="transparent")
        right.grid(row=0,column=1,sticky="nsew",padx=(6,8),pady=8)
        right.grid_columnconfigure(0,weight=1);right.grid_rowconfigure(1,weight=1)
        self._build_results_panel(right)

    def _build_form_inputs(self,p):
        r=0
        sec=ctk.CTkFrame(p,fg_color=(_SG+"25","#2a3d30"),corner_radius=6)
        sec.grid(row=r,column=0,sticky="ew",padx=12,pady=(12,8));r+=1
        ctk.CTkLabel(sec,text="Datos del Paciente",font=ctk.CTkFont(size=12,weight="bold"),
            text_color=(_SG,"#6ec896")).pack(side="left",padx=12,pady=6)
        for lbl_t,var,ph in [("NOMBRE",self._var_nombre,"Ej. Pauta Semana 1")]:
            _lbl(p,lbl_t,size=10,bold=True).grid(row=r,column=0,padx=14,pady=(10,2),sticky="w");r+=1
            ctk.CTkEntry(p,textvariable=var,height=36,placeholder_text=ph,font=ctk.CTkFont(size=12)
                ).grid(row=r,column=0,padx=12,pady=(0,4),sticky="ew");r+=1
        _lbl(p,"TIPO DE DIETA",size=10,bold=True).grid(row=r,column=0,padx=14,pady=(6,2),sticky="w");r+=1
        self._combo_tipo=ctk.CTkComboBox(p,values=_TL,height=36,font=ctk.CTkFont(size=12),command=self._on_tipo_changed)
        self._combo_tipo.grid(row=r,column=0,padx=12,pady=(0,4),sticky="ew");r+=1
        for lbl_t,var,ph in [("PESO ACTUAL (KG)",self._var_peso,"64"),
            ("PROTEINAS (G/KG)",self._var_prot_gkg,"1.2"),("% LIPIDOS",self._var_lip_pct,"28.0")]:
            _lbl(p,lbl_t,size=10,bold=True).grid(row=r,column=0,padx=14,pady=(6,2),sticky="w");r+=1
            ctk.CTkEntry(p,textvariable=var,height=36,placeholder_text=ph,font=ctk.CTkFont(size=12)
                ).grid(row=r,column=0,padx=12,pady=(0,4),sticky="ew");r+=1
        _lbl(p,"FACTOR DE ACTIVIDAD",size=10,bold=True).grid(row=r,column=0,padx=14,pady=(6,2),sticky="w");r+=1
        self._combo_fa=ctk.CTkComboBox(p,values=_FL,height=36,font=ctk.CTkFont(size=12))
        self._combo_fa.grid(row=r,column=0,padx=12,pady=(0,4),sticky="ew")
        self._combo_fa.set(_FL[1] if len(_FL)>1 else _FL[0]);r+=1
        _lbl(p,"OBSERVACIONES",size=10,bold=True).grid(row=r,column=0,padx=14,pady=(6,2),sticky="w");r+=1
        ctk.CTkEntry(p,textvariable=self._var_obs,height=36,placeholder_text="Notas...",font=ctk.CTkFont(size=12)
            ).grid(row=r,column=0,padx=12,pady=(0,4),sticky="ew");r+=1
        info=ctk.CTkFrame(p,fg_color=(_P+"15","#1a2e22"),corner_radius=8)
        info.grid(row=r,column=0,padx=12,pady=(6,8),sticky="ew");r+=1
        ctk.CTkLabel(info,text="Formula Oxford 2005 (Henry).",font=ctk.CTkFont(size=10),
            text_color=(_P,"#6ec896")).pack(padx=12,pady=8,anchor="w")
        ctk.CTkButton(p,text="Calcular",height=40,font=ctk.CTkFont(size=13,weight="bold"),
            fg_color=_P,hover_color=_PD,command=self._calcular
            ).grid(row=r,column=0,padx=12,pady=(4,4),sticky="ew");r+=1
        ctk.CTkButton(p,text="Guardar Requerimientos",height=40,font=ctk.CTkFont(size=13,weight="bold"),
            fg_color=_TC,hover_color="#a85a43",command=self._guardar_requerimientos
            ).grid(row=r,column=0,padx=12,pady=(0,16),sticky="ew")

    def _build_results_panel(self,parent):
        gc=ctk.CTkFrame(parent,fg_color=(_TC,"#6b2d1e"),corner_radius=14)
        gc.grid(row=0,column=0,sticky="ew",pady=(8,8));gc.grid_columnconfigure(0,weight=1)
        ctk.CTkLabel(gc,text="GASTO ENERGETICO TOTAL (GET)",font=ctk.CTkFont(size=10,weight="bold"),
            text_color="#ffffff99").grid(row=0,column=0,padx=20,pady=(16,2),sticky="w")
        self._lbl_get=ctk.CTkLabel(gc,text="--",font=ctk.CTkFont(size=38,weight="bold"),text_color="white")
        self._lbl_get.grid(row=1,column=0,padx=20,pady=(0,2),sticky="w")
        ctk.CTkLabel(gc,text="kcal/dia",font=ctk.CTkFont(size=14),text_color="#ffffffbb"
            ).grid(row=2,column=0,padx=22,pady=(0,8),sticky="w")
        ctk.CTkFrame(gc,height=1,fg_color="#ffffff30").grid(row=3,column=0,sticky="ew",padx=20)
        tr=ctk.CTkFrame(gc,fg_color="transparent");tr.grid(row=4,column=0,sticky="ew",padx=20,pady=(8,16))
        ctk.CTkLabel(tr,text="TASA METABOLICA BASAL",font=ctk.CTkFont(size=9,weight="bold"),
            text_color="#ffffff80").pack(anchor="w")
        self._lbl_tmb=ctk.CTkLabel(tr,text="--",font=ctk.CTkFont(size=18,weight="bold"),text_color="white")
        self._lbl_tmb.pack(anchor="w")
        mc=ctk.CTkFrame(parent,fg_color=(_CARD,"#1a2620"),corner_radius=14,border_width=1,border_color=(_BD,"#2a3d30"))
        mc.grid(row=1,column=0,sticky="nsew",pady=(0,8));mc.grid_columnconfigure(0,weight=1)
        ctk.CTkLabel(mc,text="DISTRIBUCION DE MACRONUTRIENTES",font=ctk.CTkFont(size=10,weight="bold"),
            text_color=(_SG,"#6ec896")).grid(row=0,column=0,padx=16,pady=(14,8),sticky="w")
        for i,(key,label,sub) in enumerate([("prot","Proteinas","g/kg peso"),
            ("lip","Lipidos","Grasas saludables"),("cho","Carbohidratos (CHO)","Complejos y fibra")]):
            rf=ctk.CTkFrame(mc,fg_color=(_BG,"#141f19"),corner_radius=8)
            rf.grid(row=i+1,column=0,padx=12,pady=3,sticky="ew");rf.grid_columnconfigure(1,weight=1)
            ctk.CTkLabel(rf,text="v",font=ctk.CTkFont(size=14),text_color=(_SG,"#6ec896")
                ).grid(row=0,column=0,rowspan=2,padx=(10,8),pady=8)
            ctk.CTkLabel(rf,text=label,font=ctk.CTkFont(size=12,weight="bold"),anchor="w"
                ).grid(row=0,column=1,pady=(8,0),sticky="w")
            ctk.CTkLabel(rf,text=sub,font=ctk.CTkFont(size=9),text_color=_MU,anchor="w"
                ).grid(row=1,column=1,pady=(0,6),sticky="w")
            vl=ctk.CTkLabel(rf,text="--",font=ctk.CTkFont(size=13,weight="bold"))
            vl.grid(row=0,column=2,rowspan=2,padx=(0,12));self._macro_rows[key]=vl

    def _build_tab2(self,tab):
        tab.grid_columnconfigure(0,weight=1);tab.grid_rowconfigure(0,weight=1)
        self._porciones_container=ctk.CTkScrollableFrame(tab,fg_color="transparent")
        self._porciones_container.grid(row=0,column=0,sticky="nsew")
        self._porciones_container.grid_columnconfigure(0,weight=1)

    def _rebuild_porciones_tab(self):
        for w in self._porciones_container.winfo_children(): w.destroy()
        self._vars_porciones.clear();self._vars_dist.clear()
        c=self._porciones_container
        s1=ctk.CTkFrame(c,fg_color=(_CARD,"#1a2620"),corner_radius=12,border_width=1,border_color=(_BD,"#2a3d30"))
        s1.grid(row=0,column=0,sticky="ew",padx=12,pady=(8,6));s1.grid_columnconfigure(0,weight=1)
        ctk.CTkLabel(s1,text="Porciones Diarias por Grupo",font=ctk.CTkFont(size=14,weight="bold")
            ).grid(row=0,column=0,padx=16,pady=(12,8),sticky="w")
        gf=ctk.CTkFrame(s1,fg_color="transparent");gf.grid(row=1,column=0,sticky="ew",padx=12,pady=(0,12))
        sp=db.get_porciones(self._pauta_id) if self._pauta_id else {}
        for i,grupo in enumerate(self._grupos_activos):
            col=(i%3)*2;row_g=(i//3)*2
            nombre=NOMBRES_GRUPOS.get(grupo,grupo);kcal=GRUPOS_MACROS.get(grupo,{}).get("kcal",0)
            ctk.CTkLabel(gf,text=f"{nombre}\n({kcal} kcal/p)",font=ctk.CTkFont(size=10),
                text_color=_MU,justify="center").grid(row=row_g,column=col,padx=(6,2),pady=(6,0),sticky="w")
            var=tk.DoubleVar(value=float(sp.get(grupo,0)));self._vars_porciones[grupo]=var
            var.trace_add("write",lambda *_: self._schedule_save())
            ctk.CTkEntry(gf,textvariable=var,width=60,height=32,font=ctk.CTkFont(size=11)
                ).grid(row=row_g+1,column=col,padx=(6,2),pady=(2,6),sticky="w")
        s2=ctk.CTkFrame(c,fg_color=(_CARD,"#1a2620"),corner_radius=12,border_width=1,border_color=(_BD,"#2a3d30"))
        s2.grid(row=1,column=0,sticky="ew",padx=12,pady=6);s2.grid_columnconfigure(0,weight=1)
        ctk.CTkLabel(s2,text="Distribucion por Tiempo de Comida",font=ctk.CTkFont(size=14,weight="bold")
            ).grid(row=0,column=0,padx=16,pady=(12,4),sticky="w")
        sd=db.get_distribucion(self._pauta_id) if self._pauta_id else {}
        ds=ctk.CTkScrollableFrame(s2,fg_color="transparent",height=240,orientation="horizontal")
        ds.grid(row=1,column=0,sticky="ew",padx=8,pady=(0,12))
        tiempos=[t[0] for t in TIEMPOS_COMIDA];tlabels=[t[1] for t in TIEMPOS_COMIDA]
        ctk.CTkLabel(ds,text="Grupo",font=ctk.CTkFont(size=10,weight="bold"),width=120,anchor="w"
            ).grid(row=0,column=0,padx=(4,2),pady=4)
        for j,tl in enumerate(tlabels):
            ctk.CTkLabel(ds,text=tl,font=ctk.CTkFont(size=10,weight="bold"),width=70,anchor="center"
                ).grid(row=0,column=j+1,padx=2,pady=4)
        for i,grupo in enumerate(self._grupos_activos):
            ctk.CTkLabel(ds,text=NOMBRES_GRUPOS.get(grupo,grupo),font=ctk.CTkFont(size=10),
                width=120,anchor="w",text_color=_MU).grid(row=i+1,column=0,padx=(4,2),pady=2,sticky="w")
            for j,tiempo in enumerate(tiempos):
                val=0.0
                if tiempo in sd and grupo in sd[tiempo]:
                    try: val=float(sd[tiempo][grupo])
                    except: pass
                vd=tk.DoubleVar(value=val);self._vars_dist[(grupo,tiempo)]=vd
                vd.trace_add("write",lambda *_: self._schedule_save())
                ctk.CTkEntry(ds,textvariable=vd,width=60,height=28,font=ctk.CTkFont(size=10)
                    ).grid(row=i+1,column=j+1,padx=2,pady=2)
        ctk.CTkButton(c,text="Verificar distribucion",height=36,font=ctk.CTkFont(size=12),
            fg_color=_P,hover_color=_PD,command=self._verificar_distribucion
            ).grid(row=2,column=0,padx=12,pady=8,sticky="w")
        self._lbl_validacion=ctk.CTkLabel(c,text="",font=ctk.CTkFont(size=11),
            text_color=_MU,wraplength=600,justify="left")
        self._lbl_validacion.grid(row=3,column=0,padx=16,pady=(0,8),sticky="w")

    def _verificar_distribucion(self):
        pd={g:self._get_porcion(g) for g in self._grupos_activos}
        dd=self._get_distribucion_dict();difs=validar_porciones_totales(pd,dd)
        msgs=[]
        for g,d in difs.items():
            if abs(d)>0.01:
                n=NOMBRES_GRUPOS.get(g,g)
                msgs.append(f"Exceso {n}: {d:.1f}p" if d>0 else f"Faltan {n}: {abs(d):.1f}p")
        self._lbl_validacion.configure(text="\n".join(msgs) if msgs else "v Distribucion correcta.",
            text_color=_AM if msgs else _P)

    def _get_porcion(self,grupo):
        v=self._vars_porciones.get(grupo)
        try: return float(v.get()) if v else 0.0
        except: return 0.0

    def _get_distribucion_dict(self):
        tiempos=[t[0] for t in TIEMPOS_COMIDA];dist={}
        for tiempo in tiempos:
            dist[tiempo]={}
            for grupo in self._grupos_activos:
                v=self._vars_dist.get((grupo,tiempo))
                try: val=float(v.get()) if v else 0.0
                except: val=0.0
                if val: dist[tiempo][grupo]=val
        return dist

    def _build_tab3(self,tab):
        tab.grid_columnconfigure(0,weight=1);tab.grid_rowconfigure(1,weight=1)
        sb=ctk.CTkFrame(tab,fg_color="transparent");sb.grid(row=0,column=0,sticky="ew",padx=12,pady=(8,4))
        sb.grid_columnconfigure(1,weight=1)
        ctk.CTkLabel(sb,text="Buscar alimento (USDA):",font=ctk.CTkFont(size=12)
            ).grid(row=0,column=0,padx=(0,8))
        ctk.CTkEntry(sb,textvariable=self._var_search,height=36,
            placeholder_text="Ej: arroz, pollo...",font=ctk.CTkFont(size=12)
            ).grid(row=0,column=1,sticky="ew")
        ctk.CTkButton(sb,text="Buscar",height=36,width=90,fg_color=_P,hover_color=_PD,
            command=self._buscar_alimento).grid(row=0,column=2,padx=(8,0))
        scroll=ctk.CTkScrollableFrame(tab,fg_color="transparent")
        scroll.grid(row=1,column=0,sticky="nsew");scroll.grid_columnconfigure(0,weight=1)
        self._menu_scroll=scroll;self._rebuild_menu_tab()

    def _rebuild_menu_tab(self):
        if not self._menu_scroll: return
        for w in self._menu_scroll.winfo_children(): w.destroy()
        loaded={}
        if self._pauta_id:
            try: loaded=db.get_menu_pauta(self._pauta_id)
            except: pass
        for i,(tk_,tl) in enumerate(TIEMPOS_COMIDA):
            sec=ctk.CTkFrame(self._menu_scroll,fg_color=(_CARD,"#1a2620"),corner_radius=12,
                border_width=1,border_color=(_BD,"#2a3d30"))
            sec.grid(row=i,column=0,sticky="ew",padx=12,pady=4);sec.grid_columnconfigure(0,weight=1)
            ctk.CTkLabel(sec,text=tl,font=ctk.CTkFont(size=13,weight="bold"),
                text_color=(_P,"#6ec896")).grid(row=0,column=0,padx=14,pady=(10,6),sticky="w")
            opciones=loaded.get(tk_,[{},{},{}])
            while len(opciones)<3: opciones.append({})
            of=ctk.CTkFrame(sec,fg_color="transparent");of.grid(row=1,column=0,sticky="ew",padx=12,pady=(0,10))
            for j in range(3): of.grid_columnconfigure(j,weight=1)
            for j in range(3):
                op=opciones[j] if j<len(opciones) else {}
                opf=ctk.CTkFrame(of,fg_color=(_BG,"#141f19"),corner_radius=8)
                opf.grid(row=0,column=j,padx=4,pady=4,sticky="nsew");opf.grid_columnconfigure(0,weight=1)
                ctk.CTkLabel(opf,text=f"Opcion {j+1}",font=ctk.CTkFont(size=10,weight="bold"),
                    text_color=(_SG,"#6ec896")).grid(row=0,column=0,padx=8,pady=(8,2),sticky="w")
                vf=tk.StringVar(value=op.get("alimento",""))
                vg=tk.StringVar(value=str(op.get("gramos","")) if op.get("gramos") else "")
                vk=tk.StringVar(value=str(op.get("calorias","")) if op.get("calorias") else "")
                ctk.CTkEntry(opf,textvariable=vf,height=30,placeholder_text="Alimento...",
                    font=ctk.CTkFont(size=10)).grid(row=1,column=0,padx=6,pady=2,sticky="ew")
                gr=ctk.CTkFrame(opf,fg_color="transparent");gr.grid(row=2,column=0,padx=6,pady=2,sticky="ew")
                gr.grid_columnconfigure(0,weight=1);gr.grid_columnconfigure(1,weight=1)
                ctk.CTkEntry(gr,textvariable=vg,height=28,placeholder_text="g",font=ctk.CTkFont(size=10)
                    ).grid(row=0,column=0,padx=(0,2),sticky="ew")
                ctk.CTkEntry(gr,textvariable=vk,height=28,placeholder_text="kcal",font=ctk.CTkFont(size=10)
                    ).grid(row=0,column=1,padx=(2,0),sticky="ew")
                ctk.CTkButton(opf,text="Guardar",height=28,fg_color=_P,hover_color=_PD,
                    font=ctk.CTkFont(size=10),
                    command=lambda t=tk_,jj=j,a=vf,b=vg,d=vk: self._guardar_menu_opcion(t,jj,a,b,d)
                    ).grid(row=3,column=0,padx=6,pady=(2,8),sticky="ew")

    def _buscar_alimento(self):
        q=self._var_search.get().strip()
        if not q: return
        try: results=db.search_foods(q,limit=15)
        except Exception as e: messagebox.showerror("Error",str(e));return
        if not results: messagebox.showinfo("Sin resultados","No se encontraron alimentos.");return
        dlg=ctk.CTkToplevel(self);dlg.title(f"Resultados: {q}");dlg.geometry("540x380");dlg.grab_set()
        ctk.CTkLabel(dlg,text=f"Resultados para: {q}",font=ctk.CTkFont(size=13,weight="bold")
            ).pack(padx=16,pady=(12,4))
        sc=ctk.CTkScrollableFrame(dlg,fg_color="transparent");sc.pack(fill="both",expand=True,padx=8,pady=8)
        sc.grid_columnconfigure(0,weight=1)
        for i,food in enumerate(results):
            nombre=food.get("nombre_es") or food.get("name","--")
            rf=ctk.CTkFrame(sc,fg_color=(_BG,"#141f19"),corner_radius=8)
            rf.grid(row=i,column=0,sticky="ew",padx=4,pady=3);rf.grid_columnconfigure(0,weight=1)
            ctk.CTkLabel(rf,text=nombre,font=ctk.CTkFont(size=12,weight="bold"),anchor="w"
                ).grid(row=0,column=0,padx=10,pady=(8,0),sticky="w")
            ctk.CTkLabel(rf,text=f"{food.get('calorias',0)} kcal  {food.get('proteinas_g',0)}g prot",
                font=ctk.CTkFont(size=10),text_color=_MU,anchor="w"
                ).grid(row=1,column=0,padx=10,pady=(0,8),sticky="w")

    def _guardar_menu_opcion(self,tk_,opcion_num,vf,vg,vk):
        if not self._pauta_id: messagebox.showwarning("Sin pauta","Guarda la pauta primero.");return
        alimento=vf.get().strip()
        if not alimento: return
        try: gramos=float(vg.get()) if vg.get().strip() else None
        except: gramos=None
        try: calorias=float(vk.get()) if vk.get().strip() else None
        except: calorias=None
        db.save_menu_opcion(self._pauta_id,tk_,opcion_num+1,alimento=alimento,gramos=gramos,calorias=calorias)
        if hasattr(self._app,"show_toast"): self._app.show_toast("v Opcion guardada")

    def _build_tab4(self,tab):
        tab.grid_columnconfigure(0,weight=1);tab.grid_rowconfigure(0,weight=1)
        self._tab4_scroll=ctk.CTkScrollableFrame(tab,fg_color="transparent")
        self._tab4_scroll.grid(row=0,column=0,sticky="nsew");self._tab4_scroll.grid_columnconfigure(0,weight=1)

    def _rebuild_tab4(self):
        if not self._tab4_scroll: return
        for w in self._tab4_scroll.winfo_children(): w.destroy()
        tipo=self._var_tipo.get();tabla=TABLAS_EQUIVALENCIAS.get(tipo,{})
        if not tabla:
            ctk.CTkLabel(self._tab4_scroll,text=f"Sin tabla para {NOMBRES_TIPOS_PAUTA.get(tipo,tipo)}",
                font=ctk.CTkFont(size=13),text_color=_MU).pack(pady=40);return
        ctk.CTkLabel(self._tab4_scroll,
            text=f"Tablas de Equivalencias -- {NOMBRES_TIPOS_PAUTA.get(tipo,tipo)}",
            font=ctk.CTkFont(size=15,weight="bold")
            ).grid(row=0,column=0,padx=16,pady=(12,4),sticky="w")
        for ri,(gk,items) in enumerate(tabla.items()):
            nombre=NOMBRES_GRUPOS_EQUIV.get(gk,gk)
            sec=ctk.CTkFrame(self._tab4_scroll,fg_color=(_CARD,"#1a2620"),corner_radius=10,
                border_width=1,border_color=(_BD,"#2a3d30"))
            sec.grid(row=ri+1,column=0,sticky="ew",padx=12,pady=4);sec.grid_columnconfigure(0,weight=1)
            ctk.CTkLabel(sec,text=nombre,font=ctk.CTkFont(size=12,weight="bold"),
                text_color=(_P,"#6ec896")).grid(row=0,column=0,padx=14,pady=(10,4),sticky="w")
            for j,item in enumerate(items):
                bg=(_BG,"#141f19") if j%2==0 else ("transparent","transparent")
                rf=ctk.CTkFrame(sec,fg_color=bg,corner_radius=4)
                rf.grid(row=j+1,column=0,sticky="ew",padx=8,pady=1)
                ctk.CTkLabel(rf,text=item,font=ctk.CTkFont(size=11),anchor="w"
                    ).grid(row=0,column=0,padx=10,pady=5,sticky="w")
        ab=ABREVIATURAS if isinstance(ABREVIATURAS,str) else str(ABREVIATURAS)
        ctk.CTkLabel(self._tab4_scroll,text=ab,font=ctk.CTkFont(size=9),
            text_color=_MU,wraplength=700,justify="left"
            ).grid(row=len(tabla)+2,column=0,padx=16,pady=12,sticky="w")

    def _build_tab5(self,tab):
        tab.grid_columnconfigure(0,weight=1);tab.grid_columnconfigure(1,weight=1);tab.grid_rowconfigure(0,weight=1)
        left=ctk.CTkFrame(tab,fg_color=(_CARD,"#1a2620"),corner_radius=12,border_width=1,border_color=(_BD,"#2a3d30"))
        left.grid(row=0,column=0,sticky="nsew",padx=(8,4),pady=8);left.grid_columnconfigure(0,weight=1)
        ctk.CTkLabel(left,text="Secciones a incluir",font=ctk.CTkFont(size=14,weight="bold")
            ).grid(row=0,column=0,padx=16,pady=(14,8),sticky="w")
        for i,(key,label) in enumerate([("requerimientos","Requerimientos nutricionales"),
            ("porciones","Porciones diarias"),("distribucion","Distribucion por tiempo"),
            ("menu","Ejemplos de menu"),("equivalencias","Tablas de equivalencias")]):
            var=tk.BooleanVar(value=True);self._pdf_vars[key]=var
            ctk.CTkCheckBox(left,text=label,variable=var,font=ctk.CTkFont(size=12),
                fg_color=_P,hover_color=_PD,checkmark_color="white"
                ).grid(row=i+1,column=0,padx=16,pady=4,sticky="w")
        right=ctk.CTkFrame(tab,fg_color=(_CARD,"#1a2620"),corner_radius=12,border_width=1,border_color=(_BD,"#2a3d30"))
        right.grid(row=0,column=1,sticky="nsew",padx=(4,8),pady=8);right.grid_columnconfigure(0,weight=1)
        ctk.CTkLabel(right,text="Plantillas",font=ctk.CTkFont(size=14,weight="bold")
            ).grid(row=0,column=0,padx=16,pady=(14,8),sticky="w")
        ctk.CTkButton(right,text="Guardar como plantilla",height=36,font=ctk.CTkFont(size=12),
            fg_color="transparent",border_width=1,border_color=_P,text_color=(_P,"#6ec896"),
            hover_color=("#e8f5ee","#1a2e22"),command=self._guardar_plantilla
            ).grid(row=1,column=0,padx=16,pady=(0,8),sticky="ew")
        ctk.CTkButton(right,text="Cargar desde plantilla",height=36,font=ctk.CTkFont(size=12),
            fg_color="transparent",border_width=1,border_color=_SG,text_color=(_MU,"#9ab0a0"),
            command=self._cargar_plantilla).grid(row=2,column=0,padx=16,pady=(0,16),sticky="ew")
        ef=ctk.CTkFrame(tab,fg_color="transparent")
        ef.grid(row=1,column=0,columnspan=2,padx=8,pady=(4,8),sticky="ew");ef.grid_columnconfigure(0,weight=1)
        ctk.CTkButton(ef,text="Exportar PDF",height=48,font=ctk.CTkFont(size=15,weight="bold"),
            fg_color=_P,hover_color=_PD,command=self._exportar_pdf
            ).grid(row=0,column=0,padx=8,sticky="ew")

    def on_show(self):
        pid=self._app.get_patient_id()
        if pid!=self._paciente_id: self._paciente_id=pid;self._pauta_id=None
        self._refresh_pauta_list()
        if self._paciente_id: self._load_last_weight()

    def _load_last_weight(self):
        try:
            w=db.get_last_weight(self._paciente_id)
            if w: self._var_peso.set(str(w))
        except: pass

    def _refresh_pauta_list(self):
        if not self._paciente_id:
            self._combo_pauta.configure(values=["-- ninguna --"]);self._combo_pauta.set("-- ninguna --");return
        pautas=db.get_pautas_paciente(self._paciente_id)
        if not pautas:
            self._combo_pauta.configure(values=["-- ninguna --"]);self._combo_pauta.set("-- ninguna --")
            self._pauta_id=None;return
        labels=[]
        for p in pautas:
            fecha=(p.get("fecha_creacion") or "")[:10];nombre=p.get("nombre_pauta") or f"Pauta {p['id']}"
            labels.append(f"[{fecha}] {nombre}")
        self._combo_pauta.configure(values=labels)
        if self._pauta_id:
            ids=[p["id"] for p in pautas]
            if self._pauta_id in ids:
                self._combo_pauta.set(labels[ids.index(self._pauta_id)]);return
        self._combo_pauta.set(labels[0]);self._pauta_id=pautas[0]["id"];self._load_pauta(self._pauta_id)

    def _on_pauta_selected(self,label):
        if not self._paciente_id or label=="-- ninguna --": return
        pautas=db.get_pautas_paciente(self._paciente_id)
        labels=[]
        for p in pautas:
            fecha=(p.get("fecha_creacion") or "")[:10];nombre=p.get("nombre_pauta") or f"Pauta {p['id']}"
            labels.append(f"[{fecha}] {nombre}")
        if label in labels: idx=labels.index(label);self._pauta_id=pautas[idx]["id"];self._load_pauta(self._pauta_id)

    def _load_pauta(self,pauta_id):
        p=db.get_pauta(pauta_id)
        if not p: return
        self._var_nombre.set(p.get("nombre_pauta") or "");self._var_obs.set(p.get("observaciones") or "")
        if p.get("peso_calculo"): self._var_peso.set(str(p["peso_calculo"]))
        tipo=p.get("tipo_pauta","omnivoro");self._var_tipo.set(tipo)
        if tipo in _TK: self._combo_tipo.set(_TL[_TK.index(tipo)])
        self._grupos_activos=list(GRUPOS_POR_PAUTA.get(tipo,GRUPOS_POR_PAUTA["omnivoro"]))
        fa_key=p.get("fa_key","liviana");self._var_fa.set(fa_key)
        if fa_key in _FK: self._combo_fa.set(_FL[_FK.index(fa_key)])
        if p.get("prot_gr_kg"): self._var_prot_gkg.set(str(p["prot_gr_kg"]))
        if p.get("lip_pct"): self._var_lip_pct.set(str(p["lip_pct"]))
        if self._lbl_tmb and p.get("tmb"): self._lbl_tmb.configure(text=f"{p['tmb']:.0f} kcal")
        if self._lbl_get and p.get("get"): self._lbl_get.configure(text=f"{p['get']:,.1f}")
        for key,db_key in [("prot","prot_total_g"),("lip","lip_total_g"),("cho","cho_total_g")]:
            if self._macro_rows.get(key) and p.get(db_key):
                self._macro_rows[key].configure(text=f"{p[db_key]:.0f}g")
        self._rebuild_porciones_tab();self._rebuild_menu_tab();self._rebuild_tab4()

    def _calcular(self):
        if not self._paciente_id: messagebox.showwarning("Sin paciente","Selecciona un paciente primero.");return
        patient=db.get_patient(self._paciente_id)
        if not patient: return
        try: peso=float(self._var_peso.get())
        except: messagebox.showerror("Error","El peso debe ser un numero.");return
        sexo="M" if str(patient.get("sex","Femenino")).startswith("F") else "H"
        edad=int(patient.get("age") or 30)
        fa_label=self._combo_fa.get()
        fa_key=_FK[_FL.index(fa_label)] if fa_label in _FL else "liviana";self._var_fa.set(fa_key)
        try: prot_gkg=float(self._var_prot_gkg.get());lip_pct=float(self._var_lip_pct.get())
        except: messagebox.showerror("Error","Proteinas y lipidos deben ser numeros.");return
        tmb=calcular_tmb(sexo,edad,peso);get_val=calcular_get(tmb,fa_key,sexo)
        macros=calcular_macros(get_val,prot_gkg,peso,lip_pct)
        self._tmb=tmb;self._get=get_val;self._macros=macros
        if self._lbl_tmb: self._lbl_tmb.configure(text=f"{tmb:,.0f} kcal")
        if self._lbl_get: self._lbl_get.configure(text=f"{get_val:,.1f}")
        for key,mk in [("prot","prot_g"),("lip","lip_g"),("cho","cho_g")]:
            if self._macro_rows.get(key): self._macro_rows[key].configure(text=f"{macros[mk]:.0f}g")

    def _guardar_requerimientos(self):
        if not self._paciente_id: messagebox.showwarning("Sin paciente","Selecciona un paciente primero.");return
        if self._tmb is None: self._calcular()
        if self._tmb is None: return
        fa_label=self._combo_fa.get();fa_key=_FK[_FL.index(fa_label)] if fa_label in _FL else "liviana"
        tipo_label=self._combo_tipo.get();tipo_key=_TK[_TL.index(tipo_label)] if tipo_label in _TL else "omnivoro"
        try: peso=float(self._var_peso.get());prot_gkg=float(self._var_prot_gkg.get());lip_pct=float(self._var_lip_pct.get())
        except: messagebox.showerror("Error","Verifica los valores numericos.");return
        patient=db.get_patient(self._paciente_id)
        sexo="M" if patient and str(patient.get("sex","Femenino")).startswith("F") else "H"
        fa_val=get_fa_valor(fa_key,sexo)
        data={"paciente_id":self._paciente_id,"fecha_creacion":datetime.now().strftime("%Y-%m-%d"),
            "tipo_pauta":tipo_key,"nombre_pauta":self._var_nombre.get().strip() or None,
            "peso_calculo":peso,"tmb":self._tmb,"fa":fa_val,"fa_key":fa_key,"get":self._get,
            "prot_gr_kg":prot_gkg,"prot_total_g":self._macros["prot_g"],
            "prot_total_kcal":self._macros["prot_kcal"],"prot_pct":self._macros["prot_pct"],
            "lip_pct":lip_pct,"lip_total_kcal":self._macros["lip_kcal"],"lip_total_g":self._macros["lip_g"],
            "cho_total_kcal":self._macros["cho_kcal"],"cho_total_g":self._macros["cho_g"],
            "cho_g_kg":self._macros["cho_g_kg"],"tabla_equivalencias":tipo_key,
            "incluir_equivalencias":1,"observaciones":self._var_obs.get().strip() or None}
        if self._pauta_id: db.update_pauta(self._pauta_id,data)
        else: self._pauta_id=db.insert_pauta(data)
        self._grupos_activos=list(GRUPOS_POR_PAUTA.get(tipo_key,GRUPOS_POR_PAUTA["omnivoro"]))
        self._refresh_pauta_list();self._rebuild_porciones_tab();self._rebuild_tab4()
        if hasattr(self._app,"show_toast"): self._app.show_toast("v Requerimientos guardados")

    def _nueva_pauta(self):
        if not self._paciente_id: messagebox.showwarning("Sin paciente","Selecciona un paciente primero.");return
        self._pauta_id=None;self._tmb=self._get=self._macros=None
        self._var_nombre.set("");self._var_obs.set("");self._var_tipo.set("omnivoro")
        self._combo_tipo.set(_TL[0]);self._var_fa.set("liviana")
        self._combo_fa.set(_FL[1] if len(_FL)>1 else _FL[0])
        self._var_prot_gkg.set("1.2");self._var_lip_pct.set("28.0")
        if self._lbl_tmb: self._lbl_tmb.configure(text="--")
        if self._lbl_get: self._lbl_get.configure(text="--")
        for k in self._macro_rows: self._macro_rows[k].configure(text="--")
        self._grupos_activos=list(GRUPOS_POR_PAUTA["omnivoro"])
        self._rebuild_porciones_tab();self._rebuild_menu_tab();self._rebuild_tab4()

    def _eliminar_pauta(self):
        if not self._pauta_id: messagebox.showwarning("Sin pauta","No hay pauta seleccionada.");return
        if messagebox.askyesno("Confirmar","Eliminar esta pauta y todos sus datos?",icon="warning"):
            db.delete_pauta(self._pauta_id);self._pauta_id=None;self._refresh_pauta_list();self._nueva_pauta()

    def _on_tipo_changed(self,label):
        if label in _TL:
            key=_TK[_TL.index(label)];self._var_tipo.set(key)
            self._grupos_activos=list(GRUPOS_POR_PAUTA.get(key,GRUPOS_POR_PAUTA["omnivoro"]))

    def _schedule_save(self):
        if self._save_job: self.after_cancel(self._save_job)
        self._save_job=self.after(600,self._autosave)

    def _autosave(self):
        self._save_job=None
        if not self._pauta_id: return
        porciones={g:self._get_porcion(g) for g in self._grupos_activos}
        distribucion=self._get_distribucion_dict()
        try: db.save_porciones(self._pauta_id,porciones);db.save_distribucion(self._pauta_id,distribucion)
        except: pass

    def _guardar_plantilla(self):
        if not self._pauta_id: messagebox.showwarning("Sin pauta","Guarda la pauta primero.");return
        dlg=ctk.CTkToplevel(self);dlg.title("Guardar plantilla");dlg.geometry("380x180");dlg.grab_set()
        ctk.CTkLabel(dlg,text="Nombre de la plantilla:",font=ctk.CTkFont(size=13)
            ).pack(padx=20,pady=(20,6))
        var_n=tk.StringVar()
        ctk.CTkEntry(dlg,textvariable=var_n,height=36,font=ctk.CTkFont(size=12)).pack(padx=20,fill="x")
        def do_save():
            nombre=var_n.get().strip()
            if not nombre: messagebox.showwarning("Error","Ingresa un nombre.",parent=dlg);return
            tipo=self._var_tipo.get();pid_t=db.insert_pauta_plantilla(nombre,tipo)
            porciones={g:self._get_porcion(g) for g in self._grupos_activos}
            db.save_plantilla_porciones(pid_t,porciones)
            db.save_plantilla_distribucion(pid_t,self._get_distribucion_dict())
            dlg.destroy()
            if hasattr(self._app,"show_toast"): self._app.show_toast("v Plantilla guardada")
        ctk.CTkButton(dlg,text="Guardar",height=36,fg_color=_P,hover_color=_PD,
            command=do_save).pack(padx=20,pady=16,fill="x")

    def _cargar_plantilla(self):
        plantillas=db.get_pauta_plantillas()
        if not plantillas: messagebox.showinfo("Sin plantillas","No hay plantillas guardadas.");return
        dlg=ctk.CTkToplevel(self);dlg.title("Cargar plantilla");dlg.geometry("420x360");dlg.grab_set()
        ctk.CTkLabel(dlg,text="Selecciona una plantilla:",font=ctk.CTkFont(size=13,weight="bold")
            ).pack(padx=16,pady=(16,8))
        sc=ctk.CTkScrollableFrame(dlg,fg_color="transparent");sc.pack(fill="both",expand=True,padx=8,pady=(0,8))
        sc.grid_columnconfigure(0,weight=1)
        for i,pt in enumerate(plantillas):
            rf=ctk.CTkFrame(sc,fg_color=(_BG,"#141f19"),corner_radius=8)
            rf.grid(row=i,column=0,sticky="ew",padx=4,pady=3);rf.grid_columnconfigure(0,weight=1)
            ctk.CTkLabel(rf,text=pt.get("nombre",f"Plantilla {pt['id']}"),
                font=ctk.CTkFont(size=12,weight="bold"),anchor="w"
                ).grid(row=0,column=0,padx=10,pady=(8,0),sticky="w")
            ctk.CTkLabel(rf,text=NOMBRES_TIPOS_PAUTA.get(pt.get("tipo_pauta",""),pt.get("tipo_pauta","")),
                font=ctk.CTkFont(size=10),text_color=_MU,anchor="w"
                ).grid(row=1,column=0,padx=10,pady=(0,8),sticky="w")
            def do_load(ptid=pt["id"]):
                porciones=db.get_plantilla_porciones(ptid);distribucion=db.get_plantilla_distribucion(ptid)
                if self._pauta_id: db.save_porciones(self._pauta_id,porciones);db.save_distribucion(self._pauta_id,distribucion)
                self._rebuild_porciones_tab();dlg.destroy()
                if hasattr(self._app,"show_toast"): self._app.show_toast("v Plantilla cargada")
            ctk.CTkButton(rf,text="Cargar",height=28,width=80,font=ctk.CTkFont(size=11),
                fg_color=_P,hover_color=_PD,command=do_load
                ).grid(row=0,column=1,rowspan=2,padx=10,pady=8)

    def _exportar_pdf(self):
        if not self._pauta_id: messagebox.showwarning("Sin pauta","Guarda una pauta antes de exportar.");return
        if not self._paciente_id: messagebox.showwarning("Sin paciente","Selecciona un paciente primero.");return
        path=filedialog.asksaveasfilename(defaultextension=".pdf",filetypes=[("PDF","*.pdf")],title="Guardar PDF")
        if not path: return
        try: from modules.pautas_alimentacion.pdf_pautas import generar_pdf_pauta
        except ImportError as e: messagebox.showerror("Error",f"No se puede importar el generador PDF:\n{e}");return
        try:
            generar_pdf_pauta(path=path,paciente=db.get_patient(self._paciente_id),
                pauta=db.get_pauta(self._pauta_id),porciones=db.get_porciones(self._pauta_id),
                distribucion=db.get_distribucion(self._pauta_id),menu=db.get_menu_pauta(self._pauta_id),
                opciones_pdf={k:v.get() for k,v in self._pdf_vars.items()})
            if hasattr(self._app,"show_toast"): self._app.show_toast("v PDF exportado")
            messagebox.showinfo("Exito",f"PDF generado:\n{path}")
        except Exception as e: messagebox.showerror("Error al generar PDF",str(e))
