import os
import tempfile
# import subprocess
import geopandas as gpd
from osgeo import gdal, ogr, osr
from shapely import wkt


# 設定値
GEOJSON_DIR = "fudedata"  # GeoJSONファイルが保存されているディレクトリ
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

def process_feature(mesh_dir, feature, feature_id, high_res_dem, high_res_slope, high_res_direction, high_res_geology):
    """
    各フィーチャーに対する処理
    """
    # 出力フォルダのパスを生成
#    output_feature_dir = os.path.join("meshdata", mesh_dir, "fude_data", str(feature_id))
    output_feature_dir = os.path.join(OUTPUT_DIR, mesh_dir, str(feature_id))
    os.makedirs(output_feature_dir, exist_ok=True)

    # 高解像度のラスターデータを切り抜き
    geometry_wkt = feature.geometry.wkt
    generate_fude_png(high_res_dem, os.path.join(output_feature_dir, "dem.png"), geometry_wkt)
    generate_fude_png(high_res_slope, os.path.join(output_feature_dir, "slope.png"), geometry_wkt)
    generate_fude_png(high_res_direction, os.path.join(output_feature_dir, "direction.png"), geometry_wkt)
    generate_fude_png(high_res_geology, os.path.join(output_feature_dir, "geology.png"), geometry_wkt)

def tar_mesh_data(mesh_dir):
    """
    指定されたメッシュディレクトリの内容をtarで圧縮する
    """
    output_tar_path = os.path.join(OUTPUT_DIR, f"{mesh_dir}.tar.gz")
    with tarfile.open(output_tar_path, "w:gz") as tar:
        tar.add(os.path.join(OUTPUT_DIR, mesh_dir), arcname=mesh_dir)
    # 圧縮後のディレクトリを削除
    os.system(f'rm -rf {os.path.join(OUTPUT_DIR, mesh_dir)}')

def main():
    # ログファイルの初期化
    with open(LOG_FILE, 'w') as log_file:
        log_file.write("Processing Log\n")

    # 各メッシュフォルダに対する処理
    for mesh_dir in os.listdir(INPUT_MESH_DIR):
        mesh_path = os.path.join(INPUT_MESH_DIR, mesh_dir)
        if os.path.isdir(mesh_path):
            # ラスターデータのパスを定義
            dem = os.path.join(INPUT_MESH_DIR, mesh_dir, "dem.png")
            slope = os.path.join(INPUT_MESH_DIR, mesh_dir, "slope.png")
            direction = os.path.join(INPUT_MESH_DIR, mesh_dir, "direction.png")
            geology = os.path.join(INPUT_MESH_DIR, mesh_dir, "geology.png")

            # jsonファイルの読み込み
            geojson_file = os.path.join(GEOJSON_DIR, f"{mesh_dir}.geojson")
            if os.path.exists(geojson_file):
                # GeoJSONファイルの読み込み
                gdf = gpd.read_file(geojson_file)
                # 各地物に対する処理
                for index, feature in gdf.iterrows():
                    process_feature(mesh_dir, feature, feature['polygon_uuid'], dem, slope, direction, geology)
            else:
                # ログに記録
                with open(LOG_FILE, 'a') as log_file:
                    log_file.write(f"GeoJSON file not found for mesh {mesh_dir}\n")
    tar_mesh_data(mesh_dir)

if __name__ == "__main__":
    main()