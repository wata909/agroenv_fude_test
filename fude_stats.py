import os
import tempfile
import subprocess
import geopandas as gpd
from osgeo import gdal, ogr, osr
from shapely import wkt


# 設定値
GEOJSON_DIR = "GeoJSON"  # GeoJSONファイルが保存されているディレクトリ
INPUT_MESH_DIR = "meshdata"  # 入力メッシュデータのディレクトリ
OUTPUT_DIR = "fudedata"  # 出力ディレクトリ
LOG_FILE = "process_log.txt"  # ログファイル

def clip_raster_by_feature(feature, raster_path, output_path):
    """
    地物に基づいてラスターデータを切り出す
    """
    geometry_wkt = feature.geometry.wkt  # .wkt 属性を使用

def generate_fude_png(src: str, dst: str, geometry_wkt: str, resampling="nearest") -> str:
    """
    入力筆ポリゴンの形状で切り抜いたPNG画像を生成する
    gdal.Warpで切り抜きを行う、出力形式は常にPNG

    Args:
        src (str): 入力ラスターのファイルパス（任意形式）
        dst (str): 出力ラスターのファイルパス（PNG）
        geometry_wkt (str): カットラインとして使用するWKT形式のジオメトリ
        resampling (str): 再サンプリング方法

    Returns:
        str: 出力したラスターのファイルパス
    """
    # 一時的なGeoJSONファイルを作成
    tmpfile_name = tempfile.mktemp(suffix='.geojson')
    driver = ogr.GetDriverByName('GeoJSON')
    data_source = driver.CreateDataSource(tmpfile_name)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4301)  # 適切なEPSGコードに設定
    layer = data_source.CreateLayer('', srs, ogr.wkbPolygon)
    feature = ogr.Feature(layer.GetLayerDefn())
    feature.SetGeometry(ogr.CreateGeometryFromWkt(geometry_wkt))
    layer.CreateFeature(feature)
    data_source = None

    # gdal.Warpを使用して切り出し
    warp_options = gdal.WarpOptions(cutlineDSName=tmpfile_name, cropToCutline=True, resampleAlg=resampling)
    gdal.Warp(dst, src, options=warp_options)

    # 一時ファイルを削除
    os.remove(tmpfile_name)

    return dst

def increase_resolution(src: str, dst: str, scale_factor=10, resampling="bilinear") -> str:
    """
    ラスターデータの解像度を高解像度に変更する
    """
    # 元のラスターの解像度を取得
    src_ds = gdal.Open(src)
    transform = src_ds.GetGeoTransform()
    original_res = (transform[1], transform[5])  # (pixel width, pixel height)

    # 新しい解像度を計算
    new_res = (original_res[0] / scale_factor, original_res[1] / scale_factor)

    # gdal.Warpを使用して解像度を変更
    warp_options = gdal.WarpOptions(xRes=new_res[0], yRes=new_res[1], resampleAlg=resampling)
    gdal.Warp(dst, src, options=warp_options)

    return dst

def process_feature(mesh_dir, feature, feature_id, high_res_dem, high_res_slope, high_res_direction, high_res_geology):
    """
    各フィーチャーに対する処理
    """
    # 出力フォルダのパスを生成
    output_feature_dir = os.path.join("meshdata", mesh_dir, "fude_data", str(feature_id))
    os.makedirs(output_feature_dir, exist_ok=True)

    # 高解像度のラスターデータを切り抜き
    geometry_wkt = feature.geometry.wkt
    generate_fude_png(high_res_dem, os.path.join(output_feature_dir, "dem.png"), geometry_wkt)
    generate_fude_png(high_res_slope, os.path.join(output_feature_dir, "slope.png"), geometry_wkt)
    generate_fude_png(high_res_direction, os.path.join(output_feature_dir, "direction.png"), geometry_wkt)
    generate_fude_png(high_res_geology, os.path.join(output_feature_dir, "geology.png"), geometry_wkt)


def main():
    # ログファイルの初期化
    with open(LOG_FILE, 'w') as log_file:
        log_file.write("Processing Log\n")

    # 各メッシュフォルダに対する処理
    for mesh_dir in os.listdir(INPUT_MESH_DIR):
        mesh_path = os.path.join(INPUT_MESH_DIR, mesh_dir)
        if os.path.isdir(mesh_path):
            # 各ラスターデータの解像度を高解像度に変更
            high_res_dem = increase_resolution(os.path.join(INPUT_MESH_DIR, mesh_dir, "dem.png"), 
                                               os.path.join(mesh_path, "high_res_dem.png"))
            high_res_slope = increase_resolution(os.path.join(INPUT_MESH_DIR, mesh_dir, "slope.png"), 
                                                 os.path.join(mesh_path, "high_res_slope.png"))
            high_res_direction = increase_resolution(os.path.join(INPUT_MESH_DIR, mesh_dir, "direction.png"), 
                                                     os.path.join(mesh_path, "high_res_direction.png"))
            high_res_geology = increase_resolution(os.path.join(INPUT_MESH_DIR, mesh_dir, "geology.png"), 
                                                   os.path.join(mesh_path, "high_res_geology.png"))

            geojson_file = os.path.join(GEOJSON_DIR, f"{mesh_dir}.geojson")
            if os.path.exists(geojson_file):
                # GeoJSONファイルの読み込み
                gdf = gpd.read_file(geojson_file)
                # 各地物に対する処理
                for index, feature in gdf.iterrows():
                    process_feature(mesh_dir, feature, feature['polygon_uuid'], high_res_dem, high_res_slope, high_res_direction, high_res_geology)
            else:
                # ログに記録
                with open(LOG_FILE, 'a') as log_file:
                    log_file.write(f"GeoJSON file not found for mesh {mesh_dir}\n")

if __name__ == "__main__":
    main()