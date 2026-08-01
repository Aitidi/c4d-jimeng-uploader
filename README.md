# 即梦 Seedance 白模上传器（C4D 2026.3.1）

此插件使用 Cinema 4D 的 **Viewport Renderer** 直接输出 MP4 白模动画，再通过本机临时桥接交给即梦网页导入。它不会生成 PNG 序列，也不会对 C4D 导出的 MP4 进行二次转码。

## 安装

1. 将整个 `jimeng_c4d_uploader` 文件夹（包括其中的 `presets` 子目录）复制到 Cinema 4D 2026 的 `plugins` 目录，或在 C4D Preferences 中添加该目录为插件搜索路径。
2. 重启 Cinema 4D。
3. 从 Extensions 菜单打开“即梦 Seedance 白模上传器”。
4. 首次打开会从插件内置的 `presets/Jimeng Viewport White Model` 导入 `Jimeng Viewport White Model` Render Settings 到当前 `.c4d` 文件。这个 Asset Browser 预设是唯一真源；插件不会创建或使用材质覆盖。

发布前请将 `jimeng_c4d/constants.py` 中的 `PLUGIN_ID` 更换为 Maxon Plugin Café 分配的唯一 ID。

## 使用

1. 选择相机。`Jimeng Viewport White Model` 是固定的唯一 Render Settings；帧范围、帧率和 Save 路径均自动读取该设置。仅在点击渲染时、当前设置不是 Jimeng 预设的情况下，插件会同步当前设置的输出宽高。
2. 点击“渲染设置”会将它设为 C4D 当前设置并打开原生 **Edit Render Settings** 面板。需要修改时直接在此处调整 Output、Save、Viewport Renderer 等选项。
3. 点击“重置渲染设置”会从上述 Asset Browser 预设完整恢复参数，包括 Save 路径和自动文件名；不会添加材质覆盖、效果或其他渲染模块。
4. 点击“渲染并上传”。如果当前 `.c4d` 尚未保存，插件会先提示并打开 C4D 原生保存对话框；取消保存则不会开始渲染。保存后，如果当前 Render Settings 不是 `Jimeng Viewport White Model`，插件会先将当前设置的 Output 宽高同步到 Jimeng 预设，再临时切换到该预设并调用 C4D 原生 **Render to Picture Viewer**（不是 Alt+B 的 Make Preview）。若当前已是 Jimeng 预设，则保持其原有宽高。C4D 完成 MP4 写入后，插件会恢复原 Render Settings 和相机，再上传。
5. 点击“打开即梦链接”。链接依赖本机临时 HTTP 服务：30 分钟后失效，网页开始下载后 60 秒关闭。

即梦网页当前不会自动回填本机桥接返回的提示词，因此插件不再提供误导性的提示词输入框；请在网页端按需要填写。"本地 MP4 上传"只接受已编码为 H.264/yuv420 的 `.mp4` 文件，不转码 MOV、WebM 或 AVI。

新电脑安装时不需要额外导入或注册 Render Settings 预设：只需完整复制插件文件夹，内置的 AssetDB 会随插件一起安装。

## 依赖与限制

- C4D 负责按原生 Render Settings 直接输出 MP4；插件不会覆写 Render Settings，也不调用 ffmpeg 转码。
- 上传前会内置检测 MP4 容器中的 H.264/AVC 视频流；如系统 `ffmpeg`、`JIMENG_UPLOADER_FFMPEG` 或本仓库现有 Blender 插件的内置 `ffmpeg.exe` 可用，还会额外只读核验 `yuv420` 像素格式。两种检查都不会修改视频，也不参与转码。
- Viewport Renderer 仅支持本机渲染，不能经 Team Render 分发。
- 即梦网页协议和 localhost 跨域策略为外部未公开接口，网页改版后可能需要调整桥接逻辑。

## 验证

在普通 Python 环境运行传输层 smoke tests：

```powershell
python -m unittest discover -s jimeng_c4d_uploader/tests -v
```

在 C4D 中验证：修改预设 Render Settings 的帧范围、分辨率和 Save 路径后，插件字段会自动同步；确认 Render to Picture Viewer 直接输出 H.264 MP4，完成后原 Render Settings 会恢复，以及已登录即梦网页的实际导入。
