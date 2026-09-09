// 本文件由 scripts/gen-config.mjs 自动生成，请勿手改。
// eslint-disable
export const LAYER_SPATIAL_CONFIG = {
  "crs": "EPSG:4326",
  "bounds": {
    "west": 112.177287,
    "south": 34.23536324852,
    "east": 116.68009236105,
    "north": 36.454202
  },
  "resolution": [
    0.00224578821,
    0.00224578821
  ],
  "width": 2005,
  "height": 988,
  "template": "data/processed/aligned/clcd_2020_epsg4326_250m.tif",
  "rectanglePolicy": "all_foundation_rasters_use_this_single_rectangle",
  "layers": [
    {
      "layerKey": "clcd",
      "dataType": "class",
      "resampling": "nearest",
      "years": {
        "2000": {
          "source": "1.土地利用_CLCD_30m/CLCD_2000_黄河滩区中下游边界.tif",
          "aligned": "data/processed/aligned/clcd_2000_epsg4326_250m.tif",
          "converted": true,
          "overlay": "data/overlays/clcd_2000.png",
          "queryGrid": "data/query_grids/clcd_2000.json"
        },
        "2005": {
          "source": "1.土地利用_CLCD_30m/CLCD_2005_黄河滩区中下游边界.tif",
          "aligned": "data/processed/aligned/clcd_2005_epsg4326_250m.tif",
          "converted": true,
          "overlay": "data/overlays/clcd_2005.png",
          "queryGrid": "data/query_grids/clcd_2005.json"
        },
        "2010": {
          "source": "1.土地利用_CLCD_30m/CLCD_2010_黄河滩区中下游边界.tif",
          "aligned": "data/processed/aligned/clcd_2010_epsg4326_250m.tif",
          "converted": true,
          "overlay": "data/overlays/clcd_2010.png",
          "queryGrid": "data/query_grids/clcd_2010.json"
        },
        "2015": {
          "source": "1.土地利用_CLCD_30m/CLCD_2015_黄河滩区中下游边界.tif",
          "aligned": "data/processed/aligned/clcd_2015_epsg4326_250m.tif",
          "converted": true,
          "overlay": "data/overlays/clcd_2015.png",
          "queryGrid": "data/query_grids/clcd_2015.json"
        },
        "2020": {
          "source": "1.土地利用_CLCD_30m/CLCD_2020_黄河滩区中下游边界.tif",
          "aligned": "data/processed/aligned/clcd_2020_epsg4326_250m.tif",
          "converted": true,
          "overlay": "data/overlays/clcd_2020.png",
          "queryGrid": "data/query_grids/clcd_2020.json"
        },
        "2024": {
          "source": "1.土地利用_CLCD_30m/CLCD_2024_黄河滩区中下游裁剪.tif",
          "aligned": "data/processed/aligned/clcd_2024_epsg4326_250m.tif",
          "converted": true,
          "overlay": "data/overlays/clcd_2024.png",
          "queryGrid": "data/query_grids/clcd_2024.json"
        }
      }
    },
    {
      "layerKey": "ntl",
      "dataType": "cont",
      "resampling": "bilinear",
      "years": {
        "2000": {
          "source": "2.夜间灯光_LongNTL_500m/LongNTL_2000_黄河滩区中下游边界.tif",
          "aligned": "data/processed/aligned/ntl_2000_epsg4326_250m.tif",
          "converted": true,
          "overlay": "data/overlays/ntl_2000.png",
          "queryGrid": "data/query_grids/ntl_2000.json"
        },
        "2005": {
          "source": "2.夜间灯光_LongNTL_500m/LongNTL_2005_黄河滩区中下游边界.tif",
          "aligned": "data/processed/aligned/ntl_2005_epsg4326_250m.tif",
          "converted": true,
          "overlay": "data/overlays/ntl_2005.png",
          "queryGrid": "data/query_grids/ntl_2005.json"
        },
        "2010": {
          "source": "2.夜间灯光_LongNTL_500m/LongNTL_2010_黄河滩区中下游边界.tif",
          "aligned": "data/processed/aligned/ntl_2010_epsg4326_250m.tif",
          "converted": true,
          "overlay": "data/overlays/ntl_2010.png",
          "queryGrid": "data/query_grids/ntl_2010.json"
        },
        "2015": {
          "source": "2.夜间灯光_LongNTL_500m/LongNTL_2015_黄河滩区中下游边界.tif",
          "aligned": "data/processed/aligned/ntl_2015_epsg4326_250m.tif",
          "converted": true,
          "overlay": "data/overlays/ntl_2015.png",
          "queryGrid": "data/query_grids/ntl_2015.json"
        },
        "2020": {
          "source": "2.夜间灯光_LongNTL_500m/LongNTL_2020_黄河滩区中下游边界.tif",
          "aligned": "data/processed/aligned/ntl_2020_epsg4326_250m.tif",
          "converted": true,
          "overlay": "data/overlays/ntl_2020.png",
          "queryGrid": "data/query_grids/ntl_2020.json"
        },
        "2024": {
          "source": "2.夜间灯光_LongNTL_500m/LongNTL_2024_黄河滩区中下游边界.tif",
          "aligned": "data/processed/aligned/ntl_2024_epsg4326_250m.tif",
          "converted": true,
          "overlay": "data/overlays/ntl_2024.png",
          "queryGrid": "data/query_grids/ntl_2024.json"
        }
      }
    },
    {
      "layerKey": "gdp",
      "dataType": "cont",
      "resampling": "bilinear",
      "years": {
        "2000": {
          "source": "4.GDP_1km/GDP_2000_黄河滩区中下游边界.tif",
          "aligned": "data/processed/aligned/gdp_2000_epsg4326_250m.tif",
          "converted": true,
          "overlay": "data/overlays/gdp_2000.png",
          "queryGrid": "data/query_grids/gdp_2000.json"
        },
        "2005": {
          "source": "4.GDP_1km/GDP_2005_黄河滩区中下游边界.tif",
          "aligned": "data/processed/aligned/gdp_2005_epsg4326_250m.tif",
          "converted": true,
          "overlay": "data/overlays/gdp_2005.png",
          "queryGrid": "data/query_grids/gdp_2005.json"
        },
        "2010": {
          "source": "4.GDP_1km/GDP_2010_黄河滩区中下游边界.tif",
          "aligned": "data/processed/aligned/gdp_2010_epsg4326_250m.tif",
          "converted": true,
          "overlay": "data/overlays/gdp_2010.png",
          "queryGrid": "data/query_grids/gdp_2010.json"
        },
        "2015": {
          "source": "4.GDP_1km/GDP_2015_黄河滩区中下游边界.tif",
          "aligned": "data/processed/aligned/gdp_2015_epsg4326_250m.tif",
          "converted": true,
          "overlay": "data/overlays/gdp_2015.png",
          "queryGrid": "data/query_grids/gdp_2015.json"
        },
        "2020": {
          "source": "4.GDP_1km/GDP_2020_黄河滩区中下游边界.tif",
          "aligned": "data/processed/aligned/gdp_2020_epsg4326_250m.tif",
          "converted": true,
          "overlay": "data/overlays/gdp_2020.png",
          "queryGrid": "data/query_grids/gdp_2020.json"
        },
        "2024": {
          "source": "4.GDP_1km/GDP_2024_黄河滩区中下游边界.tif",
          "aligned": "data/processed/aligned/gdp_2024_epsg4326_250m.tif",
          "converted": true,
          "overlay": "data/overlays/gdp_2024.png",
          "queryGrid": "data/query_grids/gdp_2024.json"
        }
      }
    },
    {
      "layerKey": "ndvi",
      "dataType": "cont",
      "resampling": "bilinear",
      "years": {
        "2000": {
          "source": "5.NDVI_250m/MODIS_NDVI_AnnualMean_2000.tif",
          "aligned": "data/processed/aligned/ndvi_2000_epsg4326_250m.tif",
          "converted": true,
          "overlay": "data/overlays/ndvi_2000.png",
          "queryGrid": "data/query_grids/ndvi_2000.json"
        },
        "2005": {
          "source": "5.NDVI_250m/MODIS_NDVI_AnnualMean_2005.tif",
          "aligned": "data/processed/aligned/ndvi_2005_epsg4326_250m.tif",
          "converted": true,
          "overlay": "data/overlays/ndvi_2005.png",
          "queryGrid": "data/query_grids/ndvi_2005.json"
        },
        "2010": {
          "source": "5.NDVI_250m/MODIS_NDVI_AnnualMean_2010.tif",
          "aligned": "data/processed/aligned/ndvi_2010_epsg4326_250m.tif",
          "converted": true,
          "overlay": "data/overlays/ndvi_2010.png",
          "queryGrid": "data/query_grids/ndvi_2010.json"
        },
        "2015": {
          "source": "5.NDVI_250m/MODIS_NDVI_AnnualMean_2015.tif",
          "aligned": "data/processed/aligned/ndvi_2015_epsg4326_250m.tif",
          "converted": true,
          "overlay": "data/overlays/ndvi_2015.png",
          "queryGrid": "data/query_grids/ndvi_2015.json"
        },
        "2020": {
          "source": "5.NDVI_250m/MODIS_NDVI_AnnualMean_2020.tif",
          "aligned": "data/processed/aligned/ndvi_2020_epsg4326_250m.tif",
          "converted": true,
          "overlay": "data/overlays/ndvi_2020.png",
          "queryGrid": "data/query_grids/ndvi_2020.json"
        },
        "2024": {
          "source": "5.NDVI_250m/MODIS_NDVI_AnnualMean_2024.tif",
          "aligned": "data/processed/aligned/ndvi_2024_epsg4326_250m.tif",
          "converted": true,
          "overlay": "data/overlays/ndvi_2024.png",
          "queryGrid": "data/query_grids/ndvi_2024.json"
        }
      }
    },
    {
      "layerKey": "evi",
      "dataType": "cont",
      "resampling": "bilinear",
      "years": {
        "2000": {
          "source": "6.EVI_250m/MODIS_EVI_AnnualMean_2000.tif",
          "aligned": "data/processed/aligned/evi_2000_epsg4326_250m.tif",
          "converted": true,
          "overlay": "data/overlays/evi_2000.png",
          "queryGrid": "data/query_grids/evi_2000.json"
        },
        "2005": {
          "source": "6.EVI_250m/MODIS_EVI_AnnualMean_2005.tif",
          "aligned": "data/processed/aligned/evi_2005_epsg4326_250m.tif",
          "converted": true,
          "overlay": "data/overlays/evi_2005.png",
          "queryGrid": "data/query_grids/evi_2005.json"
        },
        "2010": {
          "source": "6.EVI_250m/MODIS_EVI_AnnualMean_2010.tif",
          "aligned": "data/processed/aligned/evi_2010_epsg4326_250m.tif",
          "converted": true,
          "overlay": "data/overlays/evi_2010.png",
          "queryGrid": "data/query_grids/evi_2010.json"
        },
        "2015": {
          "source": "6.EVI_250m/MODIS_EVI_AnnualMean_2015.tif",
          "aligned": "data/processed/aligned/evi_2015_epsg4326_250m.tif",
          "converted": true,
          "overlay": "data/overlays/evi_2015.png",
          "queryGrid": "data/query_grids/evi_2015.json"
        },
        "2020": {
          "source": "6.EVI_250m/MODIS_EVI_AnnualMean_2020.tif",
          "aligned": "data/processed/aligned/evi_2020_epsg4326_250m.tif",
          "converted": true,
          "overlay": "data/overlays/evi_2020.png",
          "queryGrid": "data/query_grids/evi_2020.json"
        },
        "2024": {
          "source": "6.EVI_250m/MODIS_EVI_AnnualMean_2024.tif",
          "aligned": "data/processed/aligned/evi_2024_epsg4326_250m.tif",
          "converted": true,
          "overlay": "data/overlays/evi_2024.png",
          "queryGrid": "data/query_grids/evi_2024.json"
        }
      }
    },
    {
      "layerKey": "water",
      "dataType": "class",
      "resampling": "nearest",
      "years": {
        "2000": {
          "source": "7.水体_30m/JRC_waterClass_target_2000_data_2000.tif",
          "aligned": "data/processed/aligned/water_2000_epsg4326_250m.tif",
          "converted": true,
          "overlay": "data/overlays/water_2000.png",
          "queryGrid": "data/query_grids/water_2000.json"
        },
        "2005": {
          "source": "7.水体_30m/JRC_waterClass_target_2005_data_2005.tif",
          "aligned": "data/processed/aligned/water_2005_epsg4326_250m.tif",
          "converted": true,
          "overlay": "data/overlays/water_2005.png",
          "queryGrid": "data/query_grids/water_2005.json"
        },
        "2010": {
          "source": "7.水体_30m/JRC_waterClass_target_2010_data_2010.tif",
          "aligned": "data/processed/aligned/water_2010_epsg4326_250m.tif",
          "converted": true,
          "overlay": "data/overlays/water_2010.png",
          "queryGrid": "data/query_grids/water_2010.json"
        },
        "2015": {
          "source": "7.水体_30m/JRC_waterClass_target_2015_data_2015.tif",
          "aligned": "data/processed/aligned/water_2015_epsg4326_250m.tif",
          "converted": true,
          "overlay": "data/overlays/water_2015.png",
          "queryGrid": "data/query_grids/water_2015.json"
        },
        "2020": {
          "source": "7.水体_30m/JRC_waterClass_target_2020_data_2020.tif",
          "aligned": "data/processed/aligned/water_2020_epsg4326_250m.tif",
          "converted": true,
          "overlay": "data/overlays/water_2020.png",
          "queryGrid": "data/query_grids/water_2020.json"
        },
        "2024": {
          "source": "7.水体_30m/JRC_waterClass_target_2024_data_2021.tif",
          "aligned": "data/processed/aligned/water_2024_epsg4326_250m.tif",
          "converted": true,
          "overlay": "data/overlays/water_2024.png",
          "queryGrid": "data/query_grids/water_2024.json"
        }
      }
    },
    {
      "layerKey": "landscan",
      "dataType": "cont",
      "resampling": "bilinear",
      "years": {
        "2000": {
          "source": "3.人口_LandScan_1km/LandScan_2000_黄河滩区中下游边界.tif",
          "aligned": "data/processed/aligned/landscan_2000_epsg4326_250m.tif",
          "converted": false
        },
        "2005": {
          "source": "3.人口_LandScan_1km/LandScan_2005_黄河滩区中下游边界.tif",
          "aligned": "data/processed/aligned/landscan_2005_epsg4326_250m.tif",
          "converted": false
        },
        "2010": {
          "source": "3.人口_LandScan_1km/LandScan_2010_黄河滩区中下游边界.tif",
          "aligned": "data/processed/aligned/landscan_2010_epsg4326_250m.tif",
          "converted": false
        },
        "2015": {
          "source": "3.人口_LandScan_1km/LandScan_2015_黄河滩区中下游边界.tif",
          "aligned": "data/processed/aligned/landscan_2015_epsg4326_250m.tif",
          "converted": false
        },
        "2020": {
          "source": "3.人口_LandScan_1km/LandScan_2020_黄河滩区中下游边界.tif",
          "aligned": "data/processed/aligned/landscan_2020_epsg4326_250m.tif",
          "converted": false
        },
        "2024": {
          "source": "3.人口_LandScan_1km/LandScan_2024_黄河滩区中下游边界.tif",
          "aligned": "data/processed/aligned/landscan_2024_epsg4326_250m.tif",
          "converted": false
        }
      }
    },
    {
      "layerKey": "dem",
      "dataType": "cont",
      "resampling": "bilinear",
      "years": {
        "static": {
          "source": "3.DEM_NASA_30m/DEM_黄河滩区中下游边界.tif",
          "aligned": "data/processed/aligned/dem_static_epsg4326_250m.tif",
          "converted": false
        }
      }
    },
    {
      "layerKey": "terraclimate",
      "dataType": "cont",
      "resampling": "bilinear",
      "years": {
        "2000": {
          "source": "9.TerraClimate水文数据/TanQu_TerraClimate_Core_2000.tif",
          "aligned": "data/processed/aligned/terraclimate_2000_epsg4326_250m.tif",
          "converted": false
        },
        "2005": {
          "source": "9.TerraClimate水文数据/TanQu_TerraClimate_Core_2005.tif",
          "aligned": "data/processed/aligned/terraclimate_2005_epsg4326_250m.tif",
          "converted": false
        },
        "2010": {
          "source": "9.TerraClimate水文数据/TanQu_TerraClimate_Core_2010.tif",
          "aligned": "data/processed/aligned/terraclimate_2010_epsg4326_250m.tif",
          "converted": false
        },
        "2015": {
          "source": "9.TerraClimate水文数据/TanQu_TerraClimate_Core_2015.tif",
          "aligned": "data/processed/aligned/terraclimate_2015_epsg4326_250m.tif",
          "converted": false
        },
        "2020": {
          "source": "9.TerraClimate水文数据/TanQu_TerraClimate_Core_2020.tif",
          "aligned": "data/processed/aligned/terraclimate_2020_epsg4326_250m.tif",
          "converted": false
        },
        "2024": {
          "source": "9.TerraClimate水文数据/TanQu_TerraClimate_Core_2024.tif",
          "aligned": "data/processed/aligned/terraclimate_2024_epsg4326_250m.tif",
          "converted": false
        }
      }
    }
  ]
};
