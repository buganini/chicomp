# chicomp

[線上使用（GitHub Pages）](https://buganini.github.io/chicomp/)

漢字部件拆合工具。輸入文字拆成部件，拖曳調整順序，再組合成新的字。
例如把 `功夫不好不要艹我` 拆開再組合，可得到 `巭孬嫑莪`。

## 使用方式

- 輸入文字，按「拆成部件」。
- 點選部件庫加入部件；可依筆畫篩選。
- 拖曳排序，雙擊或按 Enter 複製，拖到刪除區移除。
- 鍵盤選取部件後，可用左右方向鍵移動、Delete／Backspace 刪除。
- 按「組合成字」，查看文字、Unicode 與 CNS 碼位，或複製結果。

所有轉換在瀏覽器的 Web Worker 內執行，輸入文字不會傳送到伺服器。
需要支援 WebAssembly、ES modules、module workers 的現代瀏覽器，以及
HTTPS 或 localhost。沒有 Python API server，也不依賴 jQuery／Vue。

## 架構

`bsdconv` 核心與必要的 codec callback 以 Emscripten 編成 Wasm。
建置啟用 `DISABLE_DYNAMIC_LOADING`，callback 靜態綁定，不使用
`dlopen`／`dlsym`。瀏覽器下載 `.zst` 碼表，由
`compress-utils/zstd/decompress` 解壓後寫入 Emscripten 虛擬檔案系統。

- `src/app.js`：介面及 SortableJS 拖曳操作。
- `src/worker.js`：載入資料、校驗雜湊及執行轉換。
- `wasm/wrapper.c`：供 JavaScript 呼叫的轉換介面。
- `scripts/build.py`：取得來源、編譯碼表與 Wasm、以 Python `zstandard` 壓縮。
- `gen.py`：從官方 PNG 部件圖產生各部件集合的 GIF 及清單。
- `scripts/bundle.mjs`：打包 JS，並以產出的 Wasm 與壓縮資料驗證轉換。

建置器只在 `.build/` 的副本加入 endian 相容處理與靜態 callback 綁定，
不修改 bsdconv 原始 checkout。這些調整針對固定版本；升級時需一起檢查。

## 本機建置

需要 Python 3.10+、Node.js 22、C compiler、Git、ImageMagick，及
`sources.lock.json` 指定版本的 Emscripten（目前為 6.0.13）。先啟用
Emscripten 的 `emsdk_env.sh`，再執行：

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
npm ci
make build
make run
```

`make build` 只建置；`make run`（或直接 `make`）會先建置，再以 Python
啟動 localhost HTTP server。按 Ctrl-C 停止。開啟 <http://localhost:8000>。
請勿直接以 `file://` 開啟 HTML：module worker、Wasm 與資料載入需要 HTTP。
正式網站只需提供 `dist/` 內的靜態檔案。
所有資源使用相對路徑，可部署在 GitHub Pages 的 repository 子路徑。

預設會取得鎖定的 bsdconv／bsdconv-cns11643 提交。也可以使用本機已有的
checkout；它們必須符合鎖定提交，且沒有已追蹤檔案的未提交修改：

```sh
make build BSDCONV_SRC=../bsdconv CNS11643_SRC=../bsdconv-cns11643
```

可用 `PYTHON`、`CC`、`EMCC` 指定工具。`make clean` 刪除 `.build/` 與 `dist/`。

## 資料與建置產物

`sources.lock.json` 固定 bsdconv、CNS 碼表、Emscripten 的版本，以及官方
`Properties.zip` 的版號與 SHA-256；npm 與 Python 依賴也有固定版本。
CNS 碼表直接取自鎖定 repo 的文字檔，本機編譯成 binary，不在 CI 隱式
更新官方碼表。部件圖片與碼表須使用相同資料版本。

官方 ZIP 的下載網址會覆寫。若 SHA-256 不符，建置會停止；請核對新版
資料，再一併更新來源鎖定與碼表提交。`.build/Properties.zip` 可保留已驗證
的下載，不能把 GitHub Actions cache 當成唯一的長期版本保存來源。

原本 repo 根目錄的 `images/` 已改為建置時產生的 `dist/images/`。
`.build/`、`dist/`、`node_modules/`、圖片與 binary 產物都不提交到 Git。
特殊部件「特」依目前官方部件集合編碼產生，沒有硬編碼舊版 `0400`。

## GitHub Pages

在 repo 的 **Settings → Pages → Build and deployment → Source** 選擇
**GitHub Actions**。`.github/workflows/pages.yml` 會：

1. 安裝固定版本工具及依賴，取得鎖定的來源。
2. 產生圖片、binary codecs、Wasm、壓縮資料及前端程式。
3. 驗證 zstd 還原及 UTF-8、CNS 查詢、漢字拆合結果。
4. 上傳 `dist/` 為 Pages artifact；master 分支的 push 或手動執行才會部署。

Pull request 只建置及驗證，不部署。不需要把產物 commit 回 repo，也不需要
`gh-pages` 分支。使用的外部 repo 提交必須已推送，Actions 才能取得。

## 資料來源與授權

部件與字碼資料來源：數位發展部，
[CNS11643 中文標準交換碼全字庫](https://www.cns11643.gov.tw/)。
資料使用依其[開放資料授權說明](https://www.cns11643.gov.tw/pageView.jsp?ID=59)。
網站下方會顯示本次建置的資料版本；完整來源資訊隨 `codecs.json` 發布。

轉換核心：[bsdconv](https://github.com/buganini/bsdconv)（BSD 授權）；
拖曳：[SortableJS](https://github.com/SortableJS/Sortable)（MIT）；
解壓：[compress-utils](https://github.com/dupontcyborg/compress-utils)（MIT）。
建置會將這些授權文件一起放入 `dist/`。
