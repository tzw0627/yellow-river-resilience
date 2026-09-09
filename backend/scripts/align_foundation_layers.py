from __future__ import annotations
import json, os
from pathlib import Path
import numpy as np, rasterio
from PIL import Image
from rasterio.enums import Resampling
from rasterio.warp import reproject

ROOT=Path(__file__).resolve().parents[2]
SRC=Path(os.environ.get('HPU_REAL_DATA_ROOT',r'C:\Users\25450\Desktop\智能体数据集_黄河滩区边界裁剪结果_最终(6)\智能体数据集_黄河滩区边界裁剪结果_最终'))
TPL=ROOT/'data/processed/aligned/clcd_2020_epsg4326_250m.tif'
AD=ROOT/'data/processed/aligned'; OD=ROOT/'frontend/data/overlays'; QD=ROOT/'frontend/data/query_grids'; CD=ROOT/'frontend/data/config'
GW,GH=200,99
SHOW={'clcd','water','ntl','gdp','ndvi','evi'}; CLS={'clcd','water'}
PAL={'clcd':{1:(230,204,110),2:(38,110,62),3:(98,140,58),4:(140,178,78),5:(32,118,168),6:(188,176,132),7:(150,108,66),8:(196,72,42),9:(108,102,88)},'water':{1:(158,210,228),2:(28,128,188),3:(8,72,128)}}
COL={'ndvi':((218,222,170),(87,130,51)),'evi':((214,221,169),(36,132,91)),'ntl':((47,56,53),(231,177,51)),'gdp':((89,69,46),(214,145,75)),'landscan':((244,232,178),(174,77,43)),'dem':((90,110,90),(238,226,188)),'terraclimate':((99,145,180),(219,185,92))}
Y=[2000,2005,2010,2015,2020,2024]
DS={
'clcd':('class',{2000:'1.土地利用_CLCD_30m/CLCD_2000_黄河滩区中下游边界.tif',2005:'1.土地利用_CLCD_30m/CLCD_2005_黄河滩区中下游边界.tif',2010:'1.土地利用_CLCD_30m/CLCD_2010_黄河滩区中下游边界.tif',2015:'1.土地利用_CLCD_30m/CLCD_2015_黄河滩区中下游边界.tif',2020:'1.土地利用_CLCD_30m/CLCD_2020_黄河滩区中下游边界.tif',2024:'1.土地利用_CLCD_30m/CLCD_2024_黄河滩区中下游裁剪.tif'}),
'ntl':('cont',{y:f'2.夜间灯光_LongNTL_500m/LongNTL_{y}_黄河滩区中下游边界.tif' for y in Y}),
'gdp':('cont',{y:f'4.GDP_1km/GDP_{y}_黄河滩区中下游边界.tif' for y in Y}),
'ndvi':('cont',{y:f'5.NDVI_250m/MODIS_NDVI_AnnualMean_{y}.tif' for y in Y}),
'evi':('cont',{y:f'6.EVI_250m/MODIS_EVI_AnnualMean_{y}.tif' for y in Y}),
'water':('class',{2000:'7.水体_30m/JRC_waterClass_target_2000_data_2000.tif',2005:'7.水体_30m/JRC_waterClass_target_2005_data_2005.tif',2010:'7.水体_30m/JRC_waterClass_target_2010_data_2010.tif',2015:'7.水体_30m/JRC_waterClass_target_2015_data_2015.tif',2020:'7.水体_30m/JRC_waterClass_target_2020_data_2020.tif',2024:'7.水体_30m/JRC_waterClass_target_2024_data_2021.tif'}),
'landscan':('cont',{y:f'3.人口_LandScan_1km/LandScan_{y}_黄河滩区中下游边界.tif' for y in Y}),
'dem':('cont',{'static':'3.DEM_NASA_30m/DEM_黄河滩区中下游边界.tif'}),
'terraclimate':('cont',{y:f'9.TerraClimate水文数据/TanQu_TerraClimate_Core_{y}.tif' for y in Y})}

def meta(p):
    with rasterio.open(p) as s:
        return {'crs':s.crs.to_string() if s.crs else None,'epsg':s.crs.to_epsg() if s.crs else None,'bounds':dict(west=s.bounds.left,south=s.bounds.bottom,east=s.bounds.right,north=s.bounds.top),'res':[abs(s.res[0]),abs(s.res[1])],'size':[s.width,s.height],'nodata':s.nodata,'bands':s.count}

def ok(a,n):
    v=np.isfinite(a)
    if n is not None: v&=a!=n
    for x in (-9999,-2147483647,-3.4028234663852886e38): v&=~np.isclose(a,x)
    return v

def align(layer,yr,src,kind,t):
    out=AD/f'{layer}_{yr}_epsg4326_250m.tif'
    if out.resolve()==TPL.resolve(): return out
    out.parent.mkdir(parents=True,exist_ok=True)
    with rasterio.open(src) as s:
        dt='uint8' if kind=='class' else 'float32'; dst=np.zeros((s.count,t.height,t.width),dtype=dt)
        if kind!='class': dst[:]=np.nan
        for b in range(1,s.count+1):
            reproject(rasterio.band(s,b),dst[b-1],src_transform=s.transform,src_crs=s.crs,src_nodata=s.nodata,dst_transform=t.transform,dst_crs=t.crs,dst_nodata=(0 if kind=='class' else np.nan),resampling=(Resampling.nearest if kind=='class' else Resampling.bilinear))
        prof=t.profile.copy(); prof.update(driver='GTiff',count=s.count,dtype=dt,nodata=(0 if kind=='class' else np.nan),compress='deflate')
        with rasterio.open(out,'w',**prof) as d: d.write(dst)
    return out

def overlay(layer,yr,kind,p):
    with rasterio.open(p) as s: a=s.read(1).astype('float32' if kind!='class' else 'uint8'); n=s.nodata
    rgba=np.zeros((*a.shape,4),dtype=np.uint8)
    if kind=='class':
        for val,c in PAL[layer].items(): m=a==val; rgba[m,:3]=c; rgba[m,3]=240
        if n is not None: rgba[a==n,3]=0
    else:
        v=ok(a,n); lo,hi=np.nanpercentile(a[v],[2,98]) if v.any() else (0,1); z=np.nan_to_num(np.clip((a-lo)/(hi-lo or 1),0,1),nan=0.0); s,e=[np.array(c,dtype=np.float32) for c in COL.get(layer,COL['ndvi'])]; rgba[:,:,:3]=(s+(e-s)*z[...,None]).astype(np.uint8); rgba[:,:,3]=np.where(v,235,0)
    OD.mkdir(parents=True,exist_ok=True); o=OD/f'{layer}_{yr}.png'; Image.fromarray(rgba,'RGBA').save(o,compress_level=1); return o

def grid(layer,yr,kind,p):
    with rasterio.open(p) as s:
        r=Resampling.nearest if kind=='class' else Resampling.average; a=s.read(1,out_shape=(GH,GW),resampling=r,masked=True).astype('float32').filled(np.nan)
        if s.nodata is not None: a[np.isclose(a,s.nodata)]=np.nan
        pay={'layer':layer,'year':yr,'source':str(p),'width':GW,'height':GH,'bounds':dict(west=s.bounds.left,south=s.bounds.bottom,east=s.bounds.right,north=s.bounds.top),'values':[[None if np.isnan(x) else (int(x) if kind=='class' else round(float(x),4)) for x in row] for row in a]}
    QD.mkdir(parents=True,exist_ok=True); o=QD/f'{layer}_{yr}.json'; o.write_text(json.dumps(pay,ensure_ascii=False),encoding='utf-8'); return o

def stat(p):
    with rasterio.open(p) as s:
        a=s.read(1).astype('float32'); v=ok(a,s.nodata); vals=a[v]
        if vals.size==0: return {'available':False,'validRatio':0,'min':None,'median':None,'p90':None,'max':None}
        q=np.nanpercentile(vals,[0,50,90,100]); return {'available':True,'validRatio':round(float(vals.size/a.size),6),'min':round(float(q[0]),4),'median':round(float(q[1]),4),'p90':round(float(q[2]),4),'max':round(float(q[3]),4)}

def main():
    rows=[]; layers=[]; stats={}
    with rasterio.open(TPL) as t:
        b=t.bounds; base={'crs':'EPSG:4326','bounds':dict(west=b.left,south=b.bottom,east=b.right,north=b.top),'resolution':[abs(t.res[0]),abs(t.res[1])],'width':t.width,'height':t.height}
        for layer,(kind,yrs) in DS.items():
            le={'layerKey':layer,'dataType':kind,'resampling':'nearest' if kind=='class' else 'bilinear','years':{}}
            for yr,rel in yrs.items():
                sp=SRC/rel
                if not sp.exists(): continue
                print('align',layer,yr); m=meta(sp); ap=align(layer,yr,sp,kind,t); st=stat(ap); stats.setdefault(str(yr),{})[layer]={**st,'sourceYear':yr}
                ent={'source':rel,'aligned':str(ap.relative_to(ROOT)).replace('\\','/'),'converted':False}
                if layer in SHOW and isinstance(yr,int):
                    op=overlay(layer,yr,kind,ap); gp=grid(layer,yr,kind,ap); ent.update(overlay=str(op.relative_to(ROOT/'frontend')).replace('\\','/'),queryGrid=str(gp.relative_to(ROOT/'frontend')).replace('\\','/'),converted=True)
                le['years'][str(yr)]=ent; rows.append((layer,yr,m,ent['aligned'],le['resampling']))
            layers.append(le)
    CD.mkdir(parents=True,exist_ok=True)
    (CD/'layerSpatialConfig.js').write_text('window.LAYER_SPATIAL_CONFIG = '+json.dumps({**base,'template':'data/processed/aligned/clcd_2020_epsg4326_250m.tif','rectanglePolicy':'all_foundation_rasters_use_this_single_rectangle','layers':layers},ensure_ascii=False,indent=2)+';\n',encoding='utf-8')
    (CD/'layerStatsAligned.js').write_text('window.LAYER_STATS_ALIGNED = '+json.dumps(stats,ensure_ascii=False,indent=2)+';\n',encoding='utf-8')
    lines=['# 图层空间配准检查报告','','## 统一空间基准',f'- CRS: `{base["crs"]}`',f'- Bounds: `{base["bounds"]}`',f'- Resolution: `{base["resolution"]}`',f'- Size: `{base["width"]} x {base["height"]}`','','| 图层 | 年份 | 原始 CRS/EPSG | 原始 bounds | 原始分辨率 | 输出文件 | 重采样 | 是否已修复 |','|---|---:|---|---|---|---|---|---|']
    for layer,yr,m,ap,rs in rows: lines.append(f'| {layer} | {yr} | {m["epsg"] or m["crs"]} | {m["bounds"]} | {m["res"]} | `{ap}` | {rs} | 是 |')
    lines += ['','## 结论','','所有栅格均已统一到 CLCD 2020 模板网格：EPSG:4326、同一 bounds、同一 transform、同一 width/height。分类图层使用 nearest，连续变量使用 bilinear。前端应统一使用 layerSpatialConfig.js 中的 rectangle。']
    (ROOT/'alignment_report.md').write_text('\n'.join(lines),encoding='utf-8')
if __name__=='__main__': main()
