window.LAYER_DATA_CONFIG = {
  sourceRoot: "C:/Users/25450/Desktop/智能体数据集_黄河滩区边界裁剪结果_最终(6)/智能体数据集_黄河滩区边界裁剪结果_最终",
  displayYears: [2000, 2005, 2010, 2015, 2020, 2024],
  note: "真实数据来自桌面 智能体数据集_黄河滩区边界裁剪结果_最终(6)。GeoTIFF 不能被 Cesium 直接高效加载；converted=true 表示已有前端 PNG/查询网格派生产物，converted=false 表示已登记真实源路径但仍需转瓦片/PNG/JSON。",
  layers: {
    clcd: {
      key: "clcd",
      label: "CLCD",
      category: "土地利用/覆被变化数据",
      type: "raster",
      format: "GeoTIFF",
      sourceFolder: "1.土地利用_CLCD_30m",
      resolution: "30 m",
      cesiumLoad: "requires_tiles_or_overlay",
      conversion: "categorical_nearest_to_xyz_tiles_or_png_overlay",
      years: {
        2000: { source: "1.土地利用_CLCD_30m/CLCD_2000_黄河滩区中下游边界.tif", overlay: "data/overlays/clcd_2000.png", queryGrid: "data/query_grids/clcd_2000.json", converted: true },
        2005: { source: "1.土地利用_CLCD_30m/CLCD_2005_黄河滩区中下游边界.tif", overlay: "data/overlays/clcd_2005.png", queryGrid: "data/query_grids/clcd_2005.json", converted: true },
        2010: { source: "1.土地利用_CLCD_30m/CLCD_2010_黄河滩区中下游边界.tif", overlay: "data/overlays/clcd_2010.png", queryGrid: "data/query_grids/clcd_2010.json", converted: true },
        2015: { source: "1.土地利用_CLCD_30m/CLCD_2015_黄河滩区中下游边界.tif", overlay: "data/overlays/clcd_2015.png", queryGrid: "data/query_grids/clcd_2015.json", converted: true },
        2020: { source: "1.土地利用_CLCD_30m/CLCD_2020_黄河滩区中下游边界.tif", overlay: "data/overlays/clcd_2020.png", queryGrid: "data/query_grids/clcd_2020.json", converted: true },
        2024: { source: "1.土地利用_CLCD_30m/CLCD_2024_黄河滩区中下游裁剪.tif", alignedSource: "data/processed/aligned/clcd_2024_epsg4326_250m.tif", overlay: "data/overlays/clcd_2024.png", queryGrid: "data/query_grids/clcd_2024.json", converted: true, alignment: "reprojected_to_clcd_2020_epsg4326_250m_template_nearest" }
      }
    },
    ntl: {
      key: "ntl",
      label: "Night Light / LongNTL",
      category: "夜间灯光数据",
      type: "raster",
      format: "GeoTIFF",
      sourceFolder: "2.夜间灯光_LongNTL_500m",
      resolution: "约 500 m / 0.004491576421°",
      cesiumLoad: "requires_tiles_or_overlay",
      conversion: "continuous_to_xyz_tiles_or_png_overlay",
      years: {
        2000: { source: "2.夜间灯光_LongNTL_500m/LongNTL_2000_黄河滩区中下游边界.tif", overlay: "data/overlays/ntl_2000.png", queryGrid: "data/query_grids/ntl_2000.json", converted: true },
        2005: { source: "2.夜间灯光_LongNTL_500m/LongNTL_2005_黄河滩区中下游边界.tif", overlay: "data/overlays/ntl_2005.png", queryGrid: "data/query_grids/ntl_2005.json", converted: true },
        2010: { source: "2.夜间灯光_LongNTL_500m/LongNTL_2010_黄河滩区中下游边界.tif", overlay: "data/overlays/ntl_2010.png", queryGrid: "data/query_grids/ntl_2010.json", converted: true },
        2015: { source: "2.夜间灯光_LongNTL_500m/LongNTL_2015_黄河滩区中下游边界.tif", overlay: "data/overlays/ntl_2015.png", queryGrid: "data/query_grids/ntl_2015.json", converted: true },
        2020: { source: "2.夜间灯光_LongNTL_500m/LongNTL_2020_黄河滩区中下游边界.tif", overlay: "data/overlays/ntl_2020.png", queryGrid: "data/query_grids/ntl_2020.json", converted: true },
        2024: { source: "2.夜间灯光_LongNTL_500m/LongNTL_2024_黄河滩区中下游边界.tif", overlay: "data/overlays/ntl_2024.png", queryGrid: "data/query_grids/ntl_2024.json", converted: true }
      }
    },
    gdp: {
      key: "gdp",
      label: "GDP",
      category: "社会经济发展数据",
      type: "raster",
      format: "GeoTIFF",
      sourceFolder: "4.GDP_1km",
      resolution: "约 1 km",
      cesiumLoad: "requires_tiles_or_overlay",
      conversion: "continuous_to_xyz_tiles_or_png_overlay",
      years: {
        2000: { source: "4.GDP_1km/GDP_2000_黄河滩区中下游边界.tif", overlay: "data/overlays/gdp_2000.png", queryGrid: "data/query_grids/gdp_2000.json", converted: true },
        2005: { source: "4.GDP_1km/GDP_2005_黄河滩区中下游边界.tif", overlay: "data/overlays/gdp_2005.png", queryGrid: "data/query_grids/gdp_2005.json", converted: true },
        2010: { source: "4.GDP_1km/GDP_2010_黄河滩区中下游边界.tif", overlay: "data/overlays/gdp_2010.png", queryGrid: "data/query_grids/gdp_2010.json", converted: true },
        2015: { source: "4.GDP_1km/GDP_2015_黄河滩区中下游边界.tif", overlay: "data/overlays/gdp_2015.png", queryGrid: "data/query_grids/gdp_2015.json", converted: true },
        2020: { source: "4.GDP_1km/GDP_2020_黄河滩区中下游边界.tif", overlay: "data/overlays/gdp_2020.png", queryGrid: "data/query_grids/gdp_2020.json", converted: true },
        2024: { source: "4.GDP_1km/GDP_2024_黄河滩区中下游边界.tif", overlay: "data/overlays/gdp_2024.png", queryGrid: "data/query_grids/gdp_2024.json", converted: true }
      }
    },
    landscan: {
      key: "landscan",
      label: "LandScan（人口）",
      category: "社会经济发展数据",
      type: "raster",
      format: "GeoTIFF",
      sourceFolder: "3.人口_LandScan_1km",
      resolution: "约 1 km / 0.00833333333333°",
      cesiumLoad: "requires_tiles_or_overlay",
      conversion: "continuous_to_xyz_tiles_or_png_overlay",
      years: {
        2000: { source: "3.人口_LandScan_1km/LandScan_2000_黄河滩区中下游边界.tif", converted: false },
        2005: { source: "3.人口_LandScan_1km/LandScan_2005_黄河滩区中下游边界.tif", converted: false },
        2010: { source: "3.人口_LandScan_1km/LandScan_2010_黄河滩区中下游边界.tif", converted: false },
        2015: { source: "3.人口_LandScan_1km/LandScan_2015_黄河滩区中下游边界.tif", converted: false },
        2020: { source: "3.人口_LandScan_1km/LandScan_2020_黄河滩区中下游边界.tif", converted: false },
        2024: { source: "3.人口_LandScan_1km/LandScan_2024_黄河滩区中下游边界.tif", converted: false }
      }
    },
    dem: {
      key: "dem",
      label: "DEM",
      category: "数字高程栅格模型",
      type: "raster",
      format: "GeoTIFF",
      sourceFolder: "3.DEM_NASA_30m",
      resolution: "30 m / 0.000277777777778°",
      cesiumLoad: "requires_terrain_or_tiles",
      conversion: "DEM should be converted to terrain tiles or colorized elevation tiles",
      years: { static: { source: "3.DEM_NASA_30m/DEM_黄河滩区中下游边界.tif", converted: false } }
    },
    ndvi: {
      key: "ndvi",
      label: "NDVI",
      category: "植被指数",
      type: "raster",
      format: "GeoTIFF",
      sourceFolder: "5.NDVI_250m",
      resolution: "250 m / 0.0022457882103°",
      cesiumLoad: "requires_tiles_or_overlay",
      conversion: "continuous_to_xyz_tiles_or_png_overlay",
      years: {
        2000: { source: "5.NDVI_250m/MODIS_NDVI_AnnualMean_2000.tif", overlay: "data/overlays/ndvi_2000.png", queryGrid: "data/query_grids/ndvi_2000.json", converted: true },
        2005: { source: "5.NDVI_250m/MODIS_NDVI_AnnualMean_2005.tif", overlay: "data/overlays/ndvi_2005.png", queryGrid: "data/query_grids/ndvi_2005.json", converted: true },
        2010: { source: "5.NDVI_250m/MODIS_NDVI_AnnualMean_2010.tif", overlay: "data/overlays/ndvi_2010.png", queryGrid: "data/query_grids/ndvi_2010.json", converted: true },
        2015: { source: "5.NDVI_250m/MODIS_NDVI_AnnualMean_2015.tif", overlay: "data/overlays/ndvi_2015.png", queryGrid: "data/query_grids/ndvi_2015.json", converted: true },
        2020: { source: "5.NDVI_250m/MODIS_NDVI_AnnualMean_2020.tif", overlay: "data/overlays/ndvi_2020.png", queryGrid: "data/query_grids/ndvi_2020.json", converted: true },
        2024: { source: "5.NDVI_250m/MODIS_NDVI_AnnualMean_2024.tif", overlay: "data/overlays/ndvi_2024.png", queryGrid: "data/query_grids/ndvi_2024.json", converted: true }
      }
    },
    evi: {
      key: "evi",
      label: "EVI",
      category: "植被指数",
      type: "raster",
      format: "GeoTIFF",
      sourceFolder: "6.EVI_250m",
      resolution: "250 m / 0.0022457882103°",
      cesiumLoad: "requires_tiles_or_overlay",
      conversion: "continuous_to_xyz_tiles_or_png_overlay",
      years: {
        2000: { source: "6.EVI_250m/MODIS_EVI_AnnualMean_2000.tif", overlay: "data/overlays/evi_2000.png", queryGrid: "data/query_grids/evi_2000.json", converted: true },
        2005: { source: "6.EVI_250m/MODIS_EVI_AnnualMean_2005.tif", overlay: "data/overlays/evi_2005.png", queryGrid: "data/query_grids/evi_2005.json", converted: true },
        2010: { source: "6.EVI_250m/MODIS_EVI_AnnualMean_2010.tif", overlay: "data/overlays/evi_2010.png", queryGrid: "data/query_grids/evi_2010.json", converted: true },
        2015: { source: "6.EVI_250m/MODIS_EVI_AnnualMean_2015.tif", overlay: "data/overlays/evi_2015.png", queryGrid: "data/query_grids/evi_2015.json", converted: true },
        2020: { source: "6.EVI_250m/MODIS_EVI_AnnualMean_2020.tif", overlay: "data/overlays/evi_2020.png", queryGrid: "data/query_grids/evi_2020.json", converted: true },
        2024: { source: "6.EVI_250m/MODIS_EVI_AnnualMean_2024.tif", overlay: "data/overlays/evi_2024.png", queryGrid: "data/query_grids/evi_2024.json", converted: true }
      }
    },
    water: {
      key: "water",
      label: "Water",
      category: "水体数据",
      type: "raster",
      format: "GeoTIFF",
      sourceFolder: "7.水体_30m",
      resolution: "30 m / 0.000269494585236°",
      cesiumLoad: "requires_tiles_or_overlay",
      conversion: "categorical_nearest_to_xyz_tiles_or_png_overlay",
      years: {
        2000: { source: "7.水体_30m/JRC_waterClass_target_2000_data_2000.tif", overlay: "data/overlays/water_2000.png", queryGrid: "data/query_grids/water_2000.json", converted: true },
        2005: { source: "7.水体_30m/JRC_waterClass_target_2005_data_2005.tif", overlay: "data/overlays/water_2005.png", queryGrid: "data/query_grids/water_2005.json", converted: true },
        2010: { source: "7.水体_30m/JRC_waterClass_target_2010_data_2010.tif", overlay: "data/overlays/water_2010.png", queryGrid: "data/query_grids/water_2010.json", converted: true },
        2015: { source: "7.水体_30m/JRC_waterClass_target_2015_data_2015.tif", overlay: "data/overlays/water_2015.png", queryGrid: "data/query_grids/water_2015.json", converted: true },
        2020: { source: "7.水体_30m/JRC_waterClass_target_2020_data_2020.tif", overlay: "data/overlays/water_2020.png", queryGrid: "data/query_grids/water_2020.json", converted: true },
        2024: { source: "7.水体_30m/JRC_waterClass_target_2024_data_2021.tif", overlay: "data/overlays/water_2024.png", queryGrid: "data/query_grids/water_2024.json", converted: true },
        frequency: { source: "7.水体_30m/JRC_Water_Frequency_2000_2021.tif", converted: false }
      }
    },
    temperature: {
      key: "temperature",
      label: "气温数据",
      category: "气象数据",
      type: "table",
      format: "Excel",
      sourceFolder: "8.气温降水数据（黄河滩区中下游8个站点数据，2000到2019年均）",
      resolution: "8 个气象站点时间序列",
      cesiumLoad: "table_not_imagery",
      conversion: "parse_xlsx_to_json_and_station_points_if_coordinates_available",
      years: { 2000: {}, 2005: {}, 2010: {}, 2015: {}, 2019: {} },
      source: "8.气温降水数据（黄河滩区中下游8个站点数据，2000到2019年均）/黄河滩区8站点_年降水年均气温_2000_2005_2010_2015_2019.xlsx",
      converted: false
    },
    precipitation: {
      key: "precipitation",
      label: "降水数据",
      category: "气象数据",
      type: "table",
      format: "Excel",
      sourceFolder: "8.气温降水数据（黄河滩区中下游8个站点数据，2000到2019年均）",
      resolution: "8 个气象站点时间序列",
      cesiumLoad: "table_not_imagery",
      conversion: "parse_xlsx_to_json_and_station_points_if_coordinates_available",
      years: { 2000: {}, 2005: {}, 2010: {}, 2015: {}, 2019: {} },
      source: "8.气温降水数据（黄河滩区中下游8个站点数据，2000到2019年均）/黄河滩区8站点_年降水年均气温_2000_2005_2010_2015_2019.xlsx",
      converted: false
    },
    terraclimate: {
      key: "terraclimate",
      label: "TerraClimate 水文数据",
      category: "气象数据",
      type: "raster-table",
      format: "GeoTIFF/CSV",
      sourceFolder: "9.TerraClimate水文数据",
      resolution: "约 4.6 km / 0.0416665578233°，11 波段",
      cesiumLoad: "requires_tiles_or_table_parse",
      conversion: "select_band_then_convert_to_tiles_or_parse_stats_csv",
      years: {
        2000: { source: "9.TerraClimate水文数据/TanQu_TerraClimate_Core_2000.tif", converted: false },
        2005: { source: "9.TerraClimate水文数据/TanQu_TerraClimate_Core_2005.tif", converted: false },
        2010: { source: "9.TerraClimate水文数据/TanQu_TerraClimate_Core_2010.tif", converted: false },
        2015: { source: "9.TerraClimate水文数据/TanQu_TerraClimate_Core_2015.tif", converted: false },
        2020: { source: "9.TerraClimate水文数据/TanQu_TerraClimate_Core_2020.tif", converted: false },
        2024: { source: "9.TerraClimate水文数据/TanQu_TerraClimate_Core_2024.tif", converted: false }
      },
      statsCsv: "9.TerraClimate水文数据/TanQu_TerraClimate_Core_Stats_2000_2005_2010_2015_2020_2024.csv"
    }
  }
};
