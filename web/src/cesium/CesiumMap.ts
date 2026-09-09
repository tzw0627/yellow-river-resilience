import * as Cesium from "cesium";
import { regionLabels, stations } from "../config/places";
import type { RegionBoundaryFeature } from "../config";
import type { Bounds } from "../config/types";

const PERF = {
  resolutionScale: Math.min(1.5, window.devicePixelRatio || 1),
  terrainExaggeration: 1.2,
  shortFlyDuration: 1.2,
};

function applyNaturalLightBasemapStyle(baseLayer: Cesium.ImageryLayer | null) {
  if (!baseLayer) return;

  baseLayer.brightness = 1.25;
  baseLayer.contrast = 0.9;
  baseLayer.gamma = 1.1;
  baseLayer.saturation = 0.7;
  baseLayer.hue = 0;
  baseLayer.alpha = 1;
}

type GeoJsonPosition = [number, number] | [number, number, number];
type GeoJsonGeometry =
  | { type: "Polygon"; coordinates: GeoJsonPosition[][] }
  | { type: "MultiPolygon"; coordinates: GeoJsonPosition[][][] }
  | { type: "LineString"; coordinates: GeoJsonPosition[] }
  | { type: "MultiLineString"; coordinates: GeoJsonPosition[][] };
type GeoJsonFeature = { type: "Feature"; geometry: GeoJsonGeometry | null };
type StudyBoundaryData =
  | { type: "FeatureCollection"; features: GeoJsonFeature[] }
  | GeoJsonFeature
  | GeoJsonGeometry;

const STUDY_AREA_BOUNDARY_ID = "study-area-boundary";
const STUDY_AREA_BOUNDARY_GLOW_ID = "study-area-boundary-glow";
const STUDY_AREA_BLACK_BOUNDARY_ID = "study-area-black-boundary";
const CHINA_NATIONAL_BOUNDARY_ID = "china-national-boundary";
const SELECTED_REGION_BOUNDARY_ID = "selected-region-boundary";
const SATELLITE_ORBIT_SOURCE_ID = "cesium-satellite-orbits";
const PRECIPITATION_SOURCE_ID = "observed-precipitation";
const SATELLITE_BILLBOARD_IMAGE = "/assets/satellite.svg";
const SATELLITE_ORBIT_VISIBLE_HEIGHT = 350000;
const SATELLITE_VISIBLE_MIN_CAMERA_HEIGHT = 3000000;
const SATELLITE_ORBIT_HEIGHTS = [900000, 1150000, 1400000];
const SATELLITE_PHASE_OFFSETS = [
  [0, Math.PI],
  [Math.PI / 3, Math.PI / 3 + Math.PI],
  [(Math.PI * 2) / 3, (Math.PI * 2) / 3 + Math.PI],
];

interface SatelliteOrbitSpec {
  id: string;
  inclination: number;
  raan: number;
  height: number;
  periodSeconds: number;
  phase: number;
  reverse?: boolean;
}

interface BoundarySegment {
  coordinates: GeoJsonPosition[];
  close: boolean;
}

function segmentsFromGeometry(geometry: GeoJsonGeometry | null): BoundarySegment[] {
  if (!geometry) return [];
  if (geometry.type === "Polygon") {
    const outer = geometry.coordinates[0];
    return outer ? [{ coordinates: outer, close: true }] : [];
  }
  if (geometry.type === "MultiPolygon") {
    return geometry.coordinates.flatMap((polygon) =>
      polygon[0] ? [{ coordinates: polygon[0], close: true }] : [],
    );
  }
  if (geometry.type === "LineString") return [{ coordinates: geometry.coordinates, close: false }];
  if (geometry.type === "MultiLineString") {
    return geometry.coordinates.map((coordinates) => ({ coordinates, close: false }));
  }
  return [];
}

function extractBoundarySegments(boundaryData: StudyBoundaryData): BoundarySegment[] {
  if (boundaryData.type === "FeatureCollection") {
    return boundaryData.features.flatMap((feature) => segmentsFromGeometry(feature.geometry));
  }
  if (boundaryData.type === "Feature") {
    return segmentsFromGeometry(boundaryData.geometry);
  }
  return segmentsFromGeometry(boundaryData);
}

function removeDataSourcesByName(viewer: Cesium.Viewer, name: string) {
  const existing = viewer.dataSources.getByName(name);
  existing.forEach((dataSource) => viewer.dataSources.remove(dataSource, true));
  const legacyEntity = viewer.entities.getById(name);
  if (legacyEntity) viewer.entities.remove(legacyEntity);
}

function addPolylineBoundaryDataSource(params: {
  viewer: Cesium.Viewer;
  boundaryData: StudyBoundaryData;
  id: string;
  width: number;
  material: Cesium.Color | Cesium.MaterialProperty;
  depthFailMaterial?: Cesium.Color | Cesium.MaterialProperty;
}) {
  removeDataSourcesByName(params.viewer, params.id);

  const segments = extractBoundarySegments(params.boundaryData);
  if (!segments.length) return null;

  const dataSource = new Cesium.CustomDataSource(params.id);
  segments.forEach((segment, index) => {
    const coordinates = segment.close ? closeRing(segment.coordinates) : segment.coordinates;
    const degrees = coordinates.flatMap(([lon, lat]) => [lon, lat]);
    if (degrees.length < 4) return;

    dataSource.entities.add({
      id: index === 0 ? params.id : `${params.id}-${index + 1}`,
      polyline: {
        positions: Cesium.Cartesian3.fromDegreesArray(degrees),
        width: params.width,
        material: params.material,
        depthFailMaterial: params.depthFailMaterial ?? params.material,
        clampToGround: true,
      },
    });
  });

  params.viewer.dataSources.add(dataSource);
  return dataSource;
}

function closeRing(ring: GeoJsonPosition[]): GeoJsonPosition[] {
  if (ring.length < 2) return ring;
  const first = ring[0];
  const last = ring[ring.length - 1];
  if (first[0] === last[0] && first[1] === last[1]) return ring;
  return [...ring, first];
}

function removeStudyAreaBoundary(viewer: Cesium.Viewer) {
  removeDataSourcesByName(viewer, STUDY_AREA_BOUNDARY_GLOW_ID);
  removeDataSourcesByName(viewer, STUDY_AREA_BOUNDARY_ID);
  removeDataSourcesByName(viewer, STUDY_AREA_BLACK_BOUNDARY_ID);
}

function addStudyAreaBoundary(viewer: Cesium.Viewer, boundaryData: StudyBoundaryData) {
  removeStudyAreaBoundary(viewer);
  addPolylineBoundaryDataSource({
    viewer,
    boundaryData,
    id: STUDY_AREA_BOUNDARY_GLOW_ID,
    width: 8,
    material: new Cesium.PolylineGlowMaterialProperty({
      color: Cesium.Color.fromCssColorString("#00eaff").withAlpha(0.32),
      glowPower: 0.16,
    }),
    depthFailMaterial: Cesium.Color.fromCssColorString("#00eaff").withAlpha(0.22),
  });
  addPolylineBoundaryDataSource({
    viewer,
    boundaryData,
    id: STUDY_AREA_BOUNDARY_ID,
    width: 3,
    material: Cesium.Color.BLACK.withAlpha(0.96),
    depthFailMaterial: Cesium.Color.BLACK.withAlpha(0.88),
  });
}

function satelliteCartographic(spec: SatelliteOrbitSpec, angle: number) {
  const inclination = Cesium.Math.toRadians(spec.inclination);
  const raan = Cesium.Math.toRadians(spec.raan);
  const direction = spec.reverse ? -1 : 1;
  const u = spec.phase + direction * angle;
  const lat = Math.asin(Math.sin(inclination) * Math.sin(u));
  const lon = raan + Math.atan2(Math.cos(inclination) * Math.sin(u), Math.cos(u));
  return { lon, lat, height: spec.height };
}

function satelliteCartesian(spec: SatelliteOrbitSpec, angle: number) {
  const point = satelliteCartographic(spec, angle);
  return Cesium.Cartesian3.fromRadians(point.lon, point.lat, point.height);
}

function satelliteOrbitPositions(spec: SatelliteOrbitSpec, samples = 144) {
  const positions: Cesium.Cartesian3[] = [];
  for (let index = 0; index <= samples; index += 1) {
    positions.push(satelliteCartesian(spec, (Math.PI * 2 * index) / samples));
  }
  return positions;
}

type CesiumRuntimeWithOccluder = typeof Cesium & {
  EllipsoidalOccluder?: new (
    ellipsoid: Cesium.Ellipsoid,
    cameraPosition: Cesium.Cartesian3,
  ) => { isPointVisible: (position: Cesium.Cartesian3) => boolean };
};

function isSatelliteVisibleFromCamera(viewer: Cesium.Viewer, satellitePosition: Cesium.Cartesian3) {
  const Occluder = (Cesium as CesiumRuntimeWithOccluder).EllipsoidalOccluder;
  if (Occluder) {
    const occluder = new Occluder(viewer.scene.globe.ellipsoid, viewer.camera.positionWC);
    return occluder.isPointVisible(satellitePosition);
  }

  const satelliteDirection = Cesium.Cartesian3.normalize(satellitePosition, new Cesium.Cartesian3());
  const cameraDirection = Cesium.Cartesian3.normalize(viewer.camera.positionWC, new Cesium.Cartesian3());
  return Cesium.Cartesian3.dot(satelliteDirection, cameraDirection) > 0;
}

async function loadChinaNationalBoundary(viewer: Cesium.Viewer, url: string) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`中国国界数据加载失败：${url}`);
  const boundaryData = (await response.json()) as StudyBoundaryData;
  addPolylineBoundaryDataSource({
    viewer,
    boundaryData,
    id: CHINA_NATIONAL_BOUNDARY_ID,
    width: 2,
    material: Cesium.Color.BLACK.withAlpha(0.9),
  });
  viewer.scene.requestRender();
}

export interface ClickResult {
  lon: number;
  lat: number;
}

export interface PrecipitationMapStation {
  id: string;
  name: string;
  lon: number;
  lat: number;
  value: number;
  percentile: number;
  mode: "daily" | "rolling3";
  fri: number;
  composite: number;
  riskLevel: string;
}

export class CesiumMap {
  viewer: Cesium.Viewer | null = null;
  private basemapLayer: Cesium.ImageryLayer | null = null;
  private thematicLayer: Cesium.ImageryLayer | null = null;
  private boundaryData: StudyBoundaryData | null = null;
  private studyBoundaryVisible = true;
  private chinaBoundaryVisible = true;
  private readonly chinaBoundaryUrl = "/data/boundary/china_boundary.geojson";
  private labelDataSource: Cesium.CustomDataSource | null = null;
  private studyBounds: Bounds | null = null;
  private studyRectangle: Cesium.Rectangle | null = null;
  private overlayCache = new Map<string, Cesium.ImageryProvider>();
  private overlayLoadSeq = 0;
  private tileManifest: Record<string, Record<string, { minLevel?: number; maxLevel?: number; tileSize?: number }>> | null =
    null;
  private boundaryReady = false;
  private annotationsReady = false;
  private satelliteDataSource: Cesium.CustomDataSource | null = null;
  private precipitationDataSource: Cesium.CustomDataSource | null = null;
  private precipitationAnimationFrame: number | null = null;
  private precipitationAnimationStart = 0;
  private precipitationStartValues = new Map<string, number>();
  private precipitationTargetValues = new Map<string, number>();
  private precipitationRiskScores = new Map<string, number>();
  private precipitationFriValues = new Map<string, number>();
  private emergencyPresentationActive = false;
  private satelliteAnimationFrame: number | null = null;
  private satelliteStartTime = 0;
  private readonly satelliteOrbitSpecs: SatelliteOrbitSpec[] = [
    { id: "satellite-1", inclination: 14, raan: 86, height: SATELLITE_ORBIT_HEIGHTS[0], periodSeconds: 22, phase: Math.PI * 0.08 },
    { id: "satellite-2", inclination: 52, raan: 105, height: SATELLITE_ORBIT_HEIGHTS[1], periodSeconds: 28, phase: Math.PI * 0.24, reverse: true },
    { id: "satellite-3", inclination: 64, raan: 48, height: SATELLITE_ORBIT_HEIGHTS[2], periodSeconds: 34, phase: -Math.PI * 0.16 },
  ];

  private rectangleFromBounds(bounds: Bounds): Cesium.Rectangle {
    return Cesium.Rectangle.fromDegrees(bounds.west, bounds.south, bounds.east, bounds.north);
  }

  private requestRender() {
    if (this.viewer && !this.viewer.isDestroyed()) this.viewer.scene.requestRender();
  }

  private centerAndHeight(bounds: Bounds) {
    const rectangle = this.rectangleFromBounds(bounds);
    const center = Cesium.Rectangle.center(rectangle);
    const lon = Cesium.Math.toDegrees(center.longitude);
    const lat = Cesium.Math.toDegrees(center.latitude);
    const spanDeg = Math.max(bounds.north - bounds.south, bounds.east - bounds.west);
    const height = Math.max(28000, spanDeg * 111000 * 1.65);
    return { lon, lat, height, rectangle };
  }

  setViewToStudyArea(bounds = this.studyBounds) {
    if (!this.viewer || !bounds) return;
    const { lon, lat, height } = this.centerAndHeight(bounds);
    this.viewer.camera.setView({
      destination: Cesium.Cartesian3.fromDegrees(lon, lat, height),
      orientation: {
        heading: Cesium.Math.toRadians(10),
        pitch: Cesium.Math.toRadians(-46),
        roll: 0,
      },
    });
    this.requestRender();
  }

  setSelectedRegionBoundary(feature: RegionBoundaryFeature | null) {
    const viewer = this.viewer;
    if (!viewer) return;
    removeDataSourcesByName(viewer, SELECTED_REGION_BOUNDARY_ID);
    if (!feature?.geometry) {
      this.requestRender();
      return;
    }
    addPolylineBoundaryDataSource({
      viewer,
      boundaryData: feature as unknown as StudyBoundaryData,
      id: SELECTED_REGION_BOUNDARY_ID,
      width: 5,
      material: Cesium.Color.fromCssColorString("#d92828"),
    });
    this.requestRender();
  }

  flyChinaToStudyArea(bounds = this.studyBounds, duration = PERF.shortFlyDuration) {
    if (!this.viewer || !bounds) return;
    const { height, rectangle } = this.centerAndHeight(bounds);
    const sphere = Cesium.BoundingSphere.fromRectangle3D(rectangle, this.viewer.scene.globe.ellipsoid, 0);
    this.viewer.camera.setView({
      destination: Cesium.Cartesian3.fromDegrees(105.5, 34.5, 1800000),
      orientation: { heading: 0, pitch: Cesium.Math.toRadians(-55), roll: 0 },
    });
    this.requestRender();
    this.viewer.camera.flyToBoundingSphere(sphere, {
      duration,
      offset: new Cesium.HeadingPitchRange(Cesium.Math.toRadians(10), Cesium.Math.toRadians(-46), height * 0.95),
      complete: () => this.requestRender(),
    });
  }

  setEmergencyPresentationMode(active: boolean, bounds = this.studyBounds) {
    const viewer = this.viewer;
    if (!viewer || !bounds) return;
    this.emergencyPresentationActive = active;
    const controls = viewer.scene.screenSpaceCameraController;

    if (active) {
      this.removeSatelliteOrbits();
      viewer.dataSources.getByName(CHINA_NATIONAL_BOUNDARY_ID).forEach((source) => { source.show = false; });
      controls.enableRotate = false;
      controls.enableTilt = false;
      controls.enableZoom = false;
      controls.enableTranslate = false;
      controls.enableLook = false;
      if (viewer.scene.skyAtmosphere) viewer.scene.skyAtmosphere.show = false;
      if (viewer.scene.skyBox) viewer.scene.skyBox.show = false;
      viewer.scene.backgroundColor = Cesium.Color.fromCssColorString("#06171d");

      const { rectangle, height } = this.centerAndHeight(bounds);
      const sphere = Cesium.BoundingSphere.fromRectangle3D(rectangle, viewer.scene.globe.ellipsoid, 0);
      viewer.camera.flyToBoundingSphere(sphere, {
        duration: 0.7,
        offset: new Cesium.HeadingPitchRange(
          Cesium.Math.toRadians(2),
          Cesium.Math.toRadians(-58),
          height * 0.92,
        ),
        complete: () => this.requestRender(),
      });
    } else {
      controls.enableRotate = true;
      controls.enableTilt = true;
      controls.enableZoom = true;
      controls.enableTranslate = true;
      controls.enableLook = true;
      if (viewer.scene.skyAtmosphere) viewer.scene.skyAtmosphere.show = true;
      if (viewer.scene.skyBox) viewer.scene.skyBox.show = true;
      viewer.dataSources.getByName(CHINA_NATIONAL_BOUNDARY_ID).forEach((source) => { source.show = this.chinaBoundaryVisible; });
      if (!this.satelliteDataSource) this.setupSatelliteOrbits(viewer);
      this.setViewToStudyArea(bounds);
    }
    this.requestRender();
  }

  private applyNaturalLightBasemapStyle() {
    applyNaturalLightBasemapStyle(this.basemapLayer);
    this.viewer?.scene.requestRender();
  }

  private setupBasemap(viewer: Cesium.Viewer) {
    viewer.imageryLayers.removeAll();
    this.basemapLayer = viewer.imageryLayers.addImageryProvider(
      new Cesium.UrlTemplateImageryProvider({
        url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        credit: "Esri",
        maximumLevel: 16,
      }),
    );
    this.applyNaturalLightBasemapStyle();
  }

  private async upgradeTerrain(viewer: Cesium.Viewer) {
    const token = window.APP_CONFIG?.cesiumIonAccessToken?.trim();
    if (!token) return;
    Cesium.Ion.defaultAccessToken = token;
    try {
      const terrain = await Cesium.createWorldTerrainAsync({ requestWaterMask: false, requestVertexNormals: false });
      if (!viewer.isDestroyed()) {
        viewer.terrainProvider = terrain;
        this.requestRender();
      }
    } catch (error) {
      console.warn("后台地形升级失败，继续使用椭球地形。", error);
    }
  }

  private createSatelliteEntity(params: {
    viewer: Cesium.Viewer;
    dataSource: Cesium.CustomDataSource;
    spec: SatelliteOrbitSpec;
    orbitIndex: number;
    satIndex: number;
    phaseOffset: number;
    satelliteImage: string;
  }) {
    const positionProperty = new Cesium.CallbackPositionProperty(() => {
      const elapsedSeconds = (performance.now() - this.satelliteStartTime) / 1000;
      const angle = (elapsedSeconds / params.spec.periodSeconds) * Math.PI * 2 + params.phaseOffset;
      return satelliteCartesian(params.spec, angle);
    }, false);

    params.dataSource.entities.add({
      id: `${params.spec.id}-${params.satIndex + 1}`,
      position: positionProperty,
      billboard: {
        show: new Cesium.CallbackProperty((time) => {
          const cameraHeight = params.viewer.camera.positionCartographic.height;
          if (cameraHeight <= SATELLITE_VISIBLE_MIN_CAMERA_HEIGHT) return false;

          const satellitePosition = positionProperty.getValue(time);
          if (!satellitePosition) return false;

          return isSatelliteVisibleFromCamera(params.viewer, satellitePosition);
        }, false),
        image: params.satelliteImage,
        width: 100,
        height: 100,
        scale: 1,
        verticalOrigin: Cesium.VerticalOrigin.CENTER,
        horizontalOrigin: Cesium.HorizontalOrigin.CENTER,
        scaleByDistance: new Cesium.NearFarScalar(500000, 1.2, 20000000, 0.8),
        heightReference: Cesium.HeightReference.NONE,
      },
      name: `遥感卫星 ${params.orbitIndex + 1}-${params.satIndex + 1}`,
    });
  }

  private setupSatelliteOrbits(viewer: Cesium.Viewer) {
    this.removeSatelliteOrbits();
    const dataSource = new Cesium.CustomDataSource(SATELLITE_ORBIT_SOURCE_ID);
    const satelliteImage = SATELLITE_BILLBOARD_IMAGE;

    this.satelliteStartTime = performance.now();

    this.satelliteOrbitSpecs.forEach((spec, index) => {
      const orbitPositions = satelliteOrbitPositions(spec);
      dataSource.entities.add({
        id: `${spec.id}-orbit`,
        polyline: {
          positions: orbitPositions,
          width: 1.7,
          material: new Cesium.PolylineDashMaterialProperty({
            color: Cesium.Color.fromCssColorString(index === 1 ? "#69ebff" : "#b4f4ff").withAlpha(0.48),
            dashLength: 18,
          }),
          arcType: Cesium.ArcType.NONE,
        },
      });

      const phaseOffsets = SATELLITE_PHASE_OFFSETS[index] ?? [0, Math.PI];
      phaseOffsets.forEach((phaseOffset, satIndex) => {
        this.createSatelliteEntity({
          viewer,
          dataSource,
          spec,
          orbitIndex: index,
          satIndex,
          phaseOffset,
          satelliteImage,
        });
      });
    });

    viewer.dataSources.add(dataSource);
    this.satelliteDataSource = dataSource;
    this.updateSatelliteVisibility();
    this.startSatelliteAnimation();
  }

  private updateSatelliteVisibility() {
    const viewer = this.viewer;
    if (!viewer || !this.satelliteDataSource) return;
    const height = viewer.camera.positionCartographic.height;
    this.satelliteDataSource.show = height > SATELLITE_ORBIT_VISIBLE_HEIGHT;
  }

  private startSatelliteAnimation() {
    if (this.satelliteAnimationFrame !== null) window.cancelAnimationFrame(this.satelliteAnimationFrame);
    const animate = () => {
      const viewer = this.viewer;
      const dataSource = this.satelliteDataSource;
      if (!viewer || viewer.isDestroyed() || !dataSource) {
        this.satelliteAnimationFrame = null;
        return;
      }
      this.updateSatelliteVisibility();
      viewer.scene.requestRender();
      this.satelliteAnimationFrame = window.requestAnimationFrame(animate);
    };
    this.satelliteAnimationFrame = window.requestAnimationFrame(animate);
  }

  private removeSatelliteOrbits() {
    if (this.satelliteAnimationFrame !== null) {
      window.cancelAnimationFrame(this.satelliteAnimationFrame);
      this.satelliteAnimationFrame = null;
    }
    if (this.viewer && this.satelliteDataSource) {
      this.viewer.dataSources.remove(this.satelliteDataSource, true);
    }
    this.satelliteDataSource = null;
  }

  init(container: HTMLElement, bounds: Bounds, onClick: (result: ClickResult) => void) {
    this.studyBounds = bounds;
    this.studyRectangle = this.rectangleFromBounds(bounds);

    const viewer = new Cesium.Viewer(container, {
      animation: false,
      timeline: false,
      baseLayerPicker: false,
      geocoder: false,
      homeButton: false,
      sceneModePicker: false,
      navigationHelpButton: false,
      fullscreenButton: false,
      vrButton: false,
      infoBox: false,
      selectionIndicator: false,
      shouldAnimate: false,
      shadows: false,
      requestRenderMode: true,
      baseLayer: false,
      terrainProvider: new Cesium.EllipsoidTerrainProvider(),
      contextOptions: {
        webgl: { alpha: false, antialias: false, powerPreference: "high-performance" },
      },
    });

    this.viewer = viewer;
    viewer.resolutionScale = PERF.resolutionScale;
    const credit = viewer.cesiumWidget.creditContainer as HTMLElement;
    if (credit) credit.style.display = "none";

    const scene = viewer.scene;
    scene.globe.enableLighting = false;
    scene.globe.depthTestAgainstTerrain = false;
    scene.verticalExaggeration = PERF.terrainExaggeration;
    scene.fog.enabled = false;
    if (scene.skyAtmosphere) scene.skyAtmosphere.show = true;
    if (scene.sun) scene.sun.show = false;
    if (scene.moon) scene.moon.show = false;
    if (scene.skyBox) scene.skyBox.show = false;
    scene.postProcessStages.fxaa.enabled = false;
    scene.screenSpaceCameraController.enableCollisionDetection = false;
    scene.screenSpaceCameraController.minimumZoomDistance = 1200;
    scene.screenSpaceCameraController.maximumZoomDistance = 900000;

    this.setupBasemap(viewer);
    this.setupClick(viewer, onClick);
    this.setViewToStudyArea();
    this.setupSatelliteOrbits(viewer);
    this.applyNaturalLightBasemapStyle();

    setTimeout(() => viewer.resize(), 0);
    void this.upgradeTerrain(viewer);
    this.scheduleDeferredLayers(viewer);
    return viewer;
  }

  private scheduleDeferredLayers(viewer: Cesium.Viewer) {
    const runChinaBoundary = () => void this.ensureChinaBoundary().catch((e) => console.warn("中国国界加载失败", e));
    const runBoundary = () => void this.loadBoundary(viewer).catch((e) => console.warn("边界加载失败", e));
    const runAnnotations = () => {
      if (!this.annotationsReady) {
        this.loadAnnotations(viewer);
        this.annotationsReady = true;
        this.requestRender();
      }
    };
    if ("requestIdleCallback" in window) {
      (window as Window).requestIdleCallback(runChinaBoundary, { timeout: 900 });
      (window as Window).requestIdleCallback(runBoundary, { timeout: 1200 });
      (window as Window).requestIdleCallback(runAnnotations, { timeout: 1800 });
    } else {
      setTimeout(runChinaBoundary, 250);
      setTimeout(runBoundary, 400);
      setTimeout(runAnnotations, 900);
    }
  }

  private ensureStudyAreaBoundaryOnTop() {
    const viewer = this.viewer;
    if (!viewer) return;
    if (!this.studyBoundaryVisible) {
      removeStudyAreaBoundary(viewer);
      this.requestRender();
      return;
    }
    if (!this.boundaryData) return;
    addStudyAreaBoundary(viewer, this.boundaryData);
    this.requestRender();
  }

  setStudyAreaBoundaryVisible(visible: boolean) {
    this.studyBoundaryVisible = visible;
    const viewer = this.viewer;
    if (!viewer) return;
    if (!visible) {
      removeStudyAreaBoundary(viewer);
      this.requestRender();
      return;
    }
    if (this.boundaryReady) {
      this.ensureStudyAreaBoundaryOnTop();
      return;
    }
    void this.loadBoundary(viewer).catch((e) => console.warn("研究区边界加载失败", e));
  }

  private async ensureChinaBoundary() {
    const viewer = this.viewer;
    if (!viewer) return;
    if (!this.chinaBoundaryVisible) {
      removeDataSourcesByName(viewer, CHINA_NATIONAL_BOUNDARY_ID);
      this.requestRender();
      return;
    }
    await loadChinaNationalBoundary(viewer, this.chinaBoundaryUrl);
  }

  setChinaBoundaryVisible(visible: boolean) {
    this.chinaBoundaryVisible = visible;
    void this.ensureChinaBoundary().then(() => {
      if (visible) this.ensureStudyAreaBoundaryOnTop();
    });
  }

  private async loadBoundary(viewer: Cesium.Viewer) {
    if (this.boundaryReady) return;
    const boundaryResponse = await fetch("/data/boundary_display.geojson");
    if (!boundaryResponse.ok) throw new Error("boundary_display.geojson 加载失败");
    const boundaryData = (await boundaryResponse.json()) as StudyBoundaryData;
    this.boundaryData = boundaryData;

    this.boundaryReady = true;
    this.ensureStudyAreaBoundaryOnTop();
    this.requestRender();
  }

  private loadAnnotations(viewer: Cesium.Viewer) {
    if (this.labelDataSource) return;
    const dataSource = new Cesium.CustomDataSource("annotations");
    const regionColor = Cesium.Color.fromCssColorString("#17211b");
    const stationColor = Cesium.Color.fromCssColorString("#b45a37");

    regionLabels.forEach((item) => {
      dataSource.entities.add({
        position: Cesium.Cartesian3.fromDegrees(item.lon, item.lat),
        label: {
          text: item.name,
          font: "bold 14px Microsoft YaHei, sans-serif",
          fillColor: regionColor,
          outlineColor: Cesium.Color.WHITE,
          outlineWidth: 3,
          style: Cesium.LabelStyle.FILL_AND_OUTLINE,
          verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
          disableDepthTestDistance: Number.POSITIVE_INFINITY,
          scaleByDistance: new Cesium.NearFarScalar(20000, 1, 280000, 0.5),
        },
      });
    });

    stations.forEach((item) => {
      dataSource.entities.add({
        position: Cesium.Cartesian3.fromDegrees(item.lon, item.lat),
        point: {
          pixelSize: 8,
          color: Cesium.Color.fromCssColorString("#f8d56b"),
          outlineColor: Cesium.Color.fromCssColorString("#202d2b"),
          outlineWidth: 2,
          disableDepthTestDistance: Number.POSITIVE_INFINITY,
        },
        label: {
          text: item.name,
          font: "12px Microsoft YaHei, sans-serif",
          fillColor: stationColor,
          outlineColor: Cesium.Color.WHITE,
          outlineWidth: 2,
          style: Cesium.LabelStyle.FILL_AND_OUTLINE,
          verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
          pixelOffset: new Cesium.Cartesian2(0, -12),
          disableDepthTestDistance: Number.POSITIVE_INFINITY,
          scaleByDistance: new Cesium.NearFarScalar(12000, 1, 200000, 0.55),
        },
      });
    });

    viewer.dataSources.add(dataSource);
    this.labelDataSource = dataSource;
  }

  private removeThematic(viewer: Cesium.Viewer) {
    if (this.thematicLayer) {
      viewer.imageryLayers.remove(this.thematicLayer, true);
      this.thematicLayer = null;
    }
  }

  private async loadTileManifest() {
    if (this.tileManifest !== null) return this.tileManifest;
    try {
      const response = await fetch("/data/tiles/manifest.json");
      this.tileManifest = response.ok ? await response.json() : {};
    } catch {
      this.tileManifest = {};
    }
    return this.tileManifest;
  }

  private applyStyle(categorical: boolean, layer: Cesium.ImageryLayer) {
    if (categorical) {
      layer.minificationFilter = Cesium.TextureMinificationFilter.NEAREST;
      layer.magnificationFilter = Cesium.TextureMagnificationFilter.NEAREST;
      layer.alpha = 0.94;
    } else {
      layer.minificationFilter = Cesium.TextureMinificationFilter.LINEAR;
      layer.magnificationFilter = Cesium.TextureMagnificationFilter.NEAREST;
      layer.alpha = 0.93;
    }
  }

  private async getOverlayProvider(layer: string, year: number, overlayUrl: string, rectangle: Cesium.Rectangle) {
    const key = `${layer}_${year}_${overlayUrl}_${rectangle.west}_${rectangle.south}_${rectangle.east}_${rectangle.north}`;
    const cached = this.overlayCache.get(key);
    if (cached) return cached;

    const manifest = await this.loadTileManifest();
    const entry = manifest?.[layer]?.[String(year)];
    let provider: Cesium.ImageryProvider;

    if (entry?.maxLevel != null) {
      provider = new Cesium.UrlTemplateImageryProvider({
        url: `/data/tiles/${layer}/${year}/{z}/{x}/{y}.png`,
        rectangle,
        tilingScheme: new Cesium.GeographicTilingScheme(),
        minimumLevel: entry.minLevel,
        maximumLevel: entry.maxLevel,
        tileWidth: entry.tileSize || 256,
        tileHeight: entry.tileSize || 256,
      });
    } else {
      provider = await Cesium.SingleTileImageryProvider.fromUrl(overlayUrl, { rectangle });
    }
    this.overlayCache.set(key, provider);
    return provider;
  }

  async updateThematicLayer(params: {
    layer: string;
    year: number;
    overlayUrl: string | null;
    categorical: boolean;
    rectangle?: Bounds;
  }) {
    const viewer = this.viewer;
    if (!viewer) return;
    const loadSeq = ++this.overlayLoadSeq;
    this.removeThematic(viewer);
    this.applyNaturalLightBasemapStyle();
    await this.ensureChinaBoundary();
    this.ensureStudyAreaBoundaryOnTop();
    this.requestRender();

    if (!params.overlayUrl) return;
    const rectangle = params.rectangle ? this.rectangleFromBounds(params.rectangle) : this.studyRectangle!;
    try {
      const provider = await this.getOverlayProvider(params.layer, params.year, params.overlayUrl, rectangle);
      if (loadSeq !== this.overlayLoadSeq) return;
      this.thematicLayer = viewer.imageryLayers.addImageryProvider(provider);
      this.applyStyle(params.categorical, this.thematicLayer);
      viewer.imageryLayers.raiseToTop(this.thematicLayer);
      this.applyNaturalLightBasemapStyle();
      this.ensureStudyAreaBoundaryOnTop();
      this.requestRender();
    } catch (error) {
      console.warn("专题图层加载失败:", params.layer, params.year, error);
    }
  }

  clearThematicLayer() {
    if (this.viewer) {
      this.removeThematic(this.viewer);
      this.applyNaturalLightBasemapStyle();
      void this.ensureChinaBoundary().then(() => this.ensureStudyAreaBoundaryOnTop());
    }
    this.requestRender();
  }

  setPrecipitationStations(stations: PrecipitationMapStation[]) {
    const viewer = this.viewer;
    if (!viewer) return;
    if (!stations.length) {
      removeDataSourcesByName(viewer, PRECIPITATION_SOURCE_ID);
      this.precipitationDataSource = null;
      this.requestRender();
      return;
    }

    const currentValue = (id: string) => {
      const start = this.precipitationStartValues.get(id) ?? 0;
      const target = this.precipitationTargetValues.get(id) ?? 0;
      const elapsed = performance.now() - this.precipitationAnimationStart;
      const linear = Math.min(1, Math.max(0, elapsed / 520));
      const eased = 1 - Math.pow(1 - linear, 3);
      return start + (target - start) * eased;
    };
    const columnHeight = (value: number) => value <= 0.05 ? 120 : 1800 + value * 980;

    if (!this.precipitationDataSource) {
      removeDataSourcesByName(viewer, PRECIPITATION_SOURCE_ID);
      const dataSource = new Cesium.CustomDataSource(PRECIPITATION_SOURCE_ID);
      stations.forEach((station) => {
        const value = Math.max(0, station.value);
        this.precipitationStartValues.set(station.id, value);
        this.precipitationTargetValues.set(station.id, value);
        this.precipitationRiskScores.set(station.id, station.composite);
        this.precipitationFriValues.set(station.id, station.fri);
        dataSource.entities.add({
          id: `precipitation-${station.id}`,
          name: station.name,
          position: new Cesium.CallbackPositionProperty(() => {
            const height = columnHeight(currentValue(station.id));
            return Cesium.Cartesian3.fromDegrees(station.lon, station.lat, height / 2);
          }, false),
          cylinder: {
            length: new Cesium.CallbackProperty(() => columnHeight(currentValue(station.id)), false),
            topRadius: 4200,
            bottomRadius: 4200,
            material: Cesium.Color.fromCssColorString("#168dff").withAlpha(0.82),
            outline: true,
            outlineColor: Cesium.Color.fromCssColorString("#7fd9ff").withAlpha(0.96),
            numberOfVerticalLines: 12,
          },
          ellipse: {
            semiMajorAxis: 3300,
            semiMinorAxis: 3300,
            material: new Cesium.ColorMaterialProperty(new Cesium.CallbackProperty(() => {
              const score = this.precipitationRiskScores.get(station.id) ?? 0;
              if (score >= 75) return Cesium.Color.fromCssColorString("#ff3b35").withAlpha(0.42);
              if (score >= 55) return Cesium.Color.fromCssColorString("#ff8b36").withAlpha(0.36);
              if (score >= 35) return Cesium.Color.fromCssColorString("#ffd45c").withAlpha(0.3);
              return Cesium.Color.fromCssColorString("#18a8ff").withAlpha(0.18);
            }, false)),
            outline: true,
            outlineColor: new Cesium.CallbackProperty(() => {
              const score = this.precipitationRiskScores.get(station.id) ?? 0;
              return Cesium.Color.fromCssColorString(score >= 75 ? "#ff6a5e" : score >= 55 ? "#ffad59" : "#61ccff").withAlpha(0.9);
            }, false),
            heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
          },
          label: {
            text: new Cesium.CallbackProperty(() => {
              const score = this.precipitationRiskScores.get(station.id) ?? 0;
              return `${station.name}\n${currentValue(station.id).toFixed(1)} mm · 联合${score}`;
            }, false),
            show: new Cesium.CallbackProperty(() => currentValue(station.id) >= 50, false),
            font: "700 13px sans-serif",
            fillColor: Cesium.Color.WHITE,
            showBackground: true,
            backgroundColor: Cesium.Color.fromCssColorString("#063653").withAlpha(0.88),
            backgroundPadding: new Cesium.Cartesian2(7, 5),
            pixelOffset: new Cesium.Cartesian2(0, -12),
            style: Cesium.LabelStyle.FILL_AND_OUTLINE,
            outlineColor: Cesium.Color.fromCssColorString("#00151f"),
            outlineWidth: 2,
            disableDepthTestDistance: Number.POSITIVE_INFINITY,
            distanceDisplayCondition: new Cesium.DistanceDisplayCondition(0, 900000),
          },
          properties: { stationId: station.id },
        });
      });
      viewer.dataSources.add(dataSource);
      this.precipitationDataSource = dataSource;
    } else {
      stations.forEach((station) => {
        this.precipitationStartValues.set(station.id, currentValue(station.id));
        this.precipitationTargetValues.set(station.id, Math.max(0, station.value));
        this.precipitationRiskScores.set(station.id, station.composite);
        this.precipitationFriValues.set(station.id, station.fri);
      });
      this.precipitationAnimationStart = performance.now();
    }

    if (this.precipitationAnimationFrame !== null) window.cancelAnimationFrame(this.precipitationAnimationFrame);
    const animateColumns = () => {
      if (!this.viewer || this.viewer.isDestroyed()) return;
      this.requestRender();
      if (performance.now() - this.precipitationAnimationStart < 560) {
        this.precipitationAnimationFrame = window.requestAnimationFrame(animateColumns);
      } else {
        this.precipitationAnimationFrame = null;
      }
    };
    this.precipitationAnimationFrame = window.requestAnimationFrame(animateColumns);
    this.ensureStudyAreaBoundaryOnTop();
    this.requestRender();
  }

  private setupClick(viewer: Cesium.Viewer, onClick: (result: ClickResult) => void) {
    const handler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);
    handler.setInputAction((movement: Cesium.ScreenSpaceEventHandler.PositionedEvent) => {
      const scene = viewer.scene;
      const ray = viewer.camera.getPickRay(movement.position);
      if (!ray) return;
      const cartesian = scene.globe.pick(ray, scene);
      if (!Cesium.defined(cartesian)) return;
      const cartographic = Cesium.Cartographic.fromCartesian(cartesian);
      onClick({
        lon: Cesium.Math.toDegrees(cartographic.longitude),
        lat: Cesium.Math.toDegrees(cartographic.latitude),
      });
    }, Cesium.ScreenSpaceEventType.LEFT_CLICK);
    viewer.camera.moveEnd.addEventListener(() => {
      this.updateSatelliteVisibility();
      this.requestRender();
    });
  }

  resize() {
    if (this.viewer && !this.viewer.isDestroyed()) {
      this.viewer.resize();
      this.requestRender();
    }
  }

  destroy() {
    this.removeSatelliteOrbits();
    if (this.precipitationAnimationFrame !== null) window.cancelAnimationFrame(this.precipitationAnimationFrame);
    this.precipitationDataSource = null;
    if (this.viewer && !this.viewer.isDestroyed()) this.viewer.destroy();
    this.viewer = null;
  }
}
