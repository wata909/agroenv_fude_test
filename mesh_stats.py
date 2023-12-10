import os
import sys
import math
import numpy as np
import pandas as pd
from PIL import Image
from scipy import stats
from collections import Counter

class Meshdata:
    """
    メッシュデータ読み出しクラス
    """

    def __init__(self, meshdata_dir: str, meshcode: str):
        """
        インスタンス化の時にmeshwriterで書き出されたメッシュデータのディレクトリを指定する

        Args:
            meshdata_dir (str): フォルダ名がメッシュコードになっているフォルダ群の親フォルダ
            meshcode (str): 3次メッシュコード
        """
        self.meshdata_dir = meshdata_dir
        self.meshcode = meshcode
        self.read_pickle = pd.read_pickle(os.path.join(
            meshdata_dir, meshcode, "meshdata.pickle"))

        self.hex_json_dir = os.path.join(meshdata_dir, "geology_hex.json")

    def get_bbox(self) -> list:
        bbox = [
            self.read_pickle["minx"],
            self.read_pickle["miny"],
            self.read_pickle["maxx"],
            self.read_pickle["maxy"],
        ]
        return bbox

    def get_precipitation(self) -> list:
        """
        時系列日降水量データを1次元配列で得る
        対象期間: 1978-01-01 ~ 2016-12-31

        Returns:
            list: list of int
        """
        precipitation = self.read_pickle["日降水量"]

        return precipitation

    def get_daylight_hours(self) -> list:
        """
        時系列日照時間データを1次元配列で得る
        対象期間: 1978-01-01 ~ 2016-12-31

        Returns:
            list: list of int
        """
        daylight_hours = self.read_pickle['日照時間']
        return daylight_hours

    def get_solar_radiation(self) -> list:
        """
        時系列日積算日射量データを1次元配列で得る
        対象期間: 1978-01-01 ~ 2016-12-31

        Returns:
            list: list of int
        """
        solar_radiation = self.read_pickle['日積算日射量']
        return solar_radiation

    def get_average_temperature(self) -> list:
        """
        時系列日平均気温データを1次元配列で得る
        対象期間: 1978-01-01 ~ 2016-12-31

        Returns:
            list: list of float
        """
        average_temperature = self.read_pickle['日平均気温']
        return average_temperature

    def get_lowest_temperature(self) -> list:
        """
        時系列日最低気温データを1次元配列で得る
        対象期間: 1978-01-01 ~ 2016-12-31

        Returns:
            list: list of float
        """
        lowest_temperature = self.read_pickle['日最低気温']
        return lowest_temperature

    def get_maximum_temperature(self) -> list:
        """
        時系列日最高気温データを1次元配列で得る
        対象期間: 1978-01-01 ~ 2016-12-31

        Returns:
            list: list of float
        """
        maximum_temperature = self.read_pickle['日最高気温']
        return maximum_temperature

    def get_landuse(self) -> dict:
        """
        土地利用面積データを得る
        Returns:
            dict: {
                "田": int,
                "他農用地": int,
                "森林": int,
                "荒地": int,
                "建物用地": int,
                "道路": int,
                "鉄道": int,
                "他用地": int,
                "河川湖沼": int,
                "海浜": int,
                "海水域": int,
                "ゴルフ場": int,
            }
        """
        landuse = {
            "田": self.read_pickle["田"],
            "他農用地": self.read_pickle["他農用地"],
            "森林": self.read_pickle["森林"],
            "荒地": self.read_pickle["荒地"],
            "建物用地": self.read_pickle["建物用地"],
            "道路": self.read_pickle["道路"],
            "鉄道": self.read_pickle["鉄道"],
            "他用地": self.read_pickle["他用地"],
            "河川湖沼": self.read_pickle["河川湖沼"],
            "海浜": self.read_pickle["海浜"],
            "海水域": self.read_pickle["海水域"],
            "ゴルフ場": self.read_pickle["ゴルフ場"],
        }
        return landuse

    def get_elevation(self) -> list:
        """
        当該メッシュの標高値分布を2次元のlistで得る
        """
        with Image.open(os.path.join(self.meshdata_dir, self.meshcode, "dem.png")) as im:
            elevation_list = self.decode_datapng(im)
        return elevation_list

    def get_slope(self) -> list:
        """
        当該メッシュの傾斜角分布を2次元のlistで得る
        """
        with Image.open(os.path.join(self.meshdata_dir, self.meshcode, "slope.png")) as im:
            slope_list = self.decode_datapng(im)
        return slope_list

    def get_direction(self) -> list:
        """
        当該メッシュの傾斜方向分布を2次元のlistで得る
        """
        with Image.open(os.path.join(self.meshdata_dir, self.meshcode, "direction.png")) as im:
            direction_list = self.decode_datapng(im)
        return direction_list

    def decode_datapng(self, im) -> list:
        """
        産総研データPNGを実数値にデコードする

        Args:
            im (PIL.Image): PNG画像のPIL.Imageインスタンス

        Returns:
            _type_: RGB値を実数値にデコードした2次元のnumpy.array
        """
        rgb_array = np.array(im, np.float64)
        mask_null = (rgb_array[:, :, 0] == 128) * \
                    (rgb_array[:, :, 1] == 0) * (rgb_array[:, :, 2] == 0)
        mask_over = (rgb_array[:, :, 0] >= 128) * \
                    (rgb_array[:, :, 1] >= 0) * (rgb_array[:, :, 2] >= 1)

        value_array = (rgb_array[:, :, 0] * 256 * 256 +
                       rgb_array[:, :, 1] * 256 + rgb_array[:, :, 2]) * 0.01
        value_array[mask_null] = None
        value_array[mask_over] -= 2 ** 24

        return value_array.tolist()

    def hex_to_detial(self) -> dict:
        """hexと対応する地質情報を読み込んで辞書を作成する"""
        return dict(pd.read_json(self.hex_json_dir).values.tolist())

    def read_geologypng_to_hexdf(self) -> pd.DataFrame:
        """
        当該メッシュの地質分布（rgb）をpd.dataframe(hex)で得る
        """

        with Image.open(os.path.join(self.meshdata_dir, self.meshcode, "geology.png")) as im:
            rgb_2d = np.array(im, dtype=np.uint8)

        geology_list = []
        for row in rgb_2d:
            geology_list.append(list(map(self.rgb2hex, row)))

        geology_df = pd.DataFrame(geology_list)

        return geology_df

    def rgb2hex(self, rgb) -> str:
        """
        リスト[R,G,B]のデータ量を減らすためにhex(文字列)に変換
        """
        return '#{:02x}{:02x}{:02x}'.format(rgb[0], rgb[1], rgb[2])

    def get_geology(self) -> list:
        """
        当該メッシュの地質情報分布を2次元のlistで得る
        """
        png_to_hex = self.read_geologypng_to_hexdf()
        geology = png_to_hex.replace(self.hex_to_detial()).values.tolist()

        return geology
    
    def get_monthly_mean(self, data, start_year=1986, end_year=2015) -> list:
        """
        月別の平均値を計算します。
        対象期間: start_year-01-01 ~ end_year-12-31

        Returns:
            list: list of float
        """
        # 月ごとの総量を計算
        monthly_totals = [[] for _ in range(12)]  # 各月の総量を格納するリストを初期化
        
        # 1. 各年度の月ごとの総量を計算する
        for year in range(start_year, end_year + 1):
            for month in range(1, 13):  # 1月から12月まで
                # 各月の日数を取得（2月の閏年を考慮）
                if month == 2 and year % 4 == 0:
                    days_in_month = 29
                elif month == 2:
                    days_in_month = 28
                elif month in [4, 6, 9, 11]:
                    days_in_month = 30
                else:
                    days_in_month = 31
                
                # 月の開始と終了のインデックスを計算
                month_start_index = (year - start_year) * 365 + sum([days_in_month for m in range(1, month)])
                month_end_index = month_start_index + days_in_month
                
                # 月のデータを抽出し、総和を計算
                monthly_total = sum(data[month_start_index:month_end_index])
                monthly_totals[month-1].append(monthly_total)
        
        # 2. 各月の総量の平均値を求める
        monthly_mean = [sum(month_totals) / len(month_totals) for month_totals in monthly_totals]
        
        return monthly_mean
    
    def get_monthly_precipitation_mean(self, start_year=1986, end_year=2015) -> list:
        """
        月別の平均降水量を計算します。
        対象期間: start_year-01-01 ~ end_year-12-31

        Returns:
            list: list of float
        """
        precipitation = self.get_precipitation()
        return self.get_monthly_mean(precipitation, start_year, end_year)
        
    def get_monthly_daylight_hours_mean(self, start_year=1986, end_year=2015) -> list:
        """
        月別の平均日照時間を計算します。
        対象期間: start_year-01-01 ~ end_year-12-31

        Returns:
            list: list of float
        """
        daylight_hours = self.get_daylight_hours()
        return self.get_monthly_mean(daylight_hours, start_year, end_year)
    
    def get_monthly_solar_radiation_mean(self, start_year=1986, end_year=2015) -> list:
        """
        月別の平均日積算日射量を計算します。
        対象期間: start_year-01-01 ~ end_year-12-31

        Returns:
            list: list of float
        """
        solar_radiation = self.get_solar_radiation()
        return self.get_monthly_mean(solar_radiation, start_year, end_year)

    def get_monthly_temperature_mean(self, start_year=1986, end_year=2015) -> list:
        average_temperature = self.get_average_temperature()
        return self.get_monthly_mean_of_mean(average_temperature, start_year, end_year)

    def get_monthly_max_temperature_mean(self, start_year=1986, end_year=2015) -> list:
        max_temperature = self.get_maximum_temperature()
        return self.get_monthly_mean_of_mean(max_temperature, start_year, end_year)

    def get_monthly_min_temperature_mean(self, start_year=1986, end_year=2015) -> list:
        min_temperature = self.get_lowest_temperature()
        return self.get_monthly_mean_of_mean(min_temperature, start_year, end_year)


    def get_monthly_mean_of_mean(self, data, start_year=1986, end_year=2015) -> list:
        """
        月別の平均値の平均を計算します。
        対象期間: start_year-01-01 ~ end_year-12-31

        Returns:
            list: list of float
        """
        # 月ごとの平均値を計算
        monthly_averages = [[] for _ in range(12)]  # 各月の平均値を格納するリストを初期化
        
        # 1. 各年度の月ごとの平均値を計算する
        for year in range(start_year, end_year + 1):
            for month in range(1, 13):  # 1月から12月まで
                # 各月の日数を取得（2月の閏年を考慮）
                if month == 2 and year % 4 == 0:
                    days_in_month = 29
                elif month == 2:
                    days_in_month = 28
                elif month in [4, 6, 9, 11]:
                    days_in_month = 30
                else:
                    days_in_month = 31
                
                # 月の開始と終了のインデックスを計算
                month_start_index = (year - start_year) * 365 + sum([days_in_month for m in range(1, month)])
                month_end_index = month_start_index + days_in_month
                
                # 月のデータを抽出し、平均を計算
                monthly_avg = sum(data[month_start_index:month_end_index]) / days_in_month
                monthly_averages[month-1].append(monthly_avg)
        
        # 2. 各月の平均値の平均を求める
        monthly_mean_of_mean = [sum(month_avgs) / len(month_avgs) for month_avgs in monthly_averages]
        
        return monthly_mean_of_mean


def calculate_mean_bearing(bearings):
    x_sum = 0
    y_sum = 0
    
    for bearing in bearings:
        radian = math.radians(bearing)
        x_sum += math.cos(radian)
        y_sum += math.sin(radian)
    
    mean_radian = math.atan2(y_sum, x_sum)
    mean_bearing = math.degrees(mean_radian)
    
    return mean_bearing % 360

def calculate_statistics(data_2d, is_direction=False):
    data_flat = [item for sublist in data_2d for item in sublist if item is not None]
    
    if is_direction:
        mean = calculate_mean_bearing(data_flat)
        std = None  
        median = None  
        mode = None  
    else:
        data_flat_int = [int(x) for x in data_flat]
        mean = np.mean(data_flat_int)
        std = np.std(data_flat_int)
        median = np.median(data_flat_int)
        
        # modeの計算を修正
        mode_result = stats.mode(data_flat_int, keepdims=False)
        
        # modeとcountを直接参照
        mode = mode_result.mode if mode_result.count > 0 else None
    
    return {
        "mean": mean,
        "std": std,
        "median": median,
        "mode": mode
    }

def save_statistics_to_tsv(data_dict, geology_dict, geology_codes, output_filepath):
    with open(output_filepath, 'w') as f:
        # 地質コードを文字列に変換し、接頭辞 'geol_' を追加
        str_geology_codes = ["geol_" + str(code) for code in geology_codes]
        
        # ヘッダーに月別降水量、月別日照時間、月別積算日射量、月別気温の平均値を追加
        temp_mean_headers = ["temp_mean{:02d}".format(month) for month in range(1, 13)]
        temp_max_headers = ["temp_max{:02d}".format(month) for month in range(1, 13)]
        temp_min_headers = ["temp_min{:02d}".format(month) for month in range(1, 13)]
        prec_mean_headers = ["prec_mean{:02d}".format(month) for month in range(1, 13)]
        daylight_mean_headers = ["daylight_mean{:02d}".format(month) for month in range(1, 13)]
        solar_mean_headers = ["solar_mean{:02d}".format(month) for month in range(1, 13)]
        
        header = "\t".join([
            "mesh_code", *temp_mean_headers, *temp_max_headers, *temp_min_headers, 
            *prec_mean_headers, *daylight_mean_headers, *solar_mean_headers,
            "ele_mean", "ele_std", "ele_med", "ele_mod",
            "slp_mean", "slp_std", "slp_med", "slp_mod", "dir_mean",
            *str_geology_codes
        ])
        f.write(header + "\n")
        
        for meshcode, stats in data_dict.items():
            meshdata = Meshdata(base_dir, meshcode)
            monthly_temperature_mean = meshdata.get_monthly_temperature_mean()
            monthly_max_temperature_mean = meshdata.get_monthly_max_temperature_mean()
            monthly_min_temperature_mean = meshdata.get_monthly_min_temperature_mean()
            monthly_precipitation_mean = meshdata.get_monthly_precipitation_mean()
            monthly_daylight_hours_mean = meshdata.get_monthly_daylight_hours_mean()
            monthly_solar_radiation_mean = meshdata.get_monthly_solar_radiation_mean()

            geology_counts = [str(geology_dict[meshcode].get(code, 0)) for code in geology_codes]
            
            line = "\t".join(map(str, [
                meshcode, *monthly_temperature_mean, *monthly_max_temperature_mean,
                *monthly_min_temperature_mean, *monthly_precipitation_mean,
                *monthly_daylight_hours_mean, *monthly_solar_radiation_mean,  
                stats['elevation']['mean'], stats['elevation']['std'],
                stats['elevation']['median'], stats['elevation']['mode'],
                stats['slope']['mean'], stats['slope']['std'],
                stats['slope']['median'], stats['slope']['mode'],
                stats['direction']['mean'], *geology_counts
            ]))
            f.write(line + "\n")


def main(base_dir, output_base_dir):
    meshcodes = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
    
    all_statistics = {}
    all_geology_counts = {}
    
    # 一つのメッシュコードを使って、全地質コードのリストを取得
    sample_meshdata = Meshdata(base_dir, meshcodes[0])
    geology_codes = list(sample_meshdata.hex_to_detial().values())  # hex値ではなく、数値を取得
    
    for meshcode in meshcodes:
        meshdata = Meshdata(base_dir, meshcode)
        
        elevation = meshdata.get_elevation()
        slope = meshdata.get_slope()
        direction = meshdata.get_direction()
        geology = meshdata.get_geology()
        
        elevation_statistics = calculate_statistics(elevation)
        slope_statistics = calculate_statistics(slope)
        direction_statistics = calculate_statistics(direction, is_direction=True)
        
        # Flatten the 2D geology list and count occurrences of each geology type
        geology_flat = [item for sublist in geology for item in sublist if item is not None]
        geology_counts = Counter(geology_flat)
        
        all_statistics[meshcode] = {
            'elevation': elevation_statistics,
            'slope': slope_statistics,
            'direction': direction_statistics
        }
        all_geology_counts[meshcode] = geology_counts
    
    output_filepath = os.path.join(output_base_dir, "mesh_stats.tsv")
    save_statistics_to_tsv(all_statistics, all_geology_counts, geology_codes, output_filepath)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script_name.py [base_dir] [output_base_dir]")
        sys.exit(1)
    
    base_dir = sys.argv[1]
    output_base_dir = sys.argv[2]
    main(base_dir, output_base_dir)