# ひらがなデータセットの作成

以下のコードを実行すると、`hiragana\unprocessed_svgs` ディレクトリにひらがなのデータセットが作成されます。
    
    ```
    python deepsvg/hiragana/make_svg.py
    ```
- ひらがなのSVGデータ生成時に以下のデータ拡張を使用しています。  
    - kernel_size=[2,3,4] のカーネルを用いた文字の膨張処理（≒文字の線を太くする）
    - kernel_size=[2,3] のカーネルを用いた文字の収縮処理（≒文字の線を細くする）
    - 画像の縦方向、横方向の収縮・膨張処理（≒文字全体の形状の変形）
        - 各方向について、[0.5, 0.6, 0.7, 0.8, 0.9, 1.1, 1.2, 1.3, 1.4, 1.5] の倍率で処理を行う
- ひらがなフォントには、[IPA Gothic Font](https://moji.or.jp/ipafont/ipaex00401/) を使用しています。

さらに以下のコードを実行して、SVGのパスの簡略化処理を行います。

```
python dataset/preprocess.py --data_folder deepsvg/hiragana/unprocessed_svgs/ --output_folder deepsvg/hiragana/svg_simplefied_large --output_meta_file deepsvg/hiragana/svg_simplefied_large_meta.csv --workers {num_workers}
```
実際の学習時には、この簡略化されたデータが使用されます。